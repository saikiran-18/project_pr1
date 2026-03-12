from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os
import hashlib
from typing import Optional

from services.nlp_service import nlp_service_instance
from services.sheets_service import sheets_service_instance
from services.db_service import db_service_instance

app = FastAPI(title="AI Complaint Classification System", version="1.0.0")

# Enable CORS for the local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ComplaintRequest(BaseModel):
    customer_name: str = Field(..., example="John Doe")
    customer_email: str = Field(..., example="john@example.com")
    text: str = Field(..., example="My internet has been down for 3 days! Please fix it immediately.")

class ComplaintResponse(BaseModel):
    complaint_id: str
    message: str
    category: str
    urgency: bool
    priority: str
    department: str
    sla: str
    sentiment_label: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: str # "customer" or "admin"

class UserLogin(BaseModel):
    email: str
    password: str

class AssignTicketRequest(BaseModel):
    complaint_id: str
    target_department: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/api/register")
async def register(user: UserRegister):
    if user.role not in ["customer", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role.")
    
    pwd_hash = hash_password(user.password)
    from datetime import datetime
    created_at = datetime.now().isoformat()
    
    success, msg = db_service_instance.create_user(user.name, user.email, pwd_hash, user.role, created_at)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"message": "User registered successfully", "role": user.role, "email": user.email, "name": user.name}

@app.post("/api/login")
async def login(user: UserLogin):
    db_user = db_service_instance.get_user_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password.")
        
    if db_user['password_hash'] != hash_password(user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password.")
        
    return {
        "message": "Login successful",
        "name": db_user['name'],
        "email": db_user['email'],
        "role": db_user['role']
    }

@app.post("/api/complaints", response_model=ComplaintResponse)
async def submit_complaint(complaint: ComplaintRequest):
    try:
        # 1. Process via NLP service
        processed_data = nlp_service_instance.process_full_complaint(
            text=complaint.text,
            customer_name=complaint.customer_name,
            customer_email=complaint.customer_email
        )
        
        # 2. Append to department-specific Sheet
        success, msg = sheets_service_instance.append_complaint(processed_data)
        if not success:
            raise HTTPException(status_code=500, detail=msg)
            
        # 3. Insert into SQLite Database
        db_service_instance.insert_complaint(processed_data)
            
        return ComplaintResponse(
            complaint_id=processed_data["complaint_id"],
            message="Complaint successfully classified and routed.",
            category=processed_data["category"],
            urgency=processed_data["urgency"],
            priority=processed_data["priority"],
            department=processed_data["department"],
            sla=processed_data["sla"],
            sentiment_label=processed_data["sentiment_label"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/complaints/{email}")
async def get_user_complaints(email: str):
    try:
        # Before serving customer history, ensure DB is perfectly synced with latest CSV changes
        sheets_service_instance.sync_statuses_from_csv_to_db()
        complaints = db_service_instance.get_complaints_by_email(email)
        return {"complaints": complaints}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics")
async def get_analytics():
    """Reads from SQLite to aggregate centralized dashboard statistics."""
    try:
        stats = db_service_instance.get_analytics_stats()
        return stats
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return {
            "total": 0,
            "categories": {},
            "sentiments": {},
            "priorities": {},
            "departments": {}
        }

@app.get("/api/admin/dashboard")
async def get_admin_dashboard():
    try:
        sheets_service_instance.sync_statuses_from_csv_to_db()
        stats = db_service_instance.get_admin_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/pending")
async def get_pending_tickets():
    try:
        query = "SELECT * FROM complaints WHERE department = 'Pending_Admin_Review' ORDER BY created_at DESC"
        with db_service_instance.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return {"tickets": [dict(row) for row in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/assign")
async def assign_pending_ticket(req: AssignTicketRequest):
    try:
        # 1. Update SQLite DB
        update_query = "UPDATE complaints SET department = ?, status = 'Open' WHERE complaint_id = ?"
        with db_service_instance.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(update_query, (req.target_department, req.complaint_id))
            conn.commit()
            
            # Fetch the updated row to write to CSV
            cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (req.complaint_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Ticket not found.")
            full_data = dict(row)
            
        # 2. Remove from Pending Admin sheet
        sheets_service_instance.remove_complaint_from_sheet("Pending_Admin_Review", req.complaint_id)

        # 3. SPAM CATCHER: If Spam, soft-delete it by updating status so customer can still see it
        if req.target_department == "Spam":
            with db_service_instance.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE complaints SET department = '-', status = 'Closed (Invalid Request)' WHERE complaint_id = ?", (req.complaint_id,))
                conn.commit()
            return {"message": "Ticket successfully marked as Spam!"}
            
        # 4. Append to the assigned target CSV
        success, msg = sheets_service_instance.append_complaint(full_data)
        if not success:
            raise HTTPException(status_code=500, detail=f"DB updated but CSV failed: {msg}")
            
        return {"message": "Ticket successfully assigned and routed!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug-score")
async def debug_score(text: str):
    cat, score = nlp_service_instance.classify_complaint(text)
    return {"category": cat, "score": score, "text": text}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
