import os
import json
import yaml
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from datetime import datetime

class BrowserAutomation:
    def __init__(self, config_file="config.yaml"):
        self.config = self.load_config(config_file)
        self.driver = None
        self.setup_logging()
        
    def load_config(self, config_file):
        """Load configuration from YAML or JSON file"""
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file {config_file} not found!")
            raise
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            raise
    
    def setup_logging(self):
        """Setup logging based on config"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO').upper())
        log_format = log_config.get('format', '%(asctime)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_config.get('file', 'automation.log')),
                logging.StreamHandler()
            ]
        )
        
    def create_driver(self):
        """Create Chrome driver with configured options"""
        browser_config = self.config.get('browser', {})
        
        options = Options()
        
        # Chrome profile settings
        if browser_config.get('user_data_dir'):
            options.add_argument(f"--user-data-dir={browser_config['user_data_dir']}")
        if browser_config.get('profile_directory'):
            options.add_argument(f"--profile-directory={browser_config['profile_directory']}")
            
        # Browser options
        for option in browser_config.get('chrome_options', []):
            options.add_argument(option)
            
        # Headless mode
        if browser_config.get('headless', False):
            options.add_argument('--headless')
            
        # Window size
        window_size = browser_config.get('window_size')
        if window_size:
            options.add_argument(f"--window-size={window_size}")
            
        logging.info("Starting Chrome browser...")
        self.driver = webdriver.Chrome(service=Service(), options=options)
        
        # Set timeouts
        timeouts = self.config.get('timeouts', {})
        self.driver.implicitly_wait(timeouts.get('implicit', 10))
        self.driver.set_page_load_timeout(timeouts.get('page_load', 30))
        
        return self.driver
    
    def execute_action(self, action):
        """Execute a single action based on configuration"""
        action_type = action.get('type')
        
        try:
            if action_type == 'navigate':
                url = action['url']
                logging.info(f"Navigating to: {url}")
                self.driver.get(url)
                
            elif action_type == 'wait':
                duration = action.get('duration', 1)
                logging.info(f"Waiting for {duration} seconds...")
                time.sleep(duration)
                
            elif action_type == 'wait_for_element':
                selector = action['selector']
                timeout = action.get('timeout', 10)
                logging.info(f"Waiting for element: {selector}")
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                
            elif action_type == 'click':
                selector = action['selector']
                timeout = action.get('timeout', 10)
                logging.info(f"Clicking element: {selector}")
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                
            elif action_type == 'fill':
                selector = action['selector']
                text = action['text']
                clear_first = action.get('clear', True)
                timeout = action.get('timeout', 10)
                logging.info(f"Filling element {selector} with: {text}")
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                if clear_first:
                    element.clear()
                element.send_keys(text)
                
            elif action_type == 'screenshot':
                filename = action.get('filename', f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                logging.info(f"Taking screenshot: {filename}")
                self.driver.save_screenshot(filename)
                
            elif action_type == 'scroll':
                direction = action.get('direction', 'down')
                pixels = action.get('pixels', 500)
                if direction == 'down':
                    self.driver.execute_script(f"window.scrollBy(0, {pixels});")
                elif direction == 'up':
                    self.driver.execute_script(f"window.scrollBy(0, -{pixels});")
                elif direction == 'top':
                    self.driver.execute_script("window.scrollTo(0, 0);")
                elif direction == 'bottom':
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                logging.info(f"Scrolled {direction}")
                
            elif action_type == 'extract_text':
                selector = action['selector']
                variable_name = action.get('variable', 'extracted_text')
                timeout = action.get('timeout', 10)
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                text = element.text
                logging.info(f"Extracted text from {selector}: {text}")
                # Store in a simple way - you could extend this to save to file/database
                setattr(self, variable_name, text)
                
            elif action_type == 'extract_attribute':
                selector = action['selector']
                attribute = action['attribute']
                variable_name = action.get('variable', 'extracted_attribute')
                timeout = action.get('timeout', 10)
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                attr_value = element.get_attribute(attribute)
                logging.info(f"Extracted {attribute} from {selector}: {attr_value}")
                setattr(self, variable_name, attr_value)
                
            elif action_type == 'send_keys':
                keys = action['keys']
                if keys == 'ENTER':
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ENTER)
                elif keys == 'TAB':
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.TAB)
                # Add more special keys as needed
                logging.info(f"Sent keys: {keys}")
                
            elif action_type == 'switch_tab':
                tab_index = action.get('index', -1)  # -1 for last tab
                if tab_index == -1:
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                else:
                    self.driver.switch_to.window(self.driver.window_handles[tab_index])
                logging.info(f"Switched to tab {tab_index}")
                
            # Add sleep after action if specified
            if action.get('sleep_after'):
                time.sleep(action['sleep_after'])
                
        except Exception as e:
            logging.error(f"Error executing action {action_type}: {e}")
            if action.get('continue_on_error', False):
                logging.info("Continuing despite error...")
            else:
                raise
    
    def run_scenario(self, scenario_name):
        """Run a specific scenario from config"""
        scenarios = self.config.get('scenarios', {})
        if scenario_name not in scenarios:
            logging.error(f"Scenario '{scenario_name}' not found in config!")
            return
            
        scenario = scenarios[scenario_name]
        logging.info(f"Running scenario: {scenario_name}")
        
        # Execute pre-actions if any
        pre_actions = scenario.get('pre_actions', [])
        for action in pre_actions:
            self.execute_action(action)
            
        # Execute main actions
        actions = scenario.get('actions', [])
        for action in actions:
            self.execute_action(action)
            
        # Execute post-actions if any
        post_actions = scenario.get('post_actions', [])
        for action in post_actions:
            self.execute_action(action)
            
        logging.info(f"Completed scenario: {scenario_name}")
    
    def run_interactive_mode(self):
        """Run interactive mode for testing and debugging"""
        print("\n💡 Interactive mode - Enter commands:")
        print("   - scenario <name>  : Run a scenario")
        print("   - action <json>    : Execute single action")
        print("   - screenshot      : Take screenshot")
        print("   - exit            : Exit")
        
        while True:
            try:
                cmd = input(">>> ").strip()
                if not cmd:
                    continue
                    
                if cmd == "exit":
                    break
                elif cmd.startswith("scenario "):
                    scenario_name = cmd[9:].strip()
                    self.run_scenario(scenario_name)
                elif cmd.startswith("action "):
                    action_json = cmd[7:].strip()
                    action = json.loads(action_json)
                    self.execute_action(action)
                elif cmd == "screenshot":
                    self.execute_action({"type": "screenshot"})
                else:
                    print("Unknown command")
                    
            except Exception as e:
                logging.error(f"Error in interactive mode: {e}")
    
    def run(self):
        """Main execution method"""
        try:
            self.create_driver()
            
            # Check if we should run specific scenarios
            scenarios_to_run = self.config.get('run_scenarios', [])
            
            if scenarios_to_run:
                for scenario_name in scenarios_to_run:
                    self.run_scenario(scenario_name)
            else:
                # Run interactive mode if no scenarios specified
                self.run_interactive_mode()
                
        except Exception as e:
            logging.error(f"Error during execution: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Configurable Browser Automation')
    parser.add_argument('--config', default='config.yaml', help='Config file path')
    parser.add_argument('--scenario', help='Specific scenario to run')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    automation = BrowserAutomation(args.config)
    
    if args.scenario:
        automation.create_driver()
        automation.run_scenario(args.scenario)
        automation.driver.quit()
    elif args.interactive:
        automation.create_driver()
        automation.run_interactive_mode()
        automation.driver.quit()
    else:
        automation.run()

if __name__ == "__main__":
    main()