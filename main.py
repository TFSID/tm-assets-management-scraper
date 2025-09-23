from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
# import undetected_chromedriver as uc
import time
import sys
import re
import os
import json
import requests
import pickle
import csv

import argparse

SESSION_FILE = "session_data.json"
COOKIE_PATH = "cookies.pkl"
CVEID = "CVE-2015-7645"

# Set your Chrome user data path (adjust this!)
profile_dir = "chrome_profile"  # or "Profile 1", etc.
profile_name = "Profile 1"  # or "Profile 1", etc.
profile_path = os.path.abspath(profile_dir)

target_url = "https://portal.sg.xdr.trendmicro.com/index.html#/app/sase"

def create_driver():
    options = Options()
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument(f"--profile-directory={profile_name}")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-default-apps")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--start-maximized")

    print(f"[INFO] Starting Chrome with profile at: {profile_path}")
    driver = webdriver.Chrome(service=Service(), options=options)
    return driver

def extract_cookies_headers(driver, base_url):
    cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
    headers = {
        "User-Agent": driver.execute_script("return navigator.userAgent"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": base_url,
        "Connection": "keep-alive"
    }

    # Optional: extract token from localStorage
    try:
        token = driver.execute_script("return localStorage.getItem('access_token')")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    except:
        pass

    return cookies, headers

def save_session_to_file(cookies, headers, filename=SESSION_FILE):
    
    with open(filename, "w") as f:
        json.dump({"cookies": cookies, "headers": headers}, f, indent=2)
    print(f"[INFO] Session saved to {filename}")

def get_deviceList(driver):
    cveId = "CVE-2023-36025"
    dashboard = "https://portal.sg.xdr.trendmicro.com/index.html#/app/sase"
    target = f"https://portal.sg.xdr.trendmicro.com/public/ass/api/v1/trilogy/deviceListByCve?cveId={cveId}&offset=0&limit=1&period=30&status=new"
    
    def run_scrape(target_url):
        try:
            driver.get(target_url)
            print(f"[INFO] Navigated to: {target_url}")
            
            input("Press Enter to save sessions...")
            
            # selenium_cookies = driver.get_cookies()
            # cookie_jar = {cookie['name']: cookie['value'] for cookie in selenium_cookies}.
            cookie = driver.get_cookies()
            with open(COOKIE_PATH, 'wb') as fp:
                pickle.dump(cookie, fp) 

            cookies, headers = extract_cookies_headers(driver, target)
            save_session_to_file(cookies, headers)
            cookies, headers = load_session_from_file()
            use_requests_session(cookies, headers, target_url)
            input("Press Enter to continue...")

        except Exception as e:
            print(f"[ERROR] Could not navigate to: {target_url} - {e}")
            driver.quit()    
    try:
        run_scrape(target_url=dashboard)
    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")

    try:
        run_scrape(target_url=target)
    except Exception as e:
        print(f"[ERROR] Scraping failed: {e}")

def use_requests_session(cookies, headers, target_url):
    with requests.Session() as session:
        session.cookies.update(cookies)
        session.headers.update(headers)
        print(f"[INFO] Requesting {target_url}")
        response = session.get(target_url)
        print(f"[STATUS] {response.status_code}")
        print(response.text[:500])

def load_session_from_file(filename=SESSION_FILE):
    if not os.path.exists(filename):
        raise FileNotFoundError(f"[ERROR] Session file '{filename}' not found.")

    with open(filename, "r") as f:
        session_data = json.load(f)

    print(f"[INFO] Loaded session from {filename}")
    return session_data["cookies"], session_data["headers"]

def get_token():
    # url = 'https://portal.sg.xdr.trendmicro.com/#/app/search'
    url = 'https://portal.sg.xdr.trendmicro.com/ui/uic/v3/session'
    

    with open(COOKIE_PATH, 'rb') as fp:
        cookies = pickle.load(fp)

    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    response = session.get(url)

    # print(response.json())
    # print(response.headers)
    # sys.exit()
    # token = response.headers.get('uic-token')
    # print('token', token)
    # if token:
    #     return token
    return response.headers.get('uic-token')

def load_cookies_from_file(cookie_path=COOKIE_PATH):
    if not os.path.exists(cookie_path):
        raise FileNotFoundError(f"[ERROR] Cookie file '{cookie_path}' not found.")

    with open(cookie_path, 'rb') as fp:
        cookies = pickle.load(fp)

    print(f"[INFO] Loaded cookies from {cookie_path}")
    return cookies

def test_requests_session(cveId):
    # url = "https://portal.sg.xdr.trendmicro.com/public/ass/api/v1/trilogy/deviceListByCve?cveId={CVEID}"
    url = f"https://portal.sg.xdr.trendmicro.com/public/ass/api/v1/trilogy/deviceListByCve?cveId={cveId}&offset=0&limit=100&period=30&status=new"
    session = requests.Session()
    # cookies_1, headers = load_session_from_file()
    try:
        try:
            with open(COOKIE_PATH, 'rb') as fp:
                cookies = pickle.load(fp)
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
        except Exception as e:
            return f"[ERROR] Failed to process load cookies: {e}"
        try:
            token = get_token()
            headers = {'Content-type': 'application/json', 'Uic-Token': token}
            session.headers.update(headers)
            response = session.get(url)
        except Exception as e:
            return f"[ERROR] Failed to process get token: {e}"
        print(response.text)
        return response
    except Exception as e:
        return f"[ERROR] Failed to rest requests session {cveId}: {e}"
    # use_requests_session(cookies, headers, url)

def get_device_info(json_data):
    device_info_list = []

    try:
        devices = json_data["data"]["list"]
    except (KeyError, TypeError):
        print("Invalid JSON format")
        return []

    for device in devices:
        device_name = device.get("deviceName")
        ip_addresses = device.get("ipAddress", [])
        riskScore = device.get("riskScore", 0)
        operatingSystem = device.get("operatingSystem", "Unknown")
        device_info_list.append({
            "deviceName": device_name,
            "ipAddress": ip_addresses,
            "riskScore": riskScore,
            "operatingSystem": operatingSystem
        })

    return device_info_list

def determine_priority(risk_score, device_name, ip_addresses):
    """Determine patch priority based on risk score and device characteristics"""
    # Server detection patterns
    server_keywords = ['SVR', 'SERVER', 'SRV', 'AWS', 'DB', 'SQL', 'WEB', 'APP', 'MAIL', 'DC', 'AD']
    is_server = any(keyword in device_name.upper() for keyword in server_keywords)
    
    # Critical infrastructure detection
    critical_keywords = ['MGTM', 'MGMT', 'PLANNER', 'OPS', 'CONTROL', 'SCADA']
    is_critical = any(keyword in device_name.upper() for keyword in critical_keywords)
    
    # Network segment analysis (simplified)
    has_external_facing = any(ip.startswith(('192.168.', '10.')) for ip in ip_addresses.split(', ') if ip != '-')
    
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

def get_patch_urgency_days(priority):
    """Get recommended patching timeframe based on priority"""
    urgency_map = {
        'Critical': 1,
        'High': 7,
        'Medium': 30,
        'Low': 90,
        'Info': 180
    }
    return urgency_map.get(priority, 90)

def create_endpoint_patch_priority_csv(all_cve_data, output_filename='endpoint_patch_priority.csv'):
    """Create CSV file with endpoint patch priority information"""
    
    # Prepare data for CSV
    csv_data = []
    
    for cve_id, devices in all_cve_data.items():
        for device in devices:
            device_name = device['deviceName'] if device['deviceName'] else 'Unknown'
            ip_addresses = ', '.join(device['ipAddress']) if device['ipAddress'] and device['ipAddress'] != ['-'] else 'Unknown'
            operating_system = device.get('operatingSystem', 'Unknown')
            risk_score = device.get('riskScore', 0)
            
            # Determine priority
            priority = determine_priority(risk_score, device_name, ip_addresses)
            urgency_days = get_patch_urgency_days(priority)
            
            # Calculate patch deadline (simplified - using current date + urgency days)
            from datetime import datetime, timedelta
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
                'User_Name': device.get('userName') or 'N/A'
            }
            csv_data.append(csv_row)
    
    # Sort by priority (Critical first) and then by risk score (descending)
    priority_order = {'Critical': 1, 'High': 2, 'Medium': 3, 'Low': 4, 'Info': 5}
    csv_data.sort(key=lambda x: (priority_order.get(x['Priority'], 99), -x['Risk_Score']))
    
    # Write to CSV file
    if csv_data:
        fieldnames = [
            'CVE_ID', 'Device_Name', 'IP_Addresses', 'Operating_System', 
            'Risk_Score', 'Priority', 'Patch_Urgency_Days', 'Patch_Deadline',
            'Status', 'User_ID', 'User_Name'
        ]
        
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        
        print(f"[INFO] Endpoint patch priority CSV created: {output_filename}")
        print(f"[INFO] Total entries: {len(csv_data)}")
        
        # Print summary statistics
        priority_counts = {}
        for row in csv_data:
            priority = row['Priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        print("\n[INFO] Priority Distribution:")
        for priority in ['Critical', 'High', 'Medium', 'Low', 'Info']:
            count = priority_counts.get(priority, 0)
            if count > 0:
                print(f"  {priority}: {count} devices")
    else:
        print("[WARNING] No data available to create CSV file.")

def process_cves_with_csv_output(cve_input, csv_output='endpoint_patch_priority.csv'):
    all_cve_data = {}  # Store all CVE data for CSV generation
    
    if os.path.isfile(cve_input):
        with open(cve_input, "r") as file:
            cve_list = [line.strip() for line in file if line.strip()]
            print(f"[INFO] Loaded {len(cve_list)} CVE IDs from file.")
        
        for cve_id in cve_list:
            print(f"[INFO] Querying CVE: {cve_id}")
            try:
                deviceListData = test_requests_session(cve_id)
                data = []
                data.append(deviceListData.str)
                data = json.loads("".join(data))
                results = get_device_info(data)
                print(f"[INFO] Found {len(results)} devices with CVE {cve_id}:")
                
                # Store data for CSV generation
                all_cve_data[cve_id] = results
                
                # Print formatted output
                print_formatted_results(cve_id, results)
                
            except Exception as e:
                print(f"[ERROR] Failed to process csv output {cve_id}: {e}")
                # Still store empty results for CSV
                all_cve_data[cve_id] = []
                print_formatted_results(cve_id, [])
        
        # Generate CSV file after processing all CVEs
        print("\n" + "="*50)
        print("GENERATING ENDPOINT PATCH PRIORITY CSV")
        print("="*50)
        create_endpoint_patch_priority_csv(all_cve_data, csv_output)
        
    else:
        raise FileNotFoundError

def print_formatted_results(cve_id, results):
    """Print results in the specified format"""
    print("=" * 24)
    print(f" CVE ID: {cve_id}")
    print("=" * 24)
    print()
    
    if results:
        for device in results:
            device_name = device['deviceName'] if device['deviceName'] else '-'
            ip_addresses = ', '.join(device['ipAddress']) if device['ipAddress'] and device['ipAddress'] != ['-'] else '-'
            print(f"Device Name: {device_name}, IP Addresses: {ip_addresses}")
    else:
        print("Device Name: -, IP Addresses: -")
    
    print()  # Add blank line after each CVE section

    return "\n".join([
        "=" * 24,
        f" CVE ID: {cve_id}",
        "=" * 24,
        "",
        "\n".join(
            f"Device Name: {device['deviceName'] if device['deviceName'] else '-'}, "
            f"IP Addresses: {', '.join(device['ipAddress']) if device['ipAddress'] and device['ipAddress'] != ['-'] else '-'}"
            for device in results
        ),
        ""
    ])


def test_selenium_session(driver, target_url):
    # driver = create_driver()
    driver.get("https://portal.sg.xdr.trendmicro.com")
    input("Press Enter to continue and save cookies...")
    cookie = driver.get_cookies()
    with open(COOKIE_PATH, 'wb') as fp:
        pickle.dump(cookie, fp) 
    
    sys.exit()
    with open(COOKIE_PATH, 'rb') as fp:
        cookies = pickle.load(fp)

    # for cookie in cookies:
        # session.cookies.set(cookie['name'], cookie['value'])

    for cookie in cookies:
        # cookie_dict = {
        #     'name': cookie['name'],
        #     'value': cookie['value'],
        #     'domain': cookie['domain'],
        #     'path': cookie['path'],
        #     'expires': cookie['expiry']
        # }
        cookie_dict = {'name': cookie['name'], 'value': cookie['value']}
        driver.add_cookie(cookie_dict)
        # cookie_dict.append({'name': cookie['name'], 'value': cookie['value']})
        print(f"[INFO] Added cookie: {cookie_dict['name']}={cookie_dict['value']}")

    token = get_token()
    driver.add_cookie({'name': 'Uic-Token', 'value': token})
    print(f"[INFO] Added token cookie: Uic-Token={token}")
    # token = driver.execute_script("return localStorage.getItem('Uic-Token')")
    # print(f"[INFO] Token: {token}")
    # Since Selenium doesn't directly support custom headers for GET requests,
    # we'll use JavaScript to make the API call with custom headers
    # script = f"""
    #     var xhr = new XMLHttpRequest();
    #     xhr.open('GET', '{target_url}', false);
    #     xhr.setRequestHeader('Content-Type', 'application/json');
    #     xhr.setRequestHeader('Uic-Token', '{token}');
    #     xhr.send();
    #     return xhr.responseText;
    #     """
    # #  Execute the JavaScript to make the API call
    # response = driver.execute_script(script)
    # print(f"[INFO] API response: {response}")
    
    driver.get(target_url)
    input("Press Enter to continue...")
    sys.exit()

    cookies, headers = extract_cookies_headers(driver, target_url)
    save_session_to_file(cookies, headers)
    driver.quit()
    use_requests_session(cookies, headers, target_url)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch CVE info using Selenium session or API call.")
    parser.add_argument(
        "--cve", 
        required=True,
        help="CVE ID to query (e.g., CVE-2015-7645)"
    )
    args = parser.parse_args()
    cve_input = args.cve


    # Gunakan try-except untuk mendeteksi apakah input adalah file atau bukan
    try:
        if os.path.isfile(cve_input):
            with open(cve_input, "r") as file:
                cve_list = [line.strip() for line in file if line.strip()]
                print(f"[INFO] Loaded {len(cve_list)} CVE IDs from file.")
            # with open('PRIORITY_ENDPOINTS.csv', 'a', encoding='utf-8') as f:
                # f.write(f"Device Name, IP Addresses, CVE ID\n")
            with open('PRIORITY_PATCH_SERVERS.csv', 'a', encoding='utf-8') as f:
                f.write(f"Device Name, IP Addresses, riskScore, operatingSystem, CVE ID\n")
            for cve_id in cve_list:
                print(f"[INFO] Querying CVE: {cve_id}")
                # with open(f'{cve_id}.csv', 'a', encoding='utf-8') as f:
                    # f.write(f"Device Name, IP Addresses, riskScore, operatingSystem\n")
                try:
                    try:
                        print(f"Try to use requests session")
                        deviceListData = test_requests_session(cve_id)
                    except Exception as e:
                        print(f"Try to use selenium session")
                        driver = create_driver()
                        target = f"https://portal.sg.xdr.trendmicro.com/public/ass/api/v1/trilogy/deviceListByCve?cveId={CVEID}&offset=0&limit=1&period=30&status=new"
                        deviceListData = test_selenium_session(driver, target)
                    data = []
                    data.append(deviceListData.text)
                    data = json.loads("".join(data))
                    results = get_device_info(data)
                    print(f"[INFO] Found {len(results)} devices with CVE {cve_id}:")
                    try:
                        with open('PRIORITY_ENDPOINTS.txt', 'a', encoding='utf-8') as f:
                            contents = print_formatted_results(cve_id, results)
                            f.write(contents)
                        for device in results:
                            with open('PRIORITY_PATCH_SERVERS.csv', 'a', encoding='utf-8', newline='') as fcsv:
                                writer = csv.writer(fcsv)
                                pattern = re.compile(r'server', re.IGNORECASE)
                                opSystem = device.get('operatingSystem', '')
                                if pattern.search(opSystem):
                                    writer.writerow([
                                        device.get('deviceName', ''),
                                        ', '.join(device.get('ipAddress', [])),
                                        device.get('riskScore', 0),
                                        device.get('operatingSystem', 'Unknown'),
                                        cve_id
                                    ])
                    except Exception as e:
                        print(f"[ERROR] Failed to process PRIORITY_ENDPOINTS.txt.print formatted results {cve_id}: {e}")
                        # if device['operatingSystem'] != 'Server':

                        # ITS WORKS CHAT

                        # with open(f'{cve_id}.csv', 'a', encoding='utf-8', newline='') as fcsv:
                        #     writer = csv.writer(fcsv)
                        #     for device in results:
                        #         opSystem = device.get('operatingSystem', '')
                        #         pattern = re.compile(r'server', re.IGNORECASE)
                        #         if pattern.search(opSystem):
                        #             writer.writerow([
                        #                 device.get('deviceName', ''),
                        #                 ', '.join(device.get('ipAddress', [])),
                        #                 device.get('riskScore', 0),
                        #                 device.get('operatingSystem', 'Unknown')
                        #             ])


                        # fcsv.write(f"{device['deviceName']}, \"{', '.join(device['ipAddress'])}\", {cve_id}\n")
                        # contents = f.read()
                        # print(contents)
                        # for device in results:
                        #     print(f"Device Name: {device['deviceName']}, IP Addresses: {', '.join(device['ipAddress'])}")
                except Exception as e:
                    print(f"[ERROR] Failed to process {cve_id}: {e}")
            # process_cves_with_csv_output(data, 'endpoint_patch_priority.csv')
            # process_cves_with_csv_output('PRIORITY_ENDPOINTS.txt', 'endpoint_patch_priority.csv')

        else:
            raise FileNotFoundError
    except Exception:
        print(f"[WARNING] Treating '{cve_input}' as a single CVE ID input.")
        cve_list = [cve_input]
        deviceListData = test_requests_session(cve_input)
    # data = json.loads(deviceListData.text)
    # results = get_device_info(data)
    # print(f"[INFO] Found {len(results)} devices with CVE {args.cve}:")
    # for device in results:
        # print(f"Device Name: {device['deviceName']}, IP Addresses: {', '.join(device['ipAddress'])}")
    




    # args = parse_args()
    # target = args.target
    # with open(args.wordlist, "r") as f:
    #     keyword = f.read()
    #     print(f"{keyword}")
    # sys.exit()
    # cveId = "CVE-2023-36025"

    # base_url = "https://portal.sg.xdr.trendmicro.com/index.html#/app/sase"
    # target = f"https://portal.sg.xdr.trendmicro.com/public/ass/api/v1/trilogy/deviceListByCve?cveId={CVEID}&offset=0&limit=1&period=30&status=new"


    # driver = create_driver()
    # cookies, headers = extract_cookies_headers(driver, base_url)
    # get_deviceList(driver)
    # save_session_to_file(cookies, headers)
    # driver.quit()
    # use_requests_session(cookies, headers, target_url)
    # print(get_token())
    # test_selenium_session(driver, target)
    # cookies, headers = load_session_from_file()
    # use_requests_session(cookies, headers, targ1et)
    # scrape_page(target)
    # links_scraper(target, "output.txt")
    
