import logging
import time

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def scrape_internshala_jobs(max_pages=5):
	logger.info("Starting Internshala jobs scraper")
	headers = {
		"User-Agent": (
			"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
			"AppleWebKit/537.36 (KHTML, like Gecko) "
			"Chrome/124.0.0.0 Safari/537.36"
		)
	}

	all_jobs = []
	seen_urls = set()

	for page in range(1, max_pages + 1):
		# Page 1 uses /jobs/, page 2+ use /jobs/page-2, /jobs/page-3, etc.
		if page == 1:
			url = "https://internshala.com/jobs/"
		else:
			url = f"https://internshala.com/jobs/page-{page}/"

		logger.info(f"Fetching page {page}: {url}")

		try:
			response = requests.get(url, headers=headers, timeout=10)
			if response.status_code != 200:
				logger.warning(
					f"Page {page} returned status {response.status_code}, skipping"
				)
				continue

			soup = BeautifulSoup(response.text, "html.parser")
			page_jobs = []

			for card in soup.find_all("div", class_="internship_meta"):
				try:
					title_link = card.find("a", class_="job-title-href")
					company_tag = card.find("p", class_="company-name")
					location_link = card.find("p", class_="locations")
					description_tag = card.find("div", class_="about_job")
					skill_tags = card.find_all("div", class_="job_skill")

					job = {
						"title": title_link.get_text(strip=True) if title_link else "",
						"url": (
							f"https://internshala.com{title_link.get('href')}"
							if title_link and title_link.get("href")
							else ""
						),
						"company": company_tag.get_text(strip=True) if company_tag else "",
						"location": (
							location_link.find("a").get_text(strip=True)
							if location_link and location_link.find("a")
							else ""
						),
						"description": (
							description_tag.get_text(strip=True)
							if description_tag
							else ""
						),
						"skills": [
							skill.get_text(strip=True) for skill in skill_tags
						],
					}

					# Deduplicate by URL
					if job["url"] and job["url"] not in seen_urls:
						all_jobs.append(job)
						seen_urls.add(job["url"])
						page_jobs.append(job)

				except Exception as e:
					logger.warning(f"Error parsing job card: {e}")
					continue

			logger.info(f"Page {page}: Found {len(page_jobs)} new jobs")

			# Rate limiting: wait 1 second before next page request
			if page < max_pages:
				time.sleep(1)

		except requests.RequestException as e:
			logger.error(f"Request error on page {page}: {e}")
			continue

	logger.info(f"Scrape complete. Total jobs found: {len(all_jobs)}")
	return all_jobs


if __name__ == "__main__":
	jobs = scrape_internshala_jobs(max_pages=2)
	print(f"\nFound {len(jobs)} jobs total")
	if jobs:
		print("First job:")
		print(jobs[0])
	else:
		print("No jobs found")