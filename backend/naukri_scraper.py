#!/usr/bin/env python3
"""
Naukri.com scraper to extract job titles and corresponding skills
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin, quote
import json
from db import init_db, add_career_skills, clear_career_skills, get_career_count

class NaukriScraper:
    def __init__(self):
        self.base_url = "https://www.naukri.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def search_jobs(self, keyword, location="", max_pages=5):
        """Search for jobs on Naukri.com"""
        jobs = []
        
        for page in range(1, max_pages + 1):
            try:
                # Construct search URL
                search_url = f"{self.base_url}/jobs-in-{location}" if location else f"{self.base_url}/jobs"
                params = {
                    'k': keyword,
                    'l': location,
                    'p': page
                }
                
                print(f"Scraping page {page} for keyword: {keyword}")
                response = self.session.get(search_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = soup.find_all('div', class_=['jobTuple', 'job-tuple'])
                    
                    for card in job_cards:
                        job_data = self.extract_job_data(card)
                        if job_data:
                            jobs.append(job_data)
                    
                    # Random delay to avoid being blocked
                    time.sleep(random.uniform(1, 3))
                else:
                    print(f"Failed to fetch page {page}: {response.status_code}")
                    
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                continue
                
        return jobs
    
    def extract_job_data(self, job_card):
        """Extract job title and skills from a job card"""
        try:
            # Extract job title
            title_elem = job_card.find('a', class_=['title', 'jobTitle']) or job_card.find('h3')
            if not title_elem:
                return None
                
            job_title = title_elem.get_text(strip=True)
            
            # Extract skills from various sections
            skills = set()
            
            # Look for skills in job description
            desc_elem = job_card.find('div', class_=['job-description', 'jobDescription'])
            if desc_elem:
                desc_text = desc_elem.get_text()
                extracted_skills = self.extract_skills_from_text(desc_text)
                skills.update(extracted_skills)
            
            # Look for skills in tags/keywords section
            tags_elem = job_card.find('div', class_=['tags', 'skillTags'])
            if tags_elem:
                tag_elements = tags_elem.find_all(['span', 'a'])
                for tag in tag_elements:
                    skill = tag.get_text(strip=True)
                    if skill and len(skill) > 2:
                        skills.add(skill.lower())
            
            # Clean and filter skills
            cleaned_skills = self.clean_skills(list(skills))
            
            if job_title and cleaned_skills:
                return {
                    'title': job_title,
                    'skills': cleaned_skills
                }
                
        except Exception as e:
            print(f"Error extracting job data: {e}")
            
        return None
    
    def extract_skills_from_text(self, text):
        """Extract skills from job description text using dynamic patterns"""
        skills = set()
        
        # Use dynamic skill extraction based on text characteristics
        words = re.findall(r'\b[A-Za-z][A-Za-z0-9+#\.\-]*\b', text)
        
        for word in words:
            cleaned_word = word.strip().lower()
            if self.is_likely_skill(cleaned_word):
                skills.add(cleaned_word)
        
        return list(skills)
    
    def is_likely_skill(self, term):
        """Dynamically determine if a term is likely a skill without hardcoded patterns"""
        if not term or len(term) < 2:
            return False
        
        # Skip common words
        if len(term) <= 3 and term.isalpha() and not term.isupper():
            return False
        
        # Technical indicators
        if (term.endswith('js') or term.endswith('sql') or 
            any(char in term for char in ['+', '#', '.']) or
            term.isupper() and len(term) <= 6 or
            any(tech_word in term for tech_word in ['dev', 'tech', 'data', 'web', 'cloud'])):
            return True
        
        # Skill-like patterns
        if len(term) > 4 and term.isalpha():
            return True
        
        return False
        
        return list(skills)
    
    def clean_skills(self, skills):
        """Clean and filter extracted skills"""
        cleaned = []
        
        # Filter out common non-skill words
        exclude_words = {
            'and', 'or', 'the', 'with', 'using', 'for', 'in', 'on', 'at', 'to', 'from',
            'experience', 'years', 'work', 'job', 'role', 'position', 'candidate',
            'required', 'preferred', 'must', 'should', 'good', 'excellent', 'strong'
        }
        
        for skill in skills:
            skill = skill.strip().lower()
            if (len(skill) > 2 and 
                skill not in exclude_words and 
                not skill.isdigit() and
                len(skill) < 30):  # Avoid very long strings
                cleaned.append(skill)
        
        return list(set(cleaned))  # Remove duplicates
    
    def scrape_multiple_categories(self, categories=None, max_jobs_per_category=50):
        """Scrape jobs from multiple categories"""
        if categories is None:
            categories = [
                'software engineer', 'data scientist', 'web developer', 'mobile developer',
                'machine learning engineer', 'devops engineer', 'database administrator',
                'business analyst', 'project manager', 'product manager', 'ui ux designer',
                'data analyst', 'software developer', 'full stack developer', 'backend developer',
                'frontend developer', 'ai engineer', 'cloud engineer', 'cybersecurity analyst'
            ]
        
        all_jobs = []
        
        for category in categories:
            print(f"\n🔍 Scraping category: {category}")
            jobs = self.search_jobs(category, max_pages=3)  # Limit pages to avoid overload
            
            # Limit jobs per category
            if len(jobs) > max_jobs_per_category:
                jobs = jobs[:max_jobs_per_category]
            
            all_jobs.extend(jobs)
            print(f"Found {len(jobs)} jobs for {category}")
            
            # Delay between categories
            time.sleep(random.uniform(2, 5))
        
        return all_jobs

def sync_naukri_data():
    """Main function to scrape Naukri.com and update database"""
    print("🚀 Starting Naukri.com data sync...")
    
    # Initialize database
    init_db()
    
    # Clear existing data
    print("🗑️ Clearing existing career data...")
    clear_career_skills()
    
    # Create scraper
    scraper = NaukriScraper()
    
    try:
        # Scrape job data
        print("🔍 Scraping Naukri.com for job data...")
        jobs = scraper.scrape_multiple_categories()
        
        print(f"\n📊 Total jobs scraped: {len(jobs)}")
        
        # Add to database
        print("💾 Adding data to database...")
        added_count = 0
        
        for job in jobs:
            if job['skills']:  # Only add jobs with skills
                add_career_skills(job['title'], job['skills'])
                added_count += 1
        
        print(f"✅ Added {added_count} career-skill mappings to database")
        
        # Verify database
        total_careers = get_career_count()
        print(f"📈 Total careers in database: {total_careers}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during Naukri sync: {e}")
        return False

if __name__ == "__main__":
    success = sync_naukri_data()
    if success:
        print("\n🎉 Naukri.com data sync completed successfully!")
    else:
        print("\n💥 Naukri.com data sync failed!")
