import requests
from bs4 import BeautifulSoup
import csv
import sys
import os
import time
import re
from urllib.parse import quote

def get_with_retry(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(2)
    return None

def scrape_handshake_jobs(job_title, location):
    all_jobs = []
    keywords = quote(job_title)
    location_encoded = quote(location)
    
    # Handshake job search URL structure
    url = f"https://app.joinhandshake.com/stu/jobs/search?query={keywords}&location={location_encoded}"
    
    print(f"Scraping Handshake jobs from: {url}")
    soup = get_with_retry(url)
    
    if soup:
        jobs = parse_handshake_jobs(soup)
        all_jobs.extend(jobs)
        print(f"Found {len(jobs)} jobs on Handshake")
    
    return remove_duplicates(all_jobs)

def parse_handshake_jobs(soup):
    jobs = []
    
    # Try multiple selectors for Handshake job cards
    job_cards = (soup.find_all('div', class_='job-card') or
                soup.find_all('div', class_='job-listing') or
                soup.find_all('article', class_='job') or
                soup.find_all('div', {'data-testid': 'job-card'}))
    
    for card in job_cards:
        try:
            # Extract job title
            title_elem = (card.find('h3') or
                         card.find('h2') or
                         card.find('a', class_='job-title') or
                         card.find('div', class_='title'))
            
            # Extract company name
            company_elem = (card.find('div', class_='company') or
                           card.find('span', class_='employer') or
                           card.find('p', class_='company-name'))
            
            # Extract location
            location_elem = (card.find('div', class_='location') or
                            card.find('span', class_='job-location') or
                            card.find('p', class_='location'))
            
            # Extract job link
            link_elem = (card.find('a') or
                        card.find('a', class_='job-link'))
            
            if title_elem and company_elem:
                job = {
                    'title': title_elem.text.strip(),
                    'company': company_elem.text.strip(),
                    'location': location_elem.text.strip() if location_elem else '',
                    'link': link_elem.get('href') if link_elem else ''
                }
                jobs.append(job)
                
        except Exception as e:
            continue
    
    return jobs

def remove_duplicates(jobs):
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job['title'], job['company'])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    return unique_jobs

def save_to_csv(jobs, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'company', 'location', 'link'])
        writer.writeheader()
        writer.writerows(jobs)

def validate_location(location):
    pattern = r'^.+,\s[A-Z]{2}$'
    return bool(re.match(pattern, location))

def main(job_title, location):
    start_time = time.perf_counter()
    
    jobs = scrape_handshake_jobs(job_title, location)
    
    if jobs:
        os.makedirs("temp", exist_ok=True)
        filename = f"{job_title.replace(' ', '_').lower()}_jobs_Handshake.csv"
        filepath = os.path.join("temp", filename)
        save_to_csv(jobs, filepath)
        
        print(f"\nFound {len(jobs)} jobs saved to {filepath}:")
        for job in jobs:
            print(f"{job['title']} at {job['company']} ({job['location']})")
    else:
        print("No jobs found on Handshake")
    
    end_time = time.perf_counter()
    print(f"Scraping finished in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        job_title = sys.argv[1]
        location = sys.argv[2]
        main(job_title, location)
    else:
        job_title = input("Job Title, Keywords, or Company: ")
        
        while True:
            location = input("Location (City, State ABV): ")
            if validate_location(location):
                break
            print("Improper format. Please use format: City, ST (e.g., Birmingham, AL)")
        
        main(job_title, location)