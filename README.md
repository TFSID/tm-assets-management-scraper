# Modular Web Scraper

A comprehensive, modular web scraping application built with Python and Selenium. This scraper is designed to be reusable, maintainable, and extensible for various web scraping tasks.

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated modules for different functionalities
- **Multiple Site Support**: Built-in scrapers for Shopee, BUMN, Kementrian, and TrendMicro
- **Session Management**: Persistent session handling with cookie and header management
- **Multiple Output Formats**: Export data to JSON, CSV, and TXT formats
- **Configurable**: Easy configuration through centralized config files
- **Error Handling**: Robust error handling and retry mechanisms
- **Logging**: Comprehensive logging system
- **Headless Mode**: Support for headless browser operation
- **Undetected Chrome**: Built-in support for undetected-chromedriver

## Project Structure

```
simple-selenium-scraper/
├── config.py              # Configuration settings and constants
├── browser_manager.py     # Browser initialization and management
├── scraper_base.py        # Base scraper classes and common functionality
├── site_scrapers.py       # Site-specific scrapers
├── session_manager.py     # Session and cookie management
├── utils.py              # Utility functions and helpers
├── scraper_app.py        # Main application interface
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── output/              # Output directory for scraped data
├── data/                # Data directory for session files
├── logs/                # Log files directory
└── chrome_profile/      # Chrome profile directory
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd simple-selenium-scraper
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Chrome WebDriver**:
   - Download ChromeDriver from [https://chromedriver.chromium.org/](https://chromedriver.chromium.org/)
   - Make sure it's in your system PATH or in the project directory

## Configuration

### Browser Configuration

Edit `config.py` to customize browser settings:

```python
BROWSER_CONFIG = {
    "user_data_dir": r"C:\Users\YourUsername\AppData\Local\Google\Chrome\User Data",
    "profile_dir": "Profile 1",
    "chrome_profile_path": "chrome_profile",
    "chrome_profile_name": "Profile 1",
    "wait_timeout": 10,
    "page_load_timeout": 30,
    "implicit_wait": 10
}
```

### XPath Templates

Add or modify XPath templates for different websites in `config.py`:

```python
XPATH_TEMPLATES = {
    "your_site": {
        "container": "//div[@class='items-container']",
        "item_loop": "//div[@class='item'][{loop}]"
    }
}
```

## Usage

### Command Line Interface

The scraper provides a comprehensive CLI with multiple commands:

#### 1. Generic Website Scraping

```bash
# Scrape any website with generic scraper
python scraper_app.py scrape --site-type generic --url "https://example.com"

# Scrape with specific site type
python scraper_app.py scrape --site-type shopee --url "https://shopee.co.id/search_user?keyword=fashion&page={page}" --max-pages 5

# Export to specific formats
python scraper_app.py scrape --site-type bumn --url "https://www.bumn.go.id/portofolio/brand?page={page}" --output json csv
```

#### 2. Shopee Store Scraping

```bash
# Scrape Shopee stores by keyword
python scraper_app.py shopee --keyword "fashion" --max-pages 10

# Export to multiple formats
python scraper_app.py shopee --keyword "electronics" --max-pages 5 --output json csv txt
```

#### 3. BUMN Brand Scraping

```bash
# Scrape BUMN brands
python scraper_app.py bumn --max-pages 8

# Export to specific format
python scraper_app.py bumn --max-pages 5 --output csv
```

#### 4. Link Extraction

```bash
# Extract all links from a webpage
python scraper_app.py links --url "https://example.com"

# Save links to specific file
python scraper_app.py links --url "https://example.com" --output-file "extracted_links.txt"
```

#### 5. TrendMicro Operations

```bash
# Get device list by CVE ID
python scraper_app.py trendmicro --cve-id "CVE-2023-36025" --limit 50

# With custom parameters
python scraper_app.py trendmicro --cve-id "CVE-2023-36025" --offset 0 --limit 100 --period 30 --status new
```

#### 6. Session Management

```bash
# Save current browser session
python scraper_app.py session --action save

# Load saved session
python scraper_app.py session --action load
```

#### 7. Headless Mode

```bash
# Run in headless mode (no browser window)
python scraper_app.py --headless shopee --keyword "fashion"
```

### Programmatic Usage

You can also use the scraper programmatically:

```python
from scraper_app import ScraperApp

# Initialize the application
app = ScraperApp(headless=False, use_undetected=True)

# Scrape Shopee stores
shopee_data = app.scrape_shopee_stores(
    keyword="fashion",
    max_pages=5,
    output_formats=['json', 'csv']
)

