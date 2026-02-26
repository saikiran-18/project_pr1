from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import os

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
