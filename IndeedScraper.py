from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import time
import re
import tempfile
import os
import sys

def scrape_indeed_with_playwright(job_title, job_location):
    max_attempts = 10
    
    for attempt in range(max_attempts):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.set_default_timeout(60000)
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                })
                
                url = f"https://www.indeed.com/jobs?q={job_title}&l={job_location}"
                print(f"Attempt {attempt + 1}: Navigating to {url}")
                
                start_time = time.time()
                page.goto(url, wait_until="networkidle", timeout=15000)
                response_time = time.time() - start_time
                print(f"Response time: {response_time:.2f} seconds")
                time.sleep(3)
                
                html = page.content()
                browser.close()
                
                with open('playwright_debug.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                print("HTML saved to playwright_debug.html")
                
                return parse_jobs(html)
                
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                print(f"Retrying in 2 seconds...")
                time.sleep(2)
            else:
                print("All attempts failed")
    
    return []

def parse_jobs(html):
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    # Try multiple selectors
    cards = (soup.select('[data-testid="job-result"]') or
             soup.select('.resultContent') or 
             soup.select('.job_seen_beacon') or
             soup.select('[data-jk]'))
    
    print(f"Found {len(cards)} job cards")
    
    for card in cards:
        # Extract job data
        title_elem = (card.select_one('[data-testid="job-title"] span') or
                     card.select_one('h2 span[title]') or
                     card.select_one('.jobTitle span'))
        title = title_elem.get('title') or title_elem.text.strip() if title_elem else ""
        
        company_elem = (card.select_one('[data-testid="company-name"]') or
                       card.select_one('.companyName'))
        company = company_elem.text.strip() if company_elem else ""
        
        location_elem = (card.select_one('[data-testid="job-location"]') or
                        card.select_one('.companyLocation'))
        location = location_elem.text.strip() if location_elem else ""
        
        link_elem = (card.select_one('[data-testid="job-title"] a') or
                    card.select_one('h2 a'))
        link = "https://www.indeed.com" + link_elem.get('href') if link_elem and link_elem.get('href') else ""
        
        if title and company:
            jobs.append({
                'title': title,
                'company': company, 
                'location': location,
                'link': link
            })
    
    return jobs

def save_to_csv(jobs, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'company', 'location', 'link'])
        writer.writeheader()
        writer.writerows(jobs)

def validate_location(location):
    # Check for "City, ST" format (city name, comma, space, 2-letter state)
    pattern = r'^.+,\s[A-Z]{2}$'
    return bool(re.match(pattern, location))

if __name__ == "__main__":
    if len(sys.argv) == 3:
        job_title = sys.argv[1]
        location = sys.argv[2]
    else:
        job_title = input("Job Title, Keywords, or Company: ")
        
        while True:
            location = input("Location (City, State ABV): ")
            if validate_location(location):
                break
            print("Improper format. Please use format: City, ST (e.g., Birmingham, AL)")
    
    os.makedirs("temp", exist_ok=True)
    jobs = scrape_indeed_with_playwright(job_title, location)
    
    if jobs:
        filename = f"{job_title.replace(' ', '_').lower()}_jobs_Indeed.csv"
        filepath = os.path.join("temp", filename)
        save_to_csv(jobs, filepath)
        print(f"\nFound {len(jobs)} jobs saved to {filepath}:")
        for job in jobs:
            print(f"{job['title']} at {job['company']} ({job['location']})")
    else:
        print("No jobs found")