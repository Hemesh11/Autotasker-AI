"""
Logger Agent: Handles logging and data storage across multiple backends
"""

import os
import json
import csv
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Google Sheets integration (optional)
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

# AWS S3 integration (optional)
try:
    import boto3
    from botocore.exceptions import ClientError
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False

from backend.utils import ensure_directory_exists, save_json_file


class LoggerAgent:
    """Agent for logging execution data to various backends"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.LoggerAgent")
        
        # Storage backends
        self.use_sheets = SHEETS_AVAILABLE and config.get("logging", {}).get("use_sheets", False)
        self.use_s3 = S3_AVAILABLE and config.get("logging", {}).get("use_s3", False)
        self.use_local = config.get("logging", {}).get("use_local", True)
        
        # Local storage paths
        self.logs_dir = "data/logs"
        self.execution_log_file = os.path.join(self.logs_dir, "execution_log.csv")
        self.detailed_logs_dir = os.path.join(self.logs_dir, "detailed")
        
        # Initialize storage backends
        self._initialize_local_storage()
        
        if self.use_sheets:
            self._initialize_sheets()
        
        if self.use_s3:
            self._initialize_s3()
    
    def _initialize_local_storage(self) -> None:
        """Initialize local file storage"""
        ensure_directory_exists(self.logs_dir)
        ensure_directory_exists(self.detailed_logs_dir)
        
        # Create CSV header if file doesn't exist
        if not os.path.exists(self.execution_log_file):
            self._create_csv_header()
    
    def _initialize_sheets(self) -> None:
        """Initialize Google Sheets integration"""
        try:
            # This would need proper OAuth setup
            # For now, we'll just mark as available
            self.sheets_service = None
            self.logger.info("Google Sheets integration initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Google Sheets: {e}")
            self.use_sheets = False
    
    def _initialize_s3(self) -> None:
        """Initialize AWS S3 integration"""
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.config.get("aws", {}).get("region", "us-east-1")
            )
            self.s3_bucket = self.config.get("aws", {}).get("s3_bucket", "autotasker-logs")
            self.logger.info("AWS S3 integration initialized")
        except Exception as e:
            self.logger.warning(f"Failed to initialize AWS S3: {e}")
            self.use_s3 = False
    
    def log_execution(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log execution data to configured backends
        
        Args:
            log_entry: Execution data to log
            
        Returns:
            Logging results
        """
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "logged_to": [],
            "errors": []
        }
        
        # Add unique ID if not present
        if "execution_id" not in log_entry:
            log_entry["execution_id"] = self._generate_execution_id()
        
        # Log to local storage
        if self.use_local:
            try:
                self._log_to_local(log_entry)
                results["logged_to"].append("local")
            except Exception as e:
                self.logger.error(f"Local logging failed: {e}")
                results["errors"].append(f"Local: {str(e)}")
        
        # Log to Google Sheets
        if self.use_sheets:
            try:
                self._log_to_sheets(log_entry)
                results["logged_to"].append("sheets")
            except Exception as e:
                self.logger.error(f"Sheets logging failed: {e}")
                results["errors"].append(f"Sheets: {str(e)}")
        
        # Log to S3
        if self.use_s3:
            try:
                self._log_to_s3(log_entry)
                results["logged_to"].append("s3")
            except Exception as e:
                self.logger.error(f"S3 logging failed: {e}")
                results["errors"].append(f"S3: {str(e)}")
        
        success = len(results["logged_to"]) > 0
        
        if success:
            self.logger.info(f"Execution logged to: {', '.join(results['logged_to'])}")
        else:
            self.logger.error("Failed to log to any backend")
        
        return {
            "success": success,
            "results": results,
            "execution_id": log_entry["execution_id"]
        }
    
    def _log_to_local(self, log_entry: Dict[str, Any]) -> None:
        """Log to local CSV and JSON files"""
        
        # Log summary to CSV
        csv_row = {
            "execution_id": log_entry["execution_id"],
            "timestamp": log_entry["timestamp"],
            "prompt": log_entry["prompt"][:100],  # Truncate for CSV
            "task_count": len(log_entry.get("task_plan", {}).get("tasks", [])),
            "success": len(log_entry.get("errors", [])) == 0,
            "retry_count": log_entry.get("retry_count", 0),
            "duration": log_entry.get("duration", "unknown")
        }
        
        # Append to CSV
        file_exists = os.path.exists(self.execution_log_file)
        with open(self.execution_log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=csv_row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(csv_row)
        
        # Save detailed JSON
        json_filename = f"execution_{log_entry['execution_id']}.json"
        json_filepath = os.path.join(self.detailed_logs_dir, json_filename)
        save_json_file(log_entry, json_filepath)
    
    def _log_to_sheets(self, log_entry: Dict[str, Any]) -> None:
        """Log to Google Sheets"""
        
        if not self.sheets_service:
            raise Exception("Google Sheets service not initialized")
        
        # This would implement the actual Sheets API calls
        # For now, we'll simulate success
        self.logger.info("Would log to Google Sheets (implementation needed)")
    
    def _log_to_s3(self, log_entry: Dict[str, Any]) -> None:
        """Log to AWS S3"""
        
        # Generate S3 key
        date_prefix = datetime.now().strftime("%Y/%m/%d")
        s3_key = f"autotasker-logs/{date_prefix}/execution_{log_entry['execution_id']}.json"
        
        # Upload to S3
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=s3_key,
            Body=json.dumps(log_entry, default=str),
            ContentType='application/json'
        )
    
    def _create_csv_header(self) -> None:
        """Create CSV header row"""
        
        headers = [
            "execution_id",
            "timestamp", 
            "prompt",
            "task_count",
            "success",
            "retry_count",
            "duration"
        ]
        
        with open(self.execution_log_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def _generate_execution_id(self) -> str:
        """Generate unique execution ID"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random
        random_suffix = random.randint(1000, 9999)
        
        return f"exec_{timestamp}_{random_suffix}"
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get execution history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of execution records
        """
        
        history = []
        
        try:
            if os.path.exists(self.execution_log_file):
                with open(self.execution_log_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    history = list(reader)
                
                # Sort by timestamp (most recent first)
                history.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Limit results
                history = history[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get execution history: {e}")
        
        return history
    
    def get_detailed_log(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed log for specific execution
        
        Args:
            execution_id: Execution ID to retrieve
            
        Returns:
            Detailed execution data or None
        """
        
        json_filename = f"execution_{execution_id}.json"
        json_filepath = os.path.join(self.detailed_logs_dir, json_filename)
        
        try:
            with open(json_filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"Detailed log not found for execution {execution_id}")
            return None
        except Exception as e:
            self.logger.error(f"Failed to read detailed log: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get execution statistics
        
        Returns:
            Statistics summary
        """
        
        history = self.get_execution_history(1000)  # Get more records for stats
        
        if not history:
            return {
                "total_executions": 0,
                "success_rate": 0,
                "average_tasks": 0,
                "most_recent": None
            }
        
        total = len(history)
        successful = len([h for h in history if h.get('success') == 'True'])
        
        # Calculate average task count
        task_counts = [int(h.get('task_count', 0)) for h in history if h.get('task_count', '').isdigit()]
        avg_tasks = sum(task_counts) / len(task_counts) if task_counts else 0
        
        return {
            "total_executions": total,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "successful_executions": successful,
            "failed_executions": total - successful,
            "average_tasks": round(avg_tasks, 1),
            "most_recent": history[0] if history else None,
            "date_range": {
                "oldest": history[-1].get('timestamp') if history else None,
                "newest": history[0].get('timestamp') if history else None
            }
        }
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old log files
        
        Args:
            days_to_keep: Number of days to keep logs
            
        Returns:
            Cleanup results
        """
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_files = []
        errors = []
        
        try:
            # Clean detailed JSON logs
            if os.path.exists(self.detailed_logs_dir):
                for filename in os.listdir(self.detailed_logs_dir):
                    filepath = os.path.join(self.detailed_logs_dir, filename)
                    
                    try:
                        file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                        if file_time < cutoff_date:
                            os.remove(filepath)
                            cleaned_files.append(filename)
                    except Exception as e:
                        errors.append(f"Failed to remove {filename}: {e}")
        
        except Exception as e:
            errors.append(f"Failed to access logs directory: {e}")
        
        self.logger.info(f"Cleaned up {len(cleaned_files)} old log files")
        
        return {
            "cleaned_files": len(cleaned_files),
            "errors": errors,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    def export_logs(self, format_type: str = "json", 
                   start_date: str = None, end_date: str = None) -> str:
        """
        Export logs in specified format
        
        Args:
            format_type: Export format (json, csv)
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            
        Returns:
            Export file path
        """
        
        history = self.get_execution_history(10000)  # Get large number for export
        
        # Filter by date if specified
        if start_date or end_date:
            filtered_history = []
            for record in history:
                record_date = datetime.fromisoformat(record['timestamp'])
                
                if start_date and record_date < datetime.fromisoformat(start_date):
                    continue
                if end_date and record_date > datetime.fromisoformat(end_date):
                    continue
                
                filtered_history.append(record)
            
            history = filtered_history
        
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_filename = f"autotasker_export_{timestamp}.{format_type}"
        export_path = os.path.join(self.logs_dir, export_filename)
        
        # Export data
        if format_type == "json":
            save_json_file(history, export_path)
        elif format_type == "csv":
            if history:
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=history[0].keys())
                    writer.writeheader()
                    writer.writerows(history)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        self.logger.info(f"Exported {len(history)} records to {export_path}")
        
        return export_path
