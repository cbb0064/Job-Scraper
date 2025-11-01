import subprocess
import os
import time
import re
import pandas as pd
from datetime import datetime

# Configuration
NUM_CSV_FILES = 2  # Wait for Indeed and LinkedIn CSVs

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

def convert_csvs_to_excel(csv_paths, job_title, location, preference):
    os.makedirs("Job Searches", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{job_title.replace(' ', '_')}_{location.replace(', ', '_').replace(' ', '_')}_{timestamp}.xlsx"
    filepath = os.path.join("Job Searches", filename)
    
    # Load and process CSVs
    dfs = {}
    for csv_path in csv_paths:
        df = pd.read_csv(csv_path)
        # Remove duplicates within each CSV
        df = df.drop_duplicates(subset=['title', 'company'])
        
        if 'Indeed' in csv_path:
            dfs['Indeed'] = df
        elif 'LinkedIn' in csv_path:
            dfs['LinkedIn'] = df
    
    # Remove cross-duplicates based on preference
    if len(dfs) == 2:
        preferred = preference.capitalize()
        other = 'LinkedIn' if preferred == 'Indeed' else 'Indeed'
        
        if preferred in dfs and other in dfs:
            # Create combined key for comparison
            preferred_keys = set(zip(dfs[preferred]['title'], dfs[preferred]['company']))
            
            # Remove duplicates from non-preferred source
            mask = ~dfs[other].apply(lambda row: (row['title'], row['company']) in preferred_keys, axis=1)
            dfs[other] = dfs[other][mask]
    
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        for source, df in dfs.items():
            df.to_excel(writer, sheet_name=source, index=False)
            
            # Format link columns as hyperlinks
            worksheet = writer.sheets[source]
            link_col = None
            for col_idx, col_name in enumerate(df.columns, 1):
                if col_name in ['link', 'job_url']:
                    link_col = col_idx
                    break
            
            if link_col:
                from openpyxl.styles import Font
                from openpyxl.utils import get_column_letter
                
                col_letter = get_column_letter(link_col)
                for row_idx in range(2, len(df) + 2):
                    cell = worksheet[f'{col_letter}{row_idx}']
                    if cell.value and cell.value.startswith('http'):
                        cell.hyperlink = cell.value
                        cell.font = Font(color="0000FF", underline="single")
    
    print(f"Excel file created: {filepath}")
    return filepath

def main():
    job_title = input("Job Title, Keywords, or Company: ")
    
    while True:
        location = input("Location (City, State ABV): ")
        if validate_location(location):
            break
        print("Improper format. Please use format: City, ST (e.g., Birmingham, AL)")
    
    while True:
        preference = input("Which source do you prefer? (indeed/linkedin): ").lower()
        if preference in ['indeed', 'linkedin']:
            break
        print("Please enter 'indeed' or 'linkedin'")
    
    os.makedirs("temp", exist_ok=True)
    
    print("Starting Indeed scraper...")
    indeed_process = subprocess.Popen(
        ["python", "IndeedScraper.py", job_title, location]
    )
    
    print("Starting LinkedIn scraper...")
    linkedin_process = subprocess.Popen(
        ["python", "LinkedinScraper.py", job_title, location]
    )
    
    # Wait for all processes to complete
    indeed_process.wait()
    linkedin_process.wait()
    
    print("All scrapers completed")
    
    csv_paths = wait_for_csvs()
    if csv_paths:
        print(f"Found {len(csv_paths)} CSV files:")
        for path in csv_paths:
            print(f"  - {path}")
        
        excel_path = convert_csvs_to_excel(csv_paths, job_title, location, preference)
        print(f"All CSV files converted to Excel: {excel_path}")
        
        # Clear CSV files from temp directory
        for csv_path in csv_paths:
            os.remove(csv_path)
        print("Temporary CSV files cleared")
    else:
        print("No CSV files found")

if __name__ == "__main__":
    main()