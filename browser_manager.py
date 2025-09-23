"""
Browser Manager Module
Handles browser initialization, configuration, and management.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
import undetected_chromedriver as uc

from config import BROWSER_CONFIG, CHROME_OPTIONS, get_profile_path


class BrowserManager:
    """Manages browser instances and configurations."""
    
    def __init__(self, use_undetected=True, headless=False, custom_options=None):
        """
        Initialize the browser manager.
        
        Args:
            use_undetected (bool): Whether to use undetected-chromedriver
            headless (bool): Whether to run in headless mode
            custom_options (list): Additional Chrome options
        """
        self.use_undetected = use_undetected
        self.headless = headless
        self.custom_options = custom_options or []
        self.driver = None
        self.wait = None
        
    def create_driver(self):
        """Create and configure a new browser driver."""
        try:
            options = self._configure_options()
            
            if self.use_undetected:
                self.driver = uc.Chrome(options=options)
            else:
                self.driver = webdriver.Chrome(service=Service(), options=options)
            
            self._configure_driver()
            self.wait = WebDriverWait(self.driver, BROWSER_CONFIG["wait_timeout"])
            
            print(f"[INFO] Browser initialized successfully")
            return self.driver
            
        except WebDriverException as e:
            print(f"[ERROR] Failed to create browser driver: {e}")
            raise
    
    def _configure_options(self):
        """Configure Chrome options."""
        options = Options()
        
        # Add profile configuration
        profile_path = get_profile_path()
        options.add_argument(f"--user-data-dir={profile_path}")
        options.add_argument(f"--profile-directory={BROWSER_CONFIG['chrome_profile_name']}")
        
        # Add standard Chrome options
        for option in CHROME_OPTIONS:
            options.add_argument(option)
        
        # Add custom options
        for option in self.custom_options:
            options.add_argument(option)
        
        # Add headless option if requested
        if self.headless:
            options.add_argument("--headless")
        
        return options
    
    def _configure_driver(self):
        """Configure driver settings."""
        if self.driver:
            self.driver.set_page_load_timeout(BROWSER_CONFIG["page_load_timeout"])
            self.driver.implicitly_wait(BROWSER_CONFIG["implicit_wait"])
    
    def navigate_to(self, url, wait_for_element=None, timeout=None):
        """
        Navigate to a URL and optionally wait for an element.
        
        Args:
            url (str): The URL to navigate to
            wait_for_element (tuple): Element locator to wait for
            timeout (int): Custom timeout in seconds
            
        Returns:
            bool: True if navigation successful
        """
        try:
            print(f"[INFO] Navigating to: {url}")
            self.driver.get(url)
            
            if wait_for_element:
                wait_time = timeout or BROWSER_CONFIG["wait_timeout"]
                WebDriverWait(self.driver, wait_time).until(
                    EC.presence_of_element_located(wait_for_element)
                )
                print(f"[INFO] Element found: {wait_for_element}")
            
            return True
            
        except TimeoutException:
            print(f"[WARNING] Timeout waiting for element: {wait_for_element}")
            return False
        except Exception as e:
            print(f"[ERROR] Navigation failed: {e}")
            return False
    
    def wait_for_element(self, locator, timeout=None):
        """
        Wait for an element to be present.
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Custom timeout in seconds
            
        Returns:
            WebElement or None: The found element or None if not found
        """
        try:
            wait_time = timeout or BROWSER_CONFIG["wait_timeout"]
            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            print(f"[WARNING] Element not found within {wait_time}s: {locator}")
            return None
    
    def find_elements(self, locator, timeout=None):
        """
        Find multiple elements.
        
        Args:
            locator (tuple): Element locator (By, value)
            timeout (int): Custom timeout in seconds
            
        Returns:
            list: List of found elements
        """
        try:
            wait_time = timeout or BROWSER_CONFIG["wait_timeout"]
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located(locator)
            )
            return self.driver.find_elements(*locator)
        except TimeoutException:
            print(f"[WARNING] No elements found within {wait_time}s: {locator}")
            return []
    
    def scroll_to_bottom(self, pause_time=1):
        """
        Scroll to the bottom of the page.
        
        Args:
            pause_time (int): Time to pause between scrolls
        """
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while True:
                # Scroll down to bottom
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait to load page
                time.sleep(pause_time)
                
                # Calculate new scroll height and compare with last scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
            print("[INFO] Scrolled to bottom of page")
            
        except Exception as e:
            print(f"[ERROR] Failed to scroll: {e}")
    
    def take_screenshot(self, filename):
        """
        Take a screenshot and save it.
        
        Args:
            filename (str): Name of the screenshot file
        """
        try:
            self.driver.save_screenshot(filename)
            print(f"[INFO] Screenshot saved: {filename}")
        except Exception as e:
            print(f"[ERROR] Failed to take screenshot: {e}")
    
    def get_page_source(self):
        """Get the current page source."""
        return self.driver.page_source
    
    def get_cookies(self):
        """Get all cookies from the current session."""
        return self.driver.get_cookies()
    
    def get_user_agent(self):
        """Get the current user agent string."""
        return self.driver.execute_script("return navigator.userAgent")
    
    def close(self):
        """Close the browser driver."""
        if self.driver:
            try:
                self.driver.quit()
                print("[INFO] Browser closed successfully")
            except Exception as e:
                print(f"[ERROR] Failed to close browser: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        self.create_driver()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_browser_manager(use_undetected=True, headless=False, custom_options=None):
    """
    Factory function to create a browser manager.
    
    Args:
        use_undetected (bool): Whether to use undetected-chromedriver
        headless (bool): Whether to run in headless mode
        custom_options (list): Additional Chrome options
        
    Returns:
        BrowserManager: Configured browser manager instance
    """
    return BrowserManager(
        use_undetected=use_undetected,
        headless=headless,
        custom_options=custom_options
    ) 