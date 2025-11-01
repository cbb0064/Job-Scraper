# Scraper Application

A Python web scraping utility for extracting data from websites.

## Features

- Web page scraping using playwright and saves as a csv
- Implements 3 different python files to simulate multithreaded support
- Executes on a batch file
- Merges the results from both csvs to a single excel

## Requirements

- Python 3.12 or later
- After running pip install you will also need to run "playwright install" to get headless browser
- Go into run.bat and change the file paths to where you save the python scripts if you want to run this outside of just the local directory or on a job

## Installation
run pip install -r requirements.txt in terminal to install the modules

## Usage

Locate the directory where you have your run.bat file saved and execute the file.

## Notes

The indeed scraper may need multiple attempts. Fake agent simulates a request but indeed rejects it sometimes. Pagination also is slow so let this run for a minute.
Adjust number of attempts as needed for your network speed.
