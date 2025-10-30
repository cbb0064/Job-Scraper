import subprocess
import os
import time
import re
import pandas as pd
from datetime import datetime

# Configuration
NUM_CSV_FILES = 3  # Wait for Indeed, LinkedIn, and Handshake CSVs

def validate_location(location):
    pattern = r'^.+,\s[A-Z]{2}$'
    return bool(re.match(pattern, location))

def wait_for_csvs(timeout=300):
    found_files = []
    start_time = time.time()
    
    while time.time() - start_time < timeout and len(found_files) < NUM_CSV_FILES:
        temp_files = [f for f in os.listdir("temp") if f.endswith(".csv")]
        
        for file in temp_files:
            filepath = os.path.join("temp", file)
            if filepath not in found_files:
                found_files.append(filepath)
                print(f"CSV file found: {filepath} ({len(found_files)}/{NUM_CSV_FILES})")
        
        if len(found_files) < NUM_CSV_FILES:
            time.sleep(1)
    
    if len(found_files) == NUM_CSV_FILES:
        print(f"All {NUM_CSV_FILES} CSV files found!")
        return found_files
    else:
        print(f"Timeout: Only found {len(found_files)}/{NUM_CSV_FILES} CSV files after {timeout} seconds")
        return found_files

def convert_csvs_to_excel(csv_paths, job_title, location):
    os.makedirs("Job Searches", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{job_title.replace(' ', '_')}_{location.replace(', ', '_').replace(' ', '_')}_{timestamp}.xlsx"
    filepath = os.path.join("Job Searches", filename)
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for i, csv_path in enumerate(csv_paths):
            df = pd.read_csv(csv_path)
            sheet_name = f"Sheet{i+1}"
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"Excel file created: {filepath}")
    return filepath

def main():
    job_title = input("Job Title, Keywords, or Company: ")
    
    while True:
        location = input("Location (City, State ABV): ")
        if validate_location(location):
            break
        print("Improper format. Please use format: City, ST (e.g., Birmingham, AL)")
    
    os.makedirs("temp", exist_ok=True)
    
    print("Starting Indeed scraper...")
    indeed_process = subprocess.Popen(
        ["python", "indeedScraper.py", job_title, location],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Starting LinkedIn scraper...")
    linkedin_process = subprocess.Popen(
        ["python", "LinkedinScraper.py", job_title, location],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("Starting Handshake scraper...")
    handshake_process = subprocess.Popen(
        ["python", "HandshakeScraper.py", job_title, location],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for all processes to complete
    indeed_stdout, indeed_stderr = indeed_process.communicate()
    linkedin_stdout, linkedin_stderr = linkedin_process.communicate()
    handshake_stdout, handshake_stderr = handshake_process.communicate()
    
    print("All scrapers completed")
    
    csv_paths = wait_for_csvs()
    if csv_paths:
        print(f"Found {len(csv_paths)} CSV files:")
        for path in csv_paths:
            print(f"  - {path}")
        
        excel_path = convert_csvs_to_excel(csv_paths, job_title, location)
        print(f"All CSV files converted to Excel: {excel_path}")
        
        # Clear CSV files from temp directory
        for csv_path in csv_paths:
            os.remove(csv_path)
        print("Temporary CSV files cleared")
    else:
        print("No CSV files found")

if __name__ == "__main__":
    main()