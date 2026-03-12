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

    def sync_statuses_from_csv_to_db(self):
        from services.db_service import db_service_instance
        
        # Ensure we are looking in the backend/sheets directory regardless of execution context
        actual_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.base_dir)
        
        if not os.path.exists(actual_dir):
            print(f"Directory {actual_dir} not found for syncing.")
            return
            
        for filename in os.listdir(actual_dir):
            if filename.endswith(".csv"):
                filepath = os.path.join(actual_dir, filename)
                try:
                    with open(filepath, mode='r', encoding='utf-8') as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            complaint_id = row.get("complaint_id")
                            status = row.get("status")
                            if complaint_id and status:
                                db_service_instance.update_complaint_status(complaint_id, status)
                except Exception as e:
                    print(f"Error syncing {filename}: {e}")

    def remove_complaint_from_sheet(self, department: str, complaint_id: str):
        filepath = self._get_filename(department)
        
        # In case we need an absolute path execution resolution like sync method
        actual_filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), filepath)
        if not os.path.exists(actual_filepath):
            return False, "Sheet not found"
            
        try:
            rows_to_keep = []
            with open(actual_filepath, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                headers = next(reader, None)
                if headers:
                    rows_to_keep.append(headers)
                
                for row in reader:
                    # Assuming complaint_id is the first column index 0
                    if row and row[0] != complaint_id:
                        rows_to_keep.append(row)
                        
            with open(actual_filepath, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows_to_keep)
                
            return True, "Removed successfully"
        except Exception as e:
            return False, f"Failed to remove from sheet: {str(e)}"

sheets_service_instance = SheetsService()
