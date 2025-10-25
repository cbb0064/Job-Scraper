import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import sys
import os
import time as tm
from datetime import datetime, time, timedelta
from urllib.parse import quote
from langdetect import detect

def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)

def safe_detect(text):
    try:
        return detect(text)
    except:
        return 'unknown'

def get_with_retry(url, config):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for attempt in range(config.get('max_retries', 3)):
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < config.get('max_retries', 3) - 1:
                tm.sleep(2)
    return None

def transform(soup):
    jobs = []
    if soup:
        job_cards = soup.find_all('div', class_='base-card')
        for card in job_cards:
            try:
                title = card.find('h3', class_='base-search-card__title')
                company = card.find('h4', class_='base-search-card__subtitle')
                location = card.find('span', class_='job-search-card__location')
                date = card.find('time', class_='job-search-card__listdate')
                link = card.find('a', class_='base-card__full-link')
                
                job = {
                    'title': title.text.strip() if title else '',
                    'company': company.text.strip() if company else '',
                    'location': location.text.strip() if location else '',
                    'date': date.text.strip() if date else '',
                    'job_url': link.get('href') if link else ''
                }
                jobs.append(job)
            except Exception as e:
                continue
    return jobs

def transform_job(soup):
    if soup:
        desc = soup.find('div', class_='show-more-less-html__markup')
        return desc.text.strip() if desc else ''
    return ''

def convert_date_format(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return datetime.now().date()

def remove_duplicates(jobs, config):
    seen = set()
    unique_jobs = []
    for job in jobs:
        key = (job['title'], job['company'], job['date'])
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)
    return unique_jobs

def remove_irrelevant_jobs(jobs, config):
    filtered_jobs = []
    exclude_keywords = config.get('exclude_keywords', [])
    
    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('job_description', '')}".lower()
        if not any(keyword.lower() in job_text for keyword in exclude_keywords):
            filtered_jobs.append(job)
    
    return filtered_jobs

def get_jobcards(config):
    all_jobs = []
    for k in range(0, config['rounds']):
        for query in config['search_queries']:
            keywords = quote(query['keywords'])
            location = quote(query['location'])
            for i in range(0, config['pages_to_scrape']):
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords}&location={location}&f_TPR=&f_WT={query['f_WT']}&geoId=&f_TPR={config['timespan']}&start={25*i}"
                soup = get_with_retry(url, config)
                jobs = transform(soup)
                all_jobs = all_jobs + jobs
                print("Finished scraping page: ", url)
    
    print("Total job cards scraped: ", len(all_jobs))
    all_jobs = remove_duplicates(all_jobs, config)
    print("Total job cards after removing duplicates: ", len(all_jobs))
    all_jobs = remove_irrelevant_jobs(all_jobs, config)
    print("Total job cards after removing irrelevant jobs: ", len(all_jobs))
    return all_jobs

def main(config_file):
    start_time = tm.perf_counter()
    job_list = []

    config = load_config(config_file)
    all_jobs = get_jobcards(config)

    if len(all_jobs) > 0:
        for job in all_jobs:
            job_date = convert_date_format(job['date'])
            job_date = datetime.combine(job_date, time())
            
            if job_date < datetime.now() - timedelta(days=config['days_to_scrape']):
                continue
                
            print('Found job: ', job['title'], 'at ', job['company'], job['job_url'])
            desc_soup = get_with_retry(job['job_url'], config)
            job['job_description'] = transform_job(desc_soup)
            
            language = safe_detect(job['job_description'])
            if language not in config['languages']:
                print('Job description language not supported: ', language)
                continue
                
            job_list.append(job)

        jobs_to_add = remove_irrelevant_jobs(job_list, config)
        print("Total jobs to add: ", len(jobs_to_add))
        
        df = pd.DataFrame(jobs_to_add)
        df['date_loaded'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract job title from first search query for filename
        job_title = config['search_queries'][0]['keywords'] if config['search_queries'] else "jobs"
        filename = f"{job_title.replace(' ', '_').lower()}_jobs_LinkedIn.csv"
        filepath = os.path.join(temp_dir, filename)
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"Saved {len(jobs_to_add)} jobs to {filepath}")
    else:
        print("No jobs found")
    
    end_time = tm.perf_counter()
    print(f"Scraping finished in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    config_file = 'config.json'
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
        
    main(config_file)