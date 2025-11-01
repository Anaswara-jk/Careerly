#!/usr/bin/env python3
"""
Automated Naukri.com updater that periodically scrapes new job postings
and updates the database with emerging careers and skills
"""
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from urllib.parse import urljoin, quote
import json
import threading
import schedule
from datetime import datetime, timedelta
from db import init_db, add_career_skills, get_career_skills, get_career_count
import subprocess
import os

class AutoNaukriUpdater:
    def __init__(self):
        self.base_url = "https://www.naukri.com"
        self.session = requests.Session()
        self.update_headers()
        self.last_update = None
        self.update_interval_hours = 24  # Update every 24 hours
        self.min_new_careers_for_retrain = 10  # Retrain ML model if 10+ new careers added
        
    def update_headers(self):
        """Update session headers with realistic browser simulation"""
        headers = {
            'User-Agent': random.choice([
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)
    
    def get_trending_job_categories(self):
        """Dynamically extract trending job categories from Naukri.com homepage"""
        trending_categories = []
        
        try:
            # Try to get trending categories from Naukri.com homepage
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for trending job links, popular searches, or category sections
                category_selectors = [
                    'a[href*="jobs"]',  # Job links
                    '.trending-searches a',  # Trending searches
                    '.popular-categories a',  # Popular categories
                    '.job-categories a',  # Job categories
                    '[data-job-category]'  # Data attributes
                ]
                
                for selector in category_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True).lower()
                        # Extract job titles from links
                        if text and len(text) > 3 and len(text) < 50:
                            # Clean the text to get job category
                            cleaned = re.sub(r'\d+|jobs?|openings?|vacancies', '', text).strip()
                            if cleaned and len(cleaned) > 3:
                                trending_categories.append(cleaned)
                
                # Also extract from search suggestions or autocomplete if available
                search_elements = soup.find_all(['input', 'div'], {'placeholder': re.compile(r'search|job', re.I)})
                for elem in search_elements:
                    suggestions = elem.get('data-suggestions', '')
                    if suggestions:
                        try:
                            suggestion_list = json.loads(suggestions)
                            trending_categories.extend([s.lower() for s in suggestion_list if isinstance(s, str)])
                        except:
                            pass
        
        except Exception as e:
            print(f"⚠️ Could not extract trending categories from homepage: {e}")
        
        # Remove duplicates and filter
        trending_categories = list(set(trending_categories))
        
        # If we couldn't extract any categories dynamically, extract from existing database
        if not trending_categories:
            print("🔄 No categories extracted from homepage, using existing database for discovery...")
            trending_categories = self.get_categories_from_existing_database()
        
        return trending_categories[:35]  # Limit to prevent overload
    
    def discover_job_categories_dynamically(self, base_terms):
        """Discover job categories by analyzing actual search results"""
        discovered_categories = set()
        
        for term in base_terms:
            try:
                # Search for the base term and extract actual job titles
                search_url = f"{self.base_url}/jobs"
                params = {'k': term, 'l': 'India'}
                
                response = self.session.get(search_url, params=params, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract job titles from search results
                    title_selectors = ['a.title', 'h3 a', '.jobTitle a', '.job-title a']
                    for selector in title_selectors:
                        titles = soup.select(selector)
                        for title_elem in titles:
                            title = title_elem.get_text(strip=True).lower()
                            if title and len(title) > 5 and len(title) < 50:
                                discovered_categories.add(title)
                
                time.sleep(2)  # Delay between searches
                
            except Exception as e:
                print(f"⚠️ Error discovering categories for {term}: {e}")
                continue
        
        return list(discovered_categories)
    
    def get_categories_from_existing_database(self):
        """Extract job categories from existing database careers"""
        from db import get_career_skills
        
        categories = set()
        try:
            career_skills_data = get_career_skills()
            
            # Extract unique job titles from database
            for career_title, _ in career_skills_data:
                if career_title and len(career_title.strip()) > 3:
                    # Clean the career title to use as search category
                    cleaned_title = career_title.strip().lower()
                    categories.add(cleaned_title)
            
            print(f"📊 Extracted {len(categories)} categories from existing database")
            
        except Exception as e:
            print(f"⚠️ Error extracting categories from database: {e}")
        
        return list(categories)[:20]  # Limit to prevent overload
    
    def scrape_job_listings(self, keyword, max_pages=2):
        """Scrape job listings for a specific keyword with improved anti-detection"""
        jobs = []
        
        try:
            for page in range(1, max_pages + 1):
                # Construct search URL
                search_url = f"{self.base_url}/jobs"
                params = {
                    'k': keyword,
                    'l': 'India',  # Search across India
                    'p': page,
                    'sort': 'date'  # Get latest jobs first
                }
                
                print(f"  📄 Scraping page {page} for: {keyword}")
                
                # Random delay before request
                time.sleep(random.uniform(2, 5))
                
                response = self.session.get(search_url, params=params, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Try multiple selectors for job cards
                    job_cards = (
                        soup.find_all('div', class_='jobTuple') or
                        soup.find_all('article', class_='jobTuple') or
                        soup.find_all('div', {'data-job-id': True}) or
                        soup.find_all('div', class_='job-tuple')
                    )
                    
                    if not job_cards:
                        print(f"    ⚠️ No job cards found on page {page}")
                        continue
                    
                    for card in job_cards:
                        job_data = self.extract_job_info(card)
                        if job_data:
                            jobs.append(job_data)
                    
                    print(f"    ✅ Found {len([card for card in job_cards if self.extract_job_info(card)])} jobs on page {page}")
                    
                else:
                    print(f"    ❌ Failed to fetch page {page}: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"    💥 Error scraping {keyword}: {e}")
        
        return jobs
    
    def extract_job_info(self, job_card):
        """Extract job title and skills from job card with multiple fallback methods"""
        try:
            # Extract job title with multiple selectors
            title = None
            title_selectors = [
                'a.title', 'h3 a', '.jobTitle a', '.job-title a',
                'h2 a', 'h4 a', '[data-job-title]'
            ]
            
            for selector in title_selectors:
                title_elem = job_card.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    break
            
            if not title:
                return None
            
            # Extract skills from job description and tags
            skills = set()
            
            # Look for skills in various sections
            skill_sections = job_card.find_all(['div', 'span', 'p'], 
                class_=re.compile(r'(skill|tag|keyword|requirement)', re.I))
            
            for section in skill_sections:
                text = section.get_text().lower()
                extracted_skills = self.extract_skills_from_text(text)
                skills.update(extracted_skills)
            
            # Also check the full job card text
            full_text = job_card.get_text().lower()
            additional_skills = self.extract_skills_from_text(full_text)
            skills.update(additional_skills)
            
            # Clean and filter skills
            cleaned_skills = self.clean_and_validate_skills(list(skills))
            
            if title and len(cleaned_skills) >= 3:  # Minimum 3 skills required
                return {
                    'title': title.strip(),
                    'skills': cleaned_skills
                }
                
        except Exception as e:
            print(f"      ⚠️ Error extracting job info: {e}")
        
        return None
    
    def extract_skills_from_text(self, text):
        """Dynamically extract skills from text without hardcoded patterns"""
        skills = set()
        text_lower = text.lower()
        
        # Dynamic skill extraction approach
        # 1. Extract words that look like technical terms
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9+#\.\-]*\b', text)
        
        for word in words:
            word_clean = word.lower().strip()
            
            # Dynamic criteria for identifying skills
            if self.is_likely_skill(word_clean):
                skills.add(word_clean)
        
        # 2. Extract multi-word technical terms
        # Look for common patterns like "machine learning", "data science", etc.
        multi_word_patterns = [
            r'\b([a-z]+\s+[a-z]+(?:\s+[a-z]+)?)\b'  # 2-3 word combinations
        ]
        
        for pattern in multi_word_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if self.is_likely_skill(match):
                    skills.add(match)
        
        return list(skills)
    
    def is_likely_skill(self, term):
        """Dynamically determine if a term is likely a skill based on characteristics"""
        if not term or len(term) < 2 or len(term) > 30:
            return False
        
        # Skip common non-skill words
        common_words = {
            'and', 'or', 'the', 'with', 'using', 'for', 'in', 'on', 'at', 'to', 'from',
            'experience', 'years', 'work', 'job', 'role', 'position', 'candidate',
            'required', 'preferred', 'must', 'should', 'good', 'excellent', 'strong',
            'knowledge', 'understanding', 'ability', 'skills', 'working', 'hands',
            'company', 'team', 'project', 'business', 'client', 'customer', 'service',
            'time', 'day', 'week', 'month', 'year', 'location', 'salary', 'benefits'
        }
        
        if term in common_words:
            return False
        
        # Characteristics that suggest a skill:
        skill_indicators = [
            # Technical abbreviations (2-5 chars, often uppercase)
            len(term) <= 5 and any(c.isupper() for c in term),
            
            # Contains version numbers or special chars (e.g., "c++", "node.js")
            any(char in term for char in ['+', '#', '.', '-']) and not term.startswith('-'),
            
            # Ends with common tech suffixes
            any(term.endswith(suffix) for suffix in ['js', 'py', 'sql', 'db', 'api', 'ui', 'ux']),
            
            # Contains common tech prefixes
            any(term.startswith(prefix) for prefix in ['web', 'app', 'data', 'cloud', 'micro']),
            
            # Multi-word technical terms
            ' ' in term and len(term.split()) <= 3,
            
            # Common patterns in job descriptions that indicate skills
            any(pattern in term for pattern in ['develop', 'engineer', 'manage', 'analy', 'design'])
        ]
        
        return any(skill_indicators)
    
    def clean_and_validate_skills(self, skills):
        """Clean and validate extracted skills dynamically"""
        cleaned = []
        
        for skill in skills:
            skill = skill.strip().lower()
            if self.is_valid_skill_term(skill):
                cleaned.append(skill)
        
        return list(set(cleaned))  # Remove duplicates
    
    def is_valid_skill_term(self, term):
        """Dynamically validate if a term is a valid skill without hardcoded lists"""
        if not term or len(term) < 2 or len(term) > 30:
            return False
        
        # Skip if it's just digits
        if term.isdigit():
            return False
        
        # Skip if it contains problematic characters
        if any(char in term for char in ['@', '$', '%', '&', '*', '(', ')', '[', ']']):
            return False
        
        # Skip very common English words (minimal set)
        if len(term) <= 3 and term in {'and', 'or', 'the', 'for', 'in', 'on', 'at', 'to', 'of', 'is', 'are', 'was', 'be', 'a', 'an'}:
            return False
        
        # Accept terms that look technical or professional
        return True
    
    def check_for_new_careers(self, scraped_jobs):
        """Check which careers are new and need to be added to database"""
        existing_careers = {title.lower() for title, _ in get_career_skills()}
        new_jobs = []
        
        for job in scraped_jobs:
            job_title_lower = job['title'].lower()
            if job_title_lower not in existing_careers:
                new_jobs.append(job)
        
        return new_jobs
    
    def update_database(self):
        """Main update function that scrapes new data and updates database"""
        print(f"\n🚀 Starting automated Naukri.com update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        initial_career_count = get_career_count()
        print(f"📊 Current careers in database: {initial_career_count}")
        
        # Get trending categories
        categories = self.get_trending_job_categories()
        print(f"🔍 Scanning {len(categories)} job categories for new opportunities...")
        
        all_new_jobs = []
        
        # Scrape each category
        for i, category in enumerate(categories, 1):
            print(f"\n📂 [{i}/{len(categories)}] Scanning: {category}")
            
            try:
                # Update headers periodically
                if i % 5 == 0:
                    self.update_headers()
                
                scraped_jobs = self.scrape_job_listings(category, max_pages=2)
                new_jobs = self.check_for_new_careers(scraped_jobs)
                
                if new_jobs:
                    print(f"  ✨ Found {len(new_jobs)} new career opportunities!")
                    all_new_jobs.extend(new_jobs)
                else:
                    print(f"  ℹ️ No new careers found in this category")
                
                # Random delay between categories
                time.sleep(random.uniform(3, 8))
                
            except Exception as e:
                print(f"  💥 Error processing {category}: {e}")
                continue
        
        # Add new jobs to database
        if all_new_jobs:
            print(f"\n💾 Adding {len(all_new_jobs)} new careers to database...")
            added_count = 0
            
            for job in all_new_jobs:
                try:
                    if add_career_skills(job['title'], job['skills']):
                        added_count += 1
                        print(f"  ✅ Added: {job['title']} ({len(job['skills'])} skills)")
                except Exception as e:
                    print(f"  ❌ Failed to add {job['title']}: {e}")
            
            final_career_count = get_career_count()
            print(f"\n📈 Database updated successfully!")
            print(f"   • New careers added: {added_count}")
            print(f"   • Total careers: {final_career_count}")
            
            # Retrain ML model if significant new data added
            if added_count >= self.min_new_careers_for_retrain:
                print(f"\n🤖 Retraining ML model with new data...")
                self.retrain_ml_model()
            
        else:
            print(f"\n📊 No new careers found. Database is up to date!")
        
        self.last_update = datetime.now()
        print(f"✅ Update completed at {self.last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def retrain_ml_model(self):
        """Retrain the ML model with updated data"""
        try:
            print("🔄 Starting ML model retraining...")
            result = subprocess.run([
                'python', 'ml_model/train_model.py'
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            if result.returncode == 0:
                print("✅ ML model retrained successfully!")
            else:
                print(f"❌ ML model retraining failed: {result.stderr}")
                
        except Exception as e:
            print(f"💥 Error retraining ML model: {e}")
    
    def start_scheduler(self):
        """Start the automated update scheduler"""
        print(f"⏰ Starting automated Naukri.com updater...")
        print(f"   • Update interval: {self.update_interval_hours} hours")
        print(f"   • Next update: {(datetime.now() + timedelta(hours=self.update_interval_hours)).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Schedule regular updates
        schedule.every(self.update_interval_hours).hours.do(self.update_database)
        
        # Run initial update
        self.update_database()
        
        # Keep scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def start_auto_updater():
    """Start the automated updater in a separate thread"""
    updater = AutoNaukriUpdater()
    
    # Run in background thread
    update_thread = threading.Thread(target=updater.start_scheduler, daemon=True)
    update_thread.start()
    
    return updater

if __name__ == "__main__":
    # Run the automated updater
    updater = AutoNaukriUpdater()
    updater.start_scheduler()
