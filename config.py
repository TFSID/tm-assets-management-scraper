"""
Configuration module for the scraper application.
Contains all settings, constants, and configuration options.
"""

import os
from pathlib import Path

# Browser Configuration
BROWSER_CONFIG = {
    "user_data_dir": r"C:\Users\Akasata\AppData\Local\Google\Chrome\User Data",
    "profile_dir": "Profile 1",
    "chrome_profile_path": "chrome_profile",
    "chrome_profile_name": "Profile 1",
    "wait_timeout": 10,
    "page_load_timeout": 30,
    "implicit_wait": 10
}

# Chrome Options
CHROME_OPTIONS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-background-networking",
    "--disable-notifications",
    "--disable-default-apps",
    "--no-default-browser-check",
    "--disable-popup-blocking",
    "--start-maximized",
    "--disable-web-security",
    "--allow-running-insecure-content",
    "--disable-features=VizDisplayCompositor"
]

# File Paths
PATHS = {
    "session_file": "session_data.json",
    "cookie_path": "cookies.pkl",
    "output_dir": "output",
    "logs_dir": "logs",
    "data_dir": "data"
}

# XPath Templates for different websites
XPATH_TEMPLATES = {
    "bumn": {
        "container": '/html/body/div[1]/section[2]/div/div[1]',
        "item_loop": '/html/body/div[1]/section[2]/div/div[1]/div[{loop}]/div/a'
    },
    "kementrian": {
        "container": '/html/body/section/div/div[2]/div/div/table/tbody',
        "item_loop": '/html/body/section/div/div[2]/div/div/table/tbody/tr[{loop}]/td[4]/a'
    },
    "shopee": {
        "container": '//*[@id="main"]/div/div[2]/div/div/div/div/div/div[2]',
        "item_loop": '//*[@id="main"]/div/div[2]/div/div/div/div/div/div[2]/div[{loop}]/a/div[2]',
        "total_produk": '//*[@id="main"]/div/div[2]/div/div/div/div/div/div[2]/div[{loop}]/div[2]/div[1]/div/div[1]/span',
        "penilaian": '//*[@id="main"]/div/div[2]/div/div/div/div/div/div[2]/div[{loop}]/div[2]/div[2]/div/div[1]/span',
        "persentase_chat_dibalas": '//*[@id="main"]/div/div[2]/div/div/div/div/div/div[2]/div[{loop}]/div[2]/div[3]/div/div[1]/span'
    }
}

# API Configuration
API_CONFIG = {
    "trendmicro": {
        "base_url": "https://portal.sg.xdr.trendmicro.com",
        "dashboard_url": "https://portal.sg.xdr.trendmicro.com/index.html#/app/sase",
        "api_endpoints": {
            "device_list": "/public/ass/api/v1/trilogy/deviceListByCve"
        }
    }
}

# Scraping Configuration
SCRAPING_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,
    "scroll_pause_time": 1,
    "max_pages": 100,
    "items_per_page": 50
}

# Output Configuration
OUTPUT_CONFIG = {
    "csv_encoding": "utf-8",
    "json_indent": 2,
    "date_format": "%Y-%m-%d %H:%M:%S"
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "scraper.log"
}

def ensure_directories():
    """Create necessary directories if they don't exist."""
    for path_name, path_value in PATHS.items():
        if path_name.endswith('_dir'):
            Path(path_value).mkdir(parents=True, exist_ok=True)

def get_profile_path():
    """Get the absolute path to the Chrome profile directory."""
    return os.path.abspath(BROWSER_CONFIG["chrome_profile_path"])

def get_output_path(filename):
    """Get the full path for an output file."""
    return os.path.join(PATHS["output_dir"], filename)

def get_data_path(filename):
    """Get the full path for a data file."""
    return os.path.join(PATHS["data_dir"], filename) 