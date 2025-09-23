#!/usr/bin/env python3
"""
TrendMicro XDR CVE Device Scraper
=================================

A comprehensive tool for scraping CVE vulnerability data from TrendMicro XDR portal.
This script can handle single CVE queries or batch processing from files, with priority
classification and CSV output generation.

Author: Security Team
Version: 2.0
"""

import argparse
import csv
import json
import os
import pickle
import re
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class TrendMicroXDRScraper:
    """Main scraper class for TrendMicro XDR CVE data extraction."""
    
    # Configuration constants
    SESSION_FILE = "session_data.json"
    COOKIE_PATH = "cookies.pkl"
    PRIORITY_ENDPOINTS_FILE = "PRIORITY_ENDPOINTS.txt"
    PRIORITY_SERVERS_CSV = "PRIORITY_PATCH_SERVERS.csv"
    ENDPOINT_PRIORITY_CSV = "endpoint_patch_priority.csv"
    
    # URLs
    BASE_URL = "https://portal.sg.xdr.trendmicro.com"
    DASHBOARD_URL = f"{BASE_URL}/index.html#/app/sase"
    TOKEN_URL = f"{BASE_URL}/ui/uic/v3/session"
    API_BASE = f"{BASE_URL}/public/ass/api/v1/trilogy/deviceListByCve"
    
    # Chrome profile settings
    PROFILE_DIR = "chrome_profile"
    PROFILE_NAME = "Profile 1"
    
    def __init__(self, headless: bool = False, timeout: int = 30):
        """
        Initialize the scraper.
        
        Args:
            headless: Run Chrome in headless mode
            timeout: Default timeout for requests
        """
        self.headless = headless
        self.timeout = timeout
        self.profile_path = os.path.abspath(self.PROFILE_DIR)
        self.session = requests.Session()
        self.token = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup basic logging."""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def create_driver(self) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver.
        
        Returns:
            Configured Chrome WebDriver instance
        """
        options = Options()
        options.add_argument(f"--user-data-dir={self.profile_path}")
        options.add_argument(f"--profile-directory={self.PROFILE_NAME}")
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-default-apps")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        if self.headless:
            options.add_argument("--headless")
            
        self.logger.info(f"Starting Chrome with profile at: {self.profile_path}")
        
        try:
            driver = webdriver.Chrome(service=Service(), options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except Exception as e:
            self.logger.error(f"Failed to create Chrome driver: {e}")
            raise
    
    def extract_cookies_and_headers(self, driver: webdriver.Chrome, base_url: str) -> Tuple[Dict, Dict]:
        """
        Extract cookies and headers from browser session.
        
        Args:
            driver: Chrome WebDriver instance
            base_url: Base URL for referer header
            
        Returns:
            Tuple of (cookies dict, headers dict)
        """
        cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
        headers = {
            "User-Agent": driver.execute_script("return navigator.userAgent"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": base_url,
            "Connection": "keep-alive",
            "Content-Type": "application/json"
        }
        
        # Try to extract token from localStorage
        try:
            token = driver.execute_script("return localStorage.getItem('access_token')")
            if token:
                headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            self.logger.warning(f"Could not extract token from localStorage: {e}")
            
        return cookies, headers
    
    def save_session(self, cookies: Dict, headers: Dict, filename: str = None) -> None:
        """
        Save session data to file.
        
        Args:
            cookies: Cookies dictionary
            headers: Headers dictionary
            filename: Optional custom filename
        """
        filename = filename or self.SESSION_FILE
        session_data = {
            "cookies": cookies,
            "headers": headers,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Session saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            raise
    
    def load_session(self, filename: str = None) -> Tuple[Dict, Dict]:
        """
        Load session data from file.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Tuple of (cookies dict, headers dict)
        """
        filename = filename or self.SESSION_FILE
        
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Session file '{filename}' not found.")
        
        try:
            with open(filename, "r", encoding='utf-8') as f:
                session_data = json.load(f)
            
            self.logger.info(f"Loaded session from {filename}")
            return session_data["cookies"], session_data["headers"]
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            raise
    
    def save_cookies(self, driver: webdriver.Chrome, filename: str = None) -> None:
        """
        Save cookies to pickle file.
        
        Args:
            driver: Chrome WebDriver instance
            filename: Optional custom filename
        """
        filename = filename or self.COOKIE_PATH
        cookies = driver.get_cookies()
        
        try:
            with open(filename, 'wb') as f:
                pickle.dump(cookies, f)
            self.logger.info(f"Cookies saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save cookies: {e}")
            raise
    
    def load_cookies(self, filename: str = None) -> List[Dict]:
        """
        Load cookies from pickle file.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            List of cookie dictionaries
        """
        filename = filename or self.COOKIE_PATH
        
        if not os.path.exists(filename):
            self.logger.warning(f"Cookie file '{filename}' not found. Attempting to create it...")
            if self._auto_setup_cookies():
                # Try loading again after setup
                return self.load_cookies(filename)
            else:
                raise FileNotFoundError(f"Cookie file '{filename}' not found and auto-setup failed.")
        
        try:
            with open(filename, 'rb') as f:
                cookies = pickle.load(f)
            self.logger.info(f"Loaded cookies from {filename}")
            return cookies
        except Exception as e:
            self.logger.error(f"Failed to load cookies: {e}")
            raise
    
    def _auto_setup_cookies(self) -> bool:
        """
        Automatically setup cookies when they're not found.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("🔧 Cookies not found. Starting automatic authentication setup...")
            print("\n" + "="*60)
            print("🔐 AUTHENTICATION REQUIRED")
            print("="*60)
            print("The cookies.pkl file is missing or invalid.")
            print("Starting browser for authentication...")
            print("Please login to TrendMicro XDR portal when the browser opens.")
            print("="*60)
            
            # Ask user if they want to proceed
            response = input("\nDo you want to setup authentication now? (y/n): ").lower().strip()
            if response not in ['y', 'yes']:
                self.logger.info("Authentication setup cancelled by user")
                return False
            
            return self.setup_authentication()
            
        except Exception as e:
            self.logger.error(f"Auto-setup failed: {e}")
            return False
    
    def _validate_cookies(self, cookies: List[Dict]) -> bool:
        """
        Validate if cookies are still valid by testing a request.
        
        Args:
            cookies: List of cookie dictionaries
            
        Returns:
            True if cookies are valid, False otherwise
        """
        try:
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Test with a simple request to the token endpoint
            response = session.get(self.TOKEN_URL, timeout=10)
            
            # If we get a successful response or redirect, cookies are likely valid
            if response.status_code in [200, 302, 401]:  # 401 might mean we need token but cookies work
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.warning(f"Cookie validation failed: {e}")
            return False
    
    def _handle_authentication_error(self, error: Exception) -> bool:
        """
        Handle authentication-related errors by attempting to refresh cookies.
        
        Args:
            error: The original exception
            
        Returns:
            True if recovery was successful, False otherwise
        """
        auth_error_indicators = [
            "Cookie file",
            "not found",
            "401",
            "Unauthorized",
            "Authentication",
            "Login required"
        ]
        
        error_str = str(error).lower()
        is_auth_error = any(indicator.lower() in error_str for indicator in auth_error_indicators)
        
        if is_auth_error:
            self.logger.warning("🔓 Authentication error detected. Attempting to refresh cookies...")
            
            # Check if cookies exist but might be expired
            if os.path.exists(self.COOKIE_PATH):
                self.logger.info("Existing cookies found but may be expired. Testing validity...")
                try:
                    cookies = self.load_cookies()
                    if not self._validate_cookies(cookies):
                        self.logger.warning("Cookies are invalid. Need to re-authenticate.")
                        return self._auto_setup_cookies()
                except:
                    return self._auto_setup_cookies()
            else:
                # No cookies file exists
                return self._auto_setup_cookies()
        
        return False
        """
        Get UIC token from session endpoint.
        
        Returns:
            UIC token string or None if failed
        """
        try:
            cookies = self.load_cookies()
            
            # Setup session with cookies
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            response = session.get(self.TOKEN_URL, timeout=self.timeout)
            response.raise_for_status()
            
            token = response.headers.get('uic-token')
            if token:
                self.token = token
                self.logger.info("Successfully obtained UIC token")
                return token
            else:
                self.logger.warning("UIC token not found in response headers")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get UIC token: {e}")
            return None
    
    def get_uic_token(self) -> str:
        """
        Get UIC token from session endpoint.
        
        Returns:
            UIC token string or None if failed
        """
        url = 'https://portal.sg.xdr.trendmicro.com/ui/uic/v3/session'
        with open(TrendMicroXDRScraper.COOKIE_PATH, 'rb') as fp:
            cookies = pickle.load(fp)

        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        response = session.get(url)
        return response.headers.get('uic-token')

    def query_cve_devices(self, cve_id: str, limit: int = 100, offset: int = 0, 
                         period: int = 30, status: str = "new") -> requests.Response:
        """
        Query devices affected by specific CVE.
        
        Args:
            cve_id: CVE identifier (e.g., CVE-2023-36025)
            limit: Maximum number of results
            offset: Results offset for pagination
            period: Time period in days
            status: Device status filter
            
        Returns:
            HTTP response object
        """
        url = f"{self.API_BASE}?cveId={cve_id}&offset={offset}&limit={limit}&period={period}&status={status}"
        
        max_retries = 2
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Load cookies and setup session
                cookies = self.load_cookies()
                session = requests.Session()
                
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'])
                
                # Get token if not already available
                if not self.token:
                    self.token = self.get_uic_token()
                
                if not self.token:
                    raise Exception("Failed to obtain UIC token")
                
                # Setup headers
                headers = {
                    'Content-Type': 'application/json',
                    'Uic-Token': self.token
                }
                session.headers.update(headers)
                
                # Make request
                response = session.get(url, timeout=self.timeout)
                
                # Check for authentication errors
                if response.status_code == 401:
                    raise Exception("Authentication failed (401 Unauthorized)")
                
                response.raise_for_status()
                
                self.logger.info(f"Successfully queried CVE {cve_id}")
                return response
                
            except Exception as e:
                self.logger.error(f"Failed to query CVE {cve_id} (attempt {retry_count + 1}): {e}")
                
                # Try to handle authentication errors
                if retry_count == 0 and self._handle_authentication_error(e):
                    self.logger.info(f"Retrying CVE {cve_id} after authentication refresh...")
                    self.token = None  # Reset token to force refresh
                    retry_count += 1
                    continue
                else:
                    raise
    
    def parse_device_info(self, json_data: Dict) -> List[Dict]:
        """
        Parse device information from API response.
        
        Args:
            json_data: JSON response from API
            
        Returns:
            List of device information dictionaries
        """
        device_info_list = []
        
        try:
            devices = json_data.get("data", {}).get("list", [])
        except (KeyError, TypeError, AttributeError):
            self.logger.error("Invalid JSON format in API response")
            return []
        
        for device in devices:
            device_info = {
                "deviceName": device.get("deviceName"),
                "ipAddress": device.get("ipAddress", []),
                "riskScore": device.get("riskScore", 0),
                "operatingSystem": device.get("operatingSystem", "Unknown"),
                "status": device.get("status", "Unknown"),
                "userId": device.get("userId"),
                "userName": device.get("userName")
            }
            device_info_list.append(device_info)
        
        return device_info_list
    
    def determine_priority(self, risk_score: int, device_name: str, ip_addresses: List[str]) -> str:
        """
        Determine patch priority based on risk score and device characteristics.
        
        Args:
            risk_score: Device risk score
            device_name: Device name
            ip_addresses: List of IP addresses
            
        Returns:
            Priority level string
        """
        # Server detection patterns
        server_keywords = ['SVR', 'SERVER', 'SRV', 'AWS', 'DB', 'SQL', 'WEB', 'APP', 'MAIL', 'DC', 'AD']
        is_server = any(keyword in device_name.upper() for keyword in server_keywords) if device_name else False
        
        # Critical infrastructure detection
        critical_keywords = ['MGTM', 'MGMT', 'PLANNER', 'OPS', 'CONTROL', 'SCADA', 'PROD', 'PRODUCTION']
        is_critical = any(keyword in device_name.upper() for keyword in critical_keywords) if device_name else False
        
        # Network segment analysis
        external_facing_patterns = ['192.168.', '10.', '172.']
        has_internal_ip = any(
            any(ip.startswith(pattern) for pattern in external_facing_patterns) 
            for ip in ip_addresses if ip and ip != '-'
        )
        
        # Priority determination logic
        if risk_score >= 80 or is_critical:
            return 'Critical'
        elif risk_score >= 60 or is_server:
            return 'High'
        elif risk_score >= 40:
            return 'Medium'
        elif risk_score >= 20:
            return 'Low'
        else:
            return 'Info'
    
    def get_patch_urgency_days(self, priority: str) -> int:
        """
        Get recommended patching timeframe based on priority.
        
        Args:
            priority: Priority level
            
        Returns:
            Number of days for patching
        """
        urgency_map = {
            'Critical': 1,
            'High': 7,
            'Medium': 30,
            'Low': 90,
            'Info': 180
        }
        return urgency_map.get(priority, 90)
    
    def print_formatted_results(self, cve_id: str, devices: List[Dict]) -> str:
        """
        Print and return formatted results for a CVE.
        
        Args:
            cve_id: CVE identifier
            devices: List of affected devices
            
        Returns:
            Formatted string output
        """
        header = "=" * 24
        output_lines = [
            header,
            f" CVE ID: {cve_id}",
            header,
            ""
        ]
        
        if devices:
            for device in devices:
                device_name = device['deviceName'] if device['deviceName'] else '-'
                ip_addresses = ', '.join(device['ipAddress']) if device['ipAddress'] and device['ipAddress'] != ['-'] else '-'
                output_lines.append(f"Device Name: {device_name}, IP Addresses: {ip_addresses}")
        else:
            output_lines.append("Device Name: -, IP Addresses: -")
        
        output_lines.append("")  # Blank line
        
        formatted_output = "\n".join(output_lines)
        print(formatted_output)
        
        return formatted_output
    
    def create_priority_csv(self, all_cve_data: Dict[str, List[Dict]], 
                           output_filename: str = None) -> None:
        """
        Create comprehensive CSV file with endpoint patch priority information.
        
        Args:
            all_cve_data: Dictionary mapping CVE IDs to device lists
            output_filename: Optional custom output filename
        """
        output_filename = output_filename or self.ENDPOINT_PRIORITY_CSV
        csv_data = []
        
        for cve_id, devices in all_cve_data.items():
            for device in devices:
                device_name = device['deviceName'] if device['deviceName'] else 'Unknown'
                ip_addresses = ', '.join(device['ipAddress']) if device['ipAddress'] and device['ipAddress'] != ['-'] else 'Unknown'
                operating_system = device.get('operatingSystem', 'Unknown')
                risk_score = device.get('riskScore', 0)
                
                # Determine priority
                priority = self.determine_priority(risk_score, device_name, device.get('ipAddress', []))
                urgency_days = self.get_patch_urgency_days(priority)
                
                # Calculate patch deadline
                patch_deadline = (datetime.now() + timedelta(days=urgency_days)).strftime('%Y-%m-%d')
                
                csv_row = {
                    'CVE_ID': cve_id,
                    'Device_Name': device_name,
                    'IP_Addresses': ip_addresses,
                    'Operating_System': operating_system,
                    'Risk_Score': risk_score,
                    'Priority': priority,
                    'Patch_Urgency_Days': urgency_days,
                    'Patch_Deadline': patch_deadline,
                    'Status': device.get('status', 'Pending'),
                    'User_ID': device.get('userId') or 'N/A',
                    'User_Name': device.get('userName') or 'N/A',
                    'Scan_Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                csv_data.append(csv_row)
        
        # Sort by priority and risk score
        priority_order = {'Critical': 1, 'High': 2, 'Medium': 3, 'Low': 4, 'Info': 5}
        csv_data.sort(key=lambda x: (priority_order.get(x['Priority'], 99), -x['Risk_Score']))
        
        # Write CSV file
        if csv_data:
            fieldnames = [
                'CVE_ID', 'Device_Name', 'IP_Addresses', 'Operating_System', 
                'Risk_Score', 'Priority', 'Patch_Urgency_Days', 'Patch_Deadline',
                'Status', 'User_ID', 'User_Name', 'Scan_Timestamp'
            ]
            
            try:
                with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
                
                self.logger.info(f"Endpoint patch priority CSV created: {output_filename}")
                self.logger.info(f"Total entries: {len(csv_data)}")
                
                # Print summary statistics
                priority_counts = {}
                for row in csv_data:
                    priority = row['Priority']
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                
                self.logger.info("Priority Distribution:")
                for priority in ['Critical', 'High', 'Medium', 'Low', 'Info']:
                    count = priority_counts.get(priority, 0)
                    if count > 0:
                        self.logger.info(f"  {priority}: {count} devices")
                        
            except Exception as e:
                self.logger.error(f"Failed to create CSV file: {e}")
                raise
        else:
            self.logger.warning("No data available to create CSV file.")
    
    def create_server_priority_csv(self, all_cve_data: Dict[str, List[Dict]]) -> None:
        """
        Create CSV file specifically for server devices.
        
        Args:
            all_cve_data: Dictionary mapping CVE IDs to device lists
        """
        server_pattern = re.compile(r'server', re.IGNORECASE)
        
        # Create header if file doesn't exist
        if not os.path.exists(self.PRIORITY_SERVERS_CSV):
            with open(self.PRIORITY_SERVERS_CSV, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Device Name', 'IP Addresses', 'Risk Score', 'Operating System', 'CVE ID'])
        
        # Append server data
        with open(self.PRIORITY_SERVERS_CSV, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            for cve_id, devices in all_cve_data.items():
                for device in devices:
                    operating_system = device.get('operatingSystem', '')
                    if server_pattern.search(operating_system):
                        writer.writerow([
                            device.get('deviceName', ''),
                            ', '.join(device.get('ipAddress', [])),
                            device.get('riskScore', 0),
                            device.get('operatingSystem', 'Unknown'),
                            cve_id
                        ])
        
        self.logger.info(f"Server priority data appended to {self.PRIORITY_SERVERS_CSV}")
    
    def setup_authentication(self) -> bool:
        """
        Setup authentication by launching browser and saving session.
        
        Returns:
            True if successful, False otherwise
        """
        driver = None
        try:
            self.logger.info("🚀 Starting authentication setup...")
            driver = self.create_driver()
            
            self.logger.info("🌐 Opening TrendMicro XDR portal...")
            driver.get(self.DASHBOARD_URL)
            
            print("\n" + "="*60)
            print("🔐 MANUAL LOGIN REQUIRED")
            print("="*60)
            print("A browser window has opened to the TrendMicro XDR portal.")
            print("Please:")
            print("1. Login with your credentials")
            print("2. Navigate to the main dashboard")
            print("3. Make sure you're fully logged in")
            print("4. Come back here and press Enter")
            print("="*60)
            
            input("Press Enter after completing login to save the session...")
            
            # Verify we're logged in by checking for specific elements or URLs
            current_url = driver.current_url
            if "login" in current_url.lower() or "auth" in current_url.lower():
                self.logger.warning("⚠️  It appears you may not be fully logged in yet.")
                response = input("Continue anyway? (y/n): ").lower().strip()
                if response not in ['y', 'yes']:
                    return False
            
            # Save cookies and session
            self.logger.info("💾 Saving cookies and session data...")
            self.save_cookies(driver)
            cookies, headers = self.extract_cookies_and_headers(driver, self.BASE_URL)
            self.save_session(cookies, headers)
            
            # Test the saved cookies
            self.logger.info("🧪 Testing saved cookies...")
            saved_cookies = self.load_cookies()
            if self._validate_cookies(saved_cookies):
                self.logger.info("✅ Cookies validated successfully!")
            else:
                self.logger.warning("⚠️  Cookie validation failed, but continuing...")
            
            self.logger.info("✅ Authentication setup completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to setup authentication: {e}")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def process_single_cve(self, cve_id: str) -> List[Dict]:
        """
        Process a single CVE and return device information.
        
        Args:
            cve_id: CVE identifier
            
        Returns:
            List of affected devices
        """
        try:
            response = self.query_cve_devices(cve_id)
            data = response.json()
            devices = self.parse_device_info(data)
            
            self.logger.info(f"Found {len(devices)} devices affected by {cve_id}")
            return devices
            
        except Exception as e:
            self.logger.error(f"Failed to process CVE {cve_id}: {e}")
            
            # Check if this is an authentication error and try recovery
            if self._handle_authentication_error(e):
                self.logger.info(f"🔄 Retrying CVE {cve_id} after authentication recovery...")
                try:
                    response = self.query_cve_devices(cve_id)
                    data = response.json()
                    devices = self.parse_device_info(data)
                    self.logger.info(f"✅ Successfully processed {cve_id} after retry - found {len(devices)} devices")
                    return devices
                except Exception as retry_error:
                    self.logger.error(f"❌ Retry failed for CVE {cve_id}: {retry_error}")
            
            return []
    
    def process_cve_list(self, cve_input: str, create_csv: bool = True) -> Dict[str, List[Dict]]:
        """
        Process multiple CVEs from file or single CVE.
        
        Args:
            cve_input: Path to CVE list file or single CVE ID
            create_csv: Whether to create CSV output files
            
        Returns:
            Dictionary mapping CVE IDs to device lists
        """
        all_cve_data = {}
        
        # Determine if input is file or single CVE
        if os.path.isfile(cve_input):
            self.logger.info(f"Loading CVE list from file: {cve_input}")
            try:
                with open(cve_input, "r", encoding='utf-8') as file:
                    cve_list = [line.strip() for line in file if line.strip()]
                self.logger.info(f"Loaded {len(cve_list)} CVE IDs from file")
            except Exception as e:
                self.logger.error(f"Failed to read CVE file: {e}")
                return {}
        else:
            self.logger.info(f"Processing single CVE: {cve_input}")
            cve_list = [cve_input]
        
        # Initialize output files
        if create_csv:
            # Clear/create priority endpoints file
            with open(self.PRIORITY_ENDPOINTS_FILE, 'w', encoding='utf-8') as f:
                f.write("")  # Clear file
        
        # Process each CVE
        for cve_id in cve_list:
            self.logger.info(f"Processing CVE: {cve_id}")
            
            try:
                devices = self.process_single_cve(cve_id)
                all_cve_data[cve_id] = devices
                
                # Save formatted output
                formatted_output = self.print_formatted_results(cve_id, devices)
                
                if create_csv:
                    # Append to priority endpoints file
                    with open(self.PRIORITY_ENDPOINTS_FILE, 'a', encoding='utf-8') as f:
                        f.write(formatted_output)
                
                # Small delay to avoid overwhelming the server
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Failed to process {cve_id}: {e}")
                all_cve_data[cve_id] = []
        
        # Create CSV files
        if create_csv and all_cve_data:
            self.logger.info("Generating CSV files...")
            self.create_priority_csv(all_cve_data)
            self.create_server_priority_csv(all_cve_data)
        
        return all_cve_data


def main():
    """Main function to handle command line arguments and execute scraper."""
    parser = argparse.ArgumentParser(
        description="TrendMicro XDR CVE Device Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --cve CVE-2023-36025                    # Process single CVE
  %(prog)s --cve cve_list.txt                      # Process CVE list from file
  %(prog)s --cve CVE-2023-36025 --no-csv          # Skip CSV generation
  %(prog)s --setup-auth                            # Setup authentication
  %(prog)s --cve CVE-2023-36025 --headless        # Run in headless mode
        """
    )
    
    parser.add_argument(
        "--cve",
        help="CVE ID to query (e.g., CVE-2023-36025) or path to file containing CVE list"
    )
    
    parser.add_argument(
        "--setup-auth",
        action="store_true",
        help="Setup authentication by launching browser (run this first)"
    )
    
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip CSV file generation"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Request timeout in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--output",
        help="Custom output filename for priority CSV"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.setup_auth and not args.cve:
        parser.error("Either --cve or --setup-auth is required")
    
    # Initialize scraper
    scraper = TrendMicroXDRScraper(headless=args.headless, timeout=args.timeout)
    
    try:
        # Setup authentication if requested
        if args.setup_auth:
            if scraper.setup_authentication():
                print("\n✅ Authentication setup completed successfully!")
                print("You can now run CVE queries using the --cve parameter.")
            else:
                print("\n❌ Authentication setup failed!")
                sys.exit(1)
            return
        
        # Process CVE queries
        if args.cve:
            print(f"\n🔍 Starting CVE analysis...")
            all_cve_data = scraper.process_cve_list(args.cve, create_csv=not args.no_csv)
            
            if all_cve_data:
                total_devices = sum(len(devices) for devices in all_cve_data.values())
                print(f"\n✅ Analysis completed!")
                print(f"📊 Processed {len(all_cve_data)} CVE(s)")
                print(f"🖥️  Found {total_devices} affected devices")
                
                if not args.no_csv:
                    print(f"📄 Generated CSV files:")
                    print(f"   - {scraper.ENDPOINT_PRIORITY_CSV}")
                    print(f"   - {scraper.PRIORITY_SERVERS_CSV}")
                    print(f"   - {scraper.PRIORITY_ENDPOINTS_FILE}")
            else:
                print("\n⚠️  No data was retrieved. Please check your authentication and CVE inputs.")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()