# Scrape BUMN brands
bumn_data = app.scrape_bumn_brands(
    max_pages=8,
    output_formats=['csv']
)

# Extract links
links = app.extract_links_from_url(
    url="https://example.com",
    output_file="links.txt"
)

# Get TrendMicro device list
device_data = app.get_trendmicro_device_list(
    cve_id="CVE-2023-36025",
    limit=50
)

# Close the application
app.close()
```

## Creating Custom Scrapers

### 1. Extend BaseScraper

Create a new scraper by extending the `BaseScraper` class:

```python
from scraper_base import BaseScraper
from selenium.webdriver.remote.webelement import WebElement
from typing import Dict, Any

class MyCustomScraper(BaseScraper):
    def __init__(self, browser_manager):
        super().__init__(browser_manager, 'my_site')
    
    def extract_item_data(self, element: WebElement, index: int) -> Dict[str, Any]:
        """Extract data from a single item element."""
        try:
            data = {
                'index': index,
                'title': element.text.strip(),
                'link': element.get_attribute('href')
            }
            return data
        except Exception as e:
            print(f"[ERROR] Failed to extract data: {e}")
            return None
```

### 2. Add XPath Templates

Add your site's XPath templates to `config.py`:

```python
XPATH_TEMPLATES = {
    "my_site": {
        "container": "//div[@class='items-container']",
        "item_loop": "//div[@class='item'][{loop}]/a"
    }
}
```

### 3. Register the Scraper

Add your scraper to the factory function in `site_scrapers.py`:

```python
def create_scraper(site_type: str, browser_manager):
    scrapers = {
        'shopee': ShopeeScraper,
        'bumn': BUMNScraper,
        'kementrian': KementrianScraper,
        'trendmicro': TrendMicroScraper,
        'my_site': MyCustomScraper,  # Add your scraper here
        'generic': BaseScraper
    }
    # ... rest of the function
```

## Output Formats

The scraper supports multiple output formats:

### JSON Format
```json
[
  {
    "index": 1,
    "store_name": "Fashion Store",
    "store_link": "https://shopee.co.id/store/123",
    "total_products": "150",
    "rating": "4.8",
    "chat_response_rate": "95%"
  }
]
```

### CSV Format
```csv
index,store_name,store_link,total_products,rating,chat_response_rate
1,Fashion Store,https://shopee.co.id/store/123,150,4.8,95%
```

### TXT Format
```
index: 1
store_name: Fashion Store
store_link: https://shopee.co.id/store/123
total_products: 150
rating: 4.8
chat_response_rate: 95%
--------------------------------------------------
```

## Error Handling

The scraper includes comprehensive error handling:

- **Retry Mechanism**: Automatic retry with exponential backoff
- **Timeout Handling**: Configurable timeouts for different operations
- **Graceful Degradation**: Continues operation even if some items fail
- **Detailed Logging**: Comprehensive logging for debugging

## Logging

Logs are saved to the `logs/` directory with the following levels:
- **INFO**: General information about operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors that may affect operation

## Session Management

The scraper can save and restore browser sessions:

- **Cookies**: Automatically saved and restored
- **Headers**: User-Agent and other headers preserved
- **Authentication**: Login sessions maintained between runs

## Performance Tips

1. **Use Headless Mode**: For production runs, use `--headless` flag
2. **Limit Pages**: Set reasonable `--max-pages` to avoid overwhelming servers
3. **Add Delays**: Configure appropriate delays between requests
4. **Use Undetected Chrome**: Helps avoid detection by websites

## Troubleshooting

### Common Issues

1. **ChromeDriver Not Found**:
   - Download ChromeDriver and add to PATH
   - Or place in project directory

2. **Permission Errors**:
   - Run with appropriate permissions
   - Check Chrome profile directory permissions

3. **Timeout Errors**:
   - Increase timeout values in `config.py`
   - Check internet connection

4. **Element Not Found**:
   - Verify XPath templates are correct
   - Check if website structure has changed

### Debug Mode

Enable debug logging by modifying `config.py`:

```python
LOGGING_CONFIG = {
    "level": "DEBUG",  # Change from "INFO" to "DEBUG"
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "scraper.log"
}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in the `logs/` directory
3. Create an issue with detailed information about the problem

## Changelog

### Version 2.0.0
- Complete modular rewrite
- Added support for multiple websites
- Improved error handling and logging
- Added session management
- Multiple output format support
- Command-line interface
- Configuration system

### Version 1.0.0
- Initial release with basic scraping functionality 