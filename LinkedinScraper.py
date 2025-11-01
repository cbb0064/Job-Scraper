import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
import os
import time as tm
from datetime import datetime
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
                tm.sleep(2)
    return None

def transform(soup):
    jobs = []
    if soup:
        # Try multiple selectors for job cards
        job_cards = (soup.find_all('div', class_='base-card') or 
                    soup.find_all('div', class_='job-search-card') or
                    soup.find_all('li', class_='result-card'))
        
        for card in job_cards:
            try:
                # Try multiple selectors for title
                title = (card.find('h3', class_='base-search-card__title') or
                        card.find('h3', class_='result-card__title') or
                        card.find('a', class_='result-card__full-card-link'))
                
                # Try multiple selectors for company
                company = (card.find('h4', class_='base-search-card__subtitle') or
                          card.find('h4', class_='result-card__subtitle'))
                

                
                # Try multiple selectors for link
                link = (card.find('a', class_='base-card__full-link') or
                       card.find('a', class_='result-card__full-card-link'))
                
                if title and company:
                    job = {
                        'title': title.text.strip() if title else '',
                        'company': company.text.strip() if company else '',
                        'job_url': link.get('href') if link else ''
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

def get_jobcards(job_title, location):
    all_jobs = []
    keywords = quote(job_title)
    location_encoded = quote(location)
    
    for i in range(0, 3):  # Scrape 3 pages
        url = f"https://www.linkedin.com/jobs/search?keywords={keywords}&location={location_encoded}&start={25*i}"
        soup = get_with_retry(url)
        jobs = transform(soup)
        all_jobs = all_jobs + jobs
        print("Finished scraping page: ", url)
    
    print("Total job cards scraped: ", len(all_jobs))
    all_jobs = remove_duplicates(all_jobs)
    print("Total job cards after removing duplicates: ", len(all_jobs))
    return all_jobs

def main(job_title, location):
    start_time = tm.perf_counter()
    
    all_jobs = get_jobcards(job_title, location)

    if len(all_jobs) > 0:
        job_list = []
        for job in all_jobs[:20]:  # Limit to 20 jobs for faster processing
            print('Found job: ', job['title'], 'at ', job['company'])
            job_list.append({
                'title': job['title'],
                'company': job['company'],
                'link': job['job_url']
            })

        print("Total jobs to add: ", len(job_list))
        
        df = pd.DataFrame(job_list)
        
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        filename = f"{job_title.replace(' ', '_').lower()}_jobs_LinkedIn.csv"
        filepath = os.path.join(temp_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Saved {len(job_list)} jobs to {filepath}")
    else:
        print("No jobs found")
    
    end_time = tm.perf_counter()
    print(f"Scraping finished in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        job_title = sys.argv[1]
        location = sys.argv[2]
        main(job_title, location)
    else:
        job_title = input("Job Title, Keywords, or Company: ")
        location = input("Location (City, State ABV): ")
        main(job_title, location)