"""
Utility functions for the scraper application.
Contains helper functions for data processing, logging, and common operations.
"""

import csv
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from config import LOGGING_CONFIG, OUTPUT_CONFIG, get_output_path


def setup_logging(log_file: str = None, level: str = None):
    """
    Setup logging configuration.
    
    Args:
        log_file (str): Path to log file
        level (str): Logging level
    """
    log_file = log_file or LOGGING_CONFIG["file"]
    level = level or LOGGING_CONFIG["level"]
    
    # Create logs directory if it doesn't exist
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=LOGGING_CONFIG["format"],
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def get_timestamp() -> str:
    """Get current timestamp in configured format."""
    return datetime.now().strftime(OUTPUT_CONFIG["date_format"])


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename (str): Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = 'untitled'
    
    return filename


def extract_links_from_text(text: str) -> List[str]:
    """
    Extract URLs from text using regex.
    
    Args:
        text (str): Text to extract URLs from
        
    Returns:
        List[str]: List of found URLs
    """
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, text)


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and special characters.
    
    Args:
        text (str): Text to clean
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\-.,!?()]', '', text)
    
    return text


def merge_data_sets(data_sets: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Merge multiple data sets into one.
    
    Args:
        data_sets (List[List[Dict[str, Any]]]): List of data sets to merge
        
    Returns:
        List[Dict[str, Any]]: Merged data set
    """
    merged_data = []
    for data_set in data_sets:
        merged_data.extend(data_set)
    return merged_data


def deduplicate_data(data: List[Dict[str, Any]], key_field: str = None) -> List[Dict[str, Any]]:
    """
    Remove duplicate entries from data.
    
    Args:
        data (List[Dict[str, Any]]): Data to deduplicate
        key_field (str): Field to use for deduplication
        
    Returns:
        List[Dict[str, Any]]: Deduplicated data
    """
    if not data:
        return []
    
    seen = set()
    deduplicated = []
    
    for item in data:
        if key_field:
            # Use specific field for deduplication
            key = item.get(key_field, '')
        else:
            # Use entire item as key
            key = json.dumps(item, sort_keys=True)
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
    
    return deduplicated


def filter_data(data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter data based on criteria.
    
    Args:
        data (List[Dict[str, Any]]): Data to filter
        filters (Dict[str, Any]): Filter criteria
        
    Returns:
        List[Dict[str, Any]]: Filtered data
    """
    if not filters:
        return data
    
    filtered_data = []
    
    for item in data:
        matches = True
        for field, value in filters.items():
            if field not in item or item[field] != value:
                matches = False
                break
        
        if matches:
            filtered_data.append(item)
    
    return filtered_data


def sort_data(data: List[Dict[str, Any]], sort_field: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """
    Sort data by a specific field.
    
    Args:
        data (List[Dict[str, Any]]): Data to sort
        sort_field (str): Field to sort by
        reverse (bool): Sort in reverse order
        
    Returns:
        List[Dict[str, Any]]: Sorted data
    """
    if not data or sort_field not in data[0]:
        return data
    
    return sorted(data, key=lambda x: x.get(sort_field, ''), reverse=reverse)


def export_to_multiple_formats(data: List[Dict[str, Any]], base_filename: str, 
                             formats: List[str] = None):
    """
    Export data to multiple formats.
    
    Args:
        data (List[Dict[str, Any]]): Data to export
        base_filename (str): Base filename without extension
        formats (List[str]): List of formats to export to
    """
    if not formats:
        formats = ['json', 'csv']
    
    base_filename = sanitize_filename(base_filename)
    
    for format_type in formats:
        try:
            if format_type.lower() == 'json':
                filename = f"{base_filename}.json"
                export_to_json(data, filename)
            elif format_type.lower() == 'csv':
                filename = f"{base_filename}.csv"
                export_to_csv(data, filename)
            elif format_type.lower() == 'txt':
                filename = f"{base_filename}.txt"
                export_to_txt(data, filename)
        except Exception as e:
            print(f"[ERROR] Failed to export to {format_type}: {e}")


def export_to_json(data: List[Dict[str, Any]], filename: str):
    """
    Export data to JSON file.
    
    Args:
        data (List[Dict[str, Any]]): Data to export
        filename (str): Output filename
    """
    output_path = get_output_path(filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=OUTPUT_CONFIG["json_indent"], ensure_ascii=False)
    print(f"[INFO] Data exported to {output_path}")


def export_to_csv(data: List[Dict[str, Any]], filename: str):
    """
    Export data to CSV file.
    
    Args:
        data (List[Dict[str, Any]]): Data to export
        filename (str): Output filename
    """
    if not data:
        print("[WARNING] No data to export")
        return
    
    output_path = get_output_path(filename)
    fieldnames = data[0].keys()
    
    with open(output_path, 'w', newline='', encoding=OUTPUT_CONFIG["csv_encoding"]) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"[INFO] Data exported to {output_path}")


def export_to_txt(data: List[Dict[str, Any]], filename: str):
    """
    Export data to text file.
    
    Args:
        data (List[Dict[str, Any]]): Data to export
        filename (str): Output filename
    """
    output_path = get_output_path(filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            for key, value in item.items():
                f.write(f"{key}: {value}\n")
            f.write("-" * 50 + "\n")
    
    print(f"[INFO] Data exported to {output_path}")


def retry_operation(operation, max_retries: int = 3, delay: float = 1.0, 
                   backoff_factor: float = 2.0):
    """
    Retry an operation with exponential backoff.
    
    Args:
        operation: Function to retry
        max_retries (int): Maximum number of retries
        delay (float): Initial delay between retries
        backoff_factor (float): Factor to multiply delay by after each retry
        
    Returns:
        Any: Result of the operation
        
    Raises:
        Exception: Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return operation()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                print(f"[WARNING] Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                print(f"[INFO] Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] Operation failed after {max_retries + 1} attempts: {e}")
    
    raise last_exception


def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL is valid
    """
    url_pattern = r'^https?://[^\s<>"{}|\\^`\[\]]+$'
    return bool(re.match(url_pattern, url))


def extract_domain(url: str) -> str:
    """
    Extract domain from URL.
    
    Args:
        url (str): URL to extract domain from
        
    Returns:
        str: Domain name
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc
    except:
        return ""


def create_summary_report(data: List[Dict[str, Any]], output_file: str = None) -> Dict[str, Any]:
    """
    Create a summary report of scraped data.
    
    Args:
        data (List[Dict[str, Any]]): Scraped data
        output_file (str): Optional output file for the report
        
    Returns:
        Dict[str, Any]: Summary report
    """
    if not data:
        return {"error": "No data to summarize"}
    
    # Basic statistics
    total_items = len(data)
    
    # Field statistics
    field_stats = {}
    for item in data:
        for field, value in item.items():
            if field not in field_stats:
                field_stats[field] = {"count": 0, "values": set()}
            field_stats[field]["count"] += 1
            if value:
                field_stats[field]["values"].add(str(value))
    
    # Convert sets to lists for JSON serialization
    for field in field_stats:
        field_stats[field]["values"] = list(field_stats[field]["values"])
        field_stats[field]["unique_count"] = len(field_stats[field]["values"])
    
    report = {
        "timestamp": get_timestamp(),
        "total_items": total_items,
        "field_statistics": field_stats,
        "sample_data": data[:5] if data else []
    }
    
    if output_file:
        try:
            output_path = get_output_path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=OUTPUT_CONFIG["json_indent"], ensure_ascii=False)
            print(f"[INFO] Summary report saved to {output_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save summary report: {e}")
    
    return report


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def get_file_info(file_path: str) -> Dict[str, Any]:
    """
    Get information about a file.
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        Dict[str, Any]: File information
    """
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True
        }
    except FileNotFoundError:
        return {"exists": False}
    except Exception as e:
        return {"exists": False, "error": str(e)} 