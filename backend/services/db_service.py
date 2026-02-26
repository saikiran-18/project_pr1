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
        create_table_query = """
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
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
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

# Expecting to run from the ai_complaint_system/ directory or ai_complaint_system/backend/
db_service_instance = DatabaseService(db_path="complaints.db")
