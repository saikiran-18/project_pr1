import csv
import os

class SheetsService:
    def __init__(self, base_dir="sheets"):
        self.base_dir = base_dir
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

        self.headers = [
            "complaint_id", 
            "created_at",
            "customer_name", 
            "customer_email", 
            "category", 
            "priority", 
            "urgency", 
            "sla", 
            "status", 
            "sentiment_label", 
            "sentiment_score", 
            "text"
        ]

    def _get_filename(self, department: str) -> str:
        # Sanitize department name for filename
        safe_name = "".join([c if c.isalnum() else "_" for c in department])
        return os.path.join(self.base_dir, f"{safe_name}.csv")

    def _ensure_file_exists_with_headers(self, filepath: str):
        if not os.path.exists(filepath):
            with open(filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(self.headers)

    def append_complaint(self, complaint_data: dict):
        department = complaint_data.get("department", "General_Support")
        filepath = self._get_filename(department)
        
        self._ensure_file_exists_with_headers(filepath)

        # Extract data in the order of headers
        row = [complaint_data.get(h, "") for h in self.headers]

        try:
            with open(filepath, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(row)
            return True, f"Successfully added to {department} sheet."
        except Exception as e:
            return False, f"Failed to add to sheet: {str(e)}"

sheets_service_instance = SheetsService()
