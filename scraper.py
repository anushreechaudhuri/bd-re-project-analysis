#!/usr/bin/env python3
"""
Renewable Energy Projects Scraper for Bangladesh Government Website
Scrapes project data from https://www.renewableenergy.gov.bd/
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RenewableEnergyScraper:
    def __init__(self):
        self.base_url = "https://www.renewableenergy.gov.bd"
        self.table_pages = [
            "https://www.renewableenergy.gov.bd/index.php?id=1&i=1&pg=1",
            "https://www.renewableenergy.gov.bd/index.php?id=1&i=1&pg=2", 
            "https://www.renewableenergy.gov.bd/index.php?id=1&i=1&pg=3"
        ]
        self.driver = None
        self.projects_data = []
        
        # Define the expected table headers based on analysis
        self.table_headers = [
            'SL', 'Project Name', 'SID', 'Capacity', 'Location', 
            'RE Technology', 'Agency', 'Finance LMFD', 'Completion Date', 
            'Present Status', 'Details'
        ]
        
    def setup_driver(self):
        """Set up Chrome WebDriver with realistic browser settings"""
        chrome_options = Options()
        
        # Add realistic user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Add other realistic browser settings
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Optional: run headless (uncomment if you don't want to see the browser)
        # chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("Chrome WebDriver initialized successfully")
        
    def analyze_site_structure(self):
        """Analyze the HTML structure of the website to understand data layout"""
        logger.info("Analyzing site structure...")
        
        if not self.driver:
            self.setup_driver()
            
        # Visit the first page to analyze structure
        url = self.table_pages[0]
        logger.info(f"Analyzing structure of: {url}")
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Wait a bit for dynamic content to load
            time.sleep(3)
            
            # Get page source and analyze
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Look for tables
            tables = soup.find_all('table')
            logger.info(f"Found {len(tables)} table(s) on the page")
            
            # Analyze each table
            for i, table in enumerate(tables):
                logger.info(f"\n--- Table {i+1} Analysis ---")
                rows = table.find_all('tr')
                logger.info(f"Number of rows: {len(rows)}")
                
                if rows:
                    # Analyze header row
                    header_row = rows[0]
                    headers = header_row.find_all(['th', 'td'])
                    logger.info(f"Headers: {[h.get_text(strip=True) for h in headers]}")
                    
                    # Analyze first few data rows
                    for j, row in enumerate(rows[1:6]):  # First 5 data rows
                        cells = row.find_all(['td', 'th'])
                        logger.info(f"Row {j+1}: {[cell.get_text(strip=True) for cell in cells]}")
                        
                        # Look for links that might lead to detail pages
                        links = row.find_all('a')
                        for link in links:
                            href = link.get('href')
                            if href:
                                logger.info(f"  Found link: {href}")
            
            # Look for pagination or navigation elements
            pagination = soup.find_all(['div', 'nav'], class_=lambda x: x and ('page' in x.lower() or 'nav' in x.lower()))
            logger.info(f"Found {len(pagination)} potential pagination elements")
            
            # Save the HTML for manual inspection
            with open('page_structure.html', 'w', encoding='utf-8') as f:
                f.write(page_source)
            logger.info("Saved page HTML to 'page_structure.html' for manual inspection")
            
        except Exception as e:
            logger.error(f"Error analyzing site structure: {e}")
            
    def scrape_table_data(self):
        """Scrape data from all table pages"""
        logger.info("Starting to scrape table data...")
        
        if not self.driver:
            self.setup_driver()
            
        for page_url in self.table_pages:
            logger.info(f"Scraping page: {page_url}")
            
            try:
                self.driver.get(page_url)
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                
                # Wait for content to load
                time.sleep(random.uniform(2, 4))
                
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Find the main data table (skip the filter form table)
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    # Skip if no rows or too few rows (likely not the main table)
                    if len(rows) < 5:  # Need at least header + some data rows
                        continue
                    
                    # Check if this looks like the data table by looking for SID column
                    # The header row is actually row 2 (index 2), not row 0
                    header_row_index = None
                    for i, row in enumerate(rows):
                        cells = row.find_all(['th', 'td'])
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        if 'SID' in cell_texts and 'Project Name' in cell_texts:
                            header_row_index = i
                            logger.info(f"Found main data table with headers: {cell_texts}")
                            break
                    
                    if header_row_index is not None:
                        # Process each data row (skip header row and filter rows)
                        for row in rows[header_row_index + 1:]:
                            cells = row.find_all(['td', 'th'])
                            
                            if len(cells) >= 10:  # Should have at least 10 columns
                                # Extract text from each cell
                                row_data = [cell.get_text(strip=True) for cell in cells]
                                
                                # Look for project ID/SID in links
                                project_id = None
                                details_link = None
                                links = row.find_all('a')
                                for link in links:
                                    href = link.get('href')
                                    if href and 'kid=' in href:
                                        # Extract kid parameter
                                        try:
                                            project_id = href.split('kid=')[1].split('&')[0]
                                            details_link = href
                                            break
                                        except:
                                            continue
                                
                                if project_id and len(row_data) >= 10:
                                    # Map data to headers
                                    project_data = {
                                        'project_id': project_id,
                                        'details_link': details_link,
                                        'page_url': page_url,
                                        'sl_number': row_data[0] if len(row_data) > 0 else '',
                                        'project_name': row_data[1] if len(row_data) > 1 else '',
                                        'sid': row_data[2] if len(row_data) > 2 else '',
                                        'capacity': row_data[3] if len(row_data) > 3 else '',
                                        'location': row_data[4] if len(row_data) > 4 else '',
                                        're_technology': row_data[5] if len(row_data) > 5 else '',
                                        'agency': row_data[6] if len(row_data) > 6 else '',
                                        'finance_lmfd': row_data[7] if len(row_data) > 7 else '',
                                        'completion_date': row_data[8] if len(row_data) > 8 else '',
                                        'present_status': row_data[9] if len(row_data) > 9 else '',
                                        'raw_data': row_data
                                    }
                                    self.projects_data.append(project_data)
                                    logger.info(f"Found project: {project_data['project_name']} (ID: {project_id})")
                
                # Random delay between pages
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error scraping page {page_url}: {e}")
                
        logger.info(f"Scraped {len(self.projects_data)} projects from table pages")
        
    def scrape_project_details(self, project_id):
        """Scrape detailed information for a specific project"""
        detail_url = f"{self.base_url}/index.php?id=06&kid={project_id}"
        
        try:
            self.driver.get(detail_url)
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            time.sleep(random.uniform(1, 2))
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract detailed information
            details = {}
            
            # Look for tables with project details
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        # Look for key-value pairs in format: Key : Value
                        key_cell = cells[0].get_text(strip=True)
                        if len(cells) >= 3 and cells[1].get_text(strip=True) == ':':
                            value_cell = cells[2].get_text(strip=True)
                            if key_cell and value_cell and key_cell != 'Item Name':
                                # Clean the key name
                                clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key_cell)
                                details[clean_key] = value_cell
                    
                    # Also look for cells with colons in the text
                    if len(cells) == 1:
                        text = cells[0].get_text(strip=True)
                        if ':' in text and len(text.split(':')) == 2:
                            key, value = text.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if key and value and key != 'Item Name':
                                clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
                                details[clean_key] = value
            
            return details
            
        except Exception as e:
            logger.error(f"Error scraping details for project {project_id}: {e}")
            return {}
            
    def scrape_all_details(self):
        """Scrape detailed information for all projects"""
        logger.info("Starting to scrape project details...")
        
        for i, project in enumerate(self.projects_data):
            project_id = project['project_id']
            logger.info(f"Scraping details for project {i+1}/{len(self.projects_data)}: {project_id}")
            
            details = self.scrape_project_details(project_id)
            project['details'] = details
            
            # Random delay between requests
            time.sleep(random.uniform(1, 3))
            
    def save_to_csv(self, filename='renewable_energy_projects.csv'):
        """Save all scraped data to CSV"""
        logger.info("Saving data to CSV...")
        
        # Flatten the data for CSV
        csv_data = []
        
        for project in self.projects_data:
            row = {
                'project_id': project['project_id'],
                'sl_number': project['sl_number'],
                'project_name': project['project_name'],
                'sid': project['sid'],
                'capacity': project['capacity'],
                'location': project['location'],
                're_technology': project['re_technology'],
                'agency': project['agency'],
                'finance_lmfd': project['finance_lmfd'],
                'completion_date': project['completion_date'],
                'present_status': project['present_status'],
                'details_link': project['details_link'],
                'page_url': project['page_url']
            }
            
            # Add detailed information if available
            if 'details' in project:
                for key, value in project['details'].items():
                    # Clean key name for CSV column
                    clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', key)
                    row[f'detail_{clean_key}'] = value
                    
            csv_data.append(row)
            
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        df.to_csv(filename, index=False, encoding='utf-8')
        logger.info(f"Data saved to {filename}")
        logger.info(f"Total projects: {len(csv_data)}")
        logger.info(f"Columns: {list(df.columns)}")
        
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")

def main():
    """Main function to run the scraper"""
    scraper = RenewableEnergyScraper()
    
    try:
        # Step 1: Scrape table data from all pages
        scraper.scrape_table_data()
        
        if not scraper.projects_data:
            logger.error("No projects found! Check the website structure.")
            return
        
        # Step 2: Scrape project details (optional - can be disabled for faster testing)
        logger.info("Starting to scrape project details...")
        scraper.scrape_all_details()
        
        # Step 3: Save to CSV
        scraper.save_to_csv()
        
        logger.info("Scraping completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
    finally:
        scraper.close_driver()

if __name__ == "__main__":
    main()
