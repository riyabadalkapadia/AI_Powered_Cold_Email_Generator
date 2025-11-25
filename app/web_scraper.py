import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time

class WebScraper:
    @staticmethod
    def get_content_static(url):
        """Try simple request first"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            return response.text
        except requests.RequestException as e:
            print(f"Failed to get content: {str(e)}")
            return None

    @staticmethod
    def get_content_selenium(url):
        """Use Selenium for JavaScript-heavy pages"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(url)
            time.sleep(5)  # Wait for dynamic content
            return driver.page_source
        finally:
            driver.quit()

    @staticmethod
    def extract_content(html_content):
        """Extract meaningful content from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Try to find job-related content
        content = ""
        
        # Look for common job posting containers
        job_containers = soup.find_all(['div', 'section'], class_=lambda x: x and any(term in str(x).lower() for term in ['job', 'position', 'career', 'description', 'requirements', 'qualifications']))
        
        if job_containers:
            for container in job_containers:
                content += container.get_text(strip=True, separator='\n') + "\n"
        else:
            # If no job-specific containers found, get main content
            main_content = soup.find(['main', 'article']) or soup.find('div', {'role': 'main'})
            if main_content:
                content = main_content.get_text(strip=True, separator='\n')
            else:
                # Fallback to body content
                content = soup.body.get_text(strip=True, separator='\n')

        return content

    @staticmethod
    def scrape_url(url):
        """Main method to scrape content using multiple strategies"""
        # Try simple request first
        content = WebScraper.get_content_static(url)
        
        # If no content or content seems incomplete, try Selenium
        if not content or len(content) < 1000:  # Arbitrary threshold
            content = WebScraper.get_content_selenium(url)
        
        if not content:
            raise ValueError("Could not fetch page content")

        # Try to parse as JSON first
        try:
            json_data = json.loads(content)
            # If it's JSON, convert it to string representation
            return json.dumps(json_data, indent=2)
        except json.JSONDecodeError:
            # If not JSON, extract meaningful content from HTML
            return WebScraper.extract_content(content)