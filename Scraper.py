import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import urllib.parse

def scrape_indeed(keyword, city, max_results=10):
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    base_url = "https://www.indeed.com/jobs"

    query = {
        "q": keyword,
        "l": city,
        "limit": max_results
    }
    url = f"{base_url}?{urllib.parse.urlencode(query)}"

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    jobs = []

    for card in soup.select(".resultContent"):
        title_tag = card.select_one("h2.jobTitle span")
        company_tag = card.select_one(".companyName")
        location_tag = card.select_one(".companyLocation")
        link_tag = card.find_parent("a", href=True)

        if title_tag and link_tag:
            job = {
                "title": title_tag.text.strip(),
                "company": company_tag.text.strip() if company_tag else "Unknown",
                "location": location_tag.text.strip() if location_tag else "Unknown",
                "link": "https://www.indeed.com" + link_tag['href']
            }
            jobs.append(job)

    return jobs

if __name__ == "__main__":
    keyword = input("Enter job keyword: ")
    city = input("Enter city: ")
    results = scrape_indeed(keyword, city)

    for job in results:
        print(f"{job['title']} at {job['company']} ({job['location']})")
        print(f"Apply: {job['link']}\n")
