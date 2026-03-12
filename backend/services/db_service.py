import sqlite3
import os

class DatabaseService:
    def __init__(self, db_path="backend/complaints.db"):
        # Ensure directory exists if needed, though here it's expected to be in backend/
        self.db_path = db_path
        self._create_tables()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # To get dict-like rows
        return conn

    def _create_tables(self):
        create_complaints_table_query = """
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            text TEXT NOT NULL,
            category TEXT NOT NULL,
            sentiment_label TEXT NOT NULL,
            sentiment_score REAL NOT NULL,
            urgency BOOLEAN NOT NULL,
            priority TEXT NOT NULL,
            department TEXT NOT NULL,
            sla TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        
        create_users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_complaints_table_query)
            cursor.execute(create_users_table_query)
            conn.commit()

    def insert_complaint(self, data: dict):
        insert_query = """
        INSERT INTO complaints (
            complaint_id, customer_name, customer_email, text, category, 
            sentiment_label, sentiment_score, urgency, priority, department, 
            sla, status, created_at
        ) VALUES (
            :complaint_id, :customer_name, :customer_email, :text, :category,
            :sentiment_label, :sentiment_score, :urgency, :priority, :department,
            :sla, :status, :created_at
        )
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(insert_query, data)
            conn.commit()
            return True

    def create_user(self, name: str, email: str, password_hash: str, role: str, created_at: str):
        insert_query = """
        INSERT INTO users (name, email, password_hash, role, created_at)
        VALUES (?, ?, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(insert_query, (name, email, password_hash, role, created_at))
                conn.commit()
                return True, "User registered successfully."
        except sqlite3.IntegrityError:
            return False, "Email already exists."

    def get_user_by_email(self, email: str):
        query = "SELECT * FROM users WHERE email = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

    def get_complaints_by_email(self, email: str):
        query = "SELECT * FROM complaints WHERE customer_email = ? ORDER BY created_at DESC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (email,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_analytics_stats(self):
        stats = {
            "total": 0,
            "categories": {},
            "sentiments": {},
            "priorities": {},
            "departments": {}
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total complaints
            cursor.execute("SELECT COUNT(*) FROM complaints")
            stats["total"] = cursor.fetchone()[0]

            if stats["total"] == 0:
                return stats

            # Categories grouping
            cursor.execute("SELECT category, COUNT(*) FROM complaints GROUP BY category")
            for row in cursor.fetchall():
                stats["categories"][row[0]] = row[1]

            # Sentiments grouping
            cursor.execute("SELECT sentiment_label, COUNT(*) FROM complaints GROUP BY sentiment_label")
            for row in cursor.fetchall():
                stats["sentiments"][row[0]] = row[1]

            # Priorities grouping
            cursor.execute("SELECT priority, COUNT(*) FROM complaints GROUP BY priority")
            for row in cursor.fetchall():
                stats["priorities"][row[0]] = row[1]

            # Departments grouping
            cursor.execute("SELECT department, COUNT(*) FROM complaints GROUP BY department")
            for row in cursor.fetchall():
                stats["departments"][row[0]] = row[1]

        return stats

    def update_complaint_status(self, complaint_id: str, new_status: str):
        update_query = "UPDATE complaints SET status = ? WHERE complaint_id = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(update_query, (new_status, complaint_id))
            conn.commit()

    def get_admin_dashboard_stats(self):
        stats = {
            "total_tickets": 0,
            "active_tickets": 0,
            "resolved_tickets": 0,
            "department_stats": {}
        }
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM complaints WHERE department NOT IN ('Spam', '-')")
            stats["total_tickets"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM complaints WHERE status != 'Resolved' AND department NOT IN ('Spam', '-')")
            stats["active_tickets"] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved' AND department NOT IN ('Spam', '-')")
            stats["resolved_tickets"] = cursor.fetchone()[0]

            cursor.execute("SELECT department, COUNT(*) as total, SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved FROM complaints WHERE department NOT IN ('Spam', '-') GROUP BY department")
            for row in cursor.fetchall():
                stats["department_stats"][row["department"]] = {
                    "total": row["total"],
                    "resolved": row["resolved"] if row["resolved"] else 0,
                    "active": row["total"] - (row["resolved"] if row["resolved"] else 0)
                }
                
        return stats

# Expecting to run from the ai_complaint_system/ directory or ai_complaint_system/backend/
db_service_instance = DatabaseService(db_path="complaints.db")
