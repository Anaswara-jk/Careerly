import requests
import json
import re
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import random
from dataclasses import dataclass
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    """Data class for job posting information."""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    job_type: Optional[str] = None
    experience_level: Optional[str] = None
    skills_required: List[str] = None
    source: str = "unknown"

class ImprovedJobScraper:
    """Improved job scraper with better methods and API integration."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_github_jobs(self, query: str = "", location: str = "", limit: int = 20) -> List[JobPosting]:
        """Scrape jobs from GitHub Jobs API (if still available) or similar."""
        jobs = []
        try:
            # GitHub Jobs API endpoint
            url = "https://jobs.github.com/positions.json"
            params = {
                'description': query,
                'location': location,
                'full_time': 'true'
            }
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                for job_data in data[:limit]:
                    try:
                        job = JobPosting(
                            title=job_data.get('title', 'N/A'),
                            company=job_data.get('company', 'N/A'),
                            location=job_data.get('location', 'N/A'),
                            description=job_data.get('description', ''),
                            url=job_data.get('url', ''),
                            posted_date=job_data.get('created_at', ''),
                            job_type=job_data.get('type', ''),
                            source="GitHub Jobs"
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error parsing GitHub job: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping GitHub Jobs: {e}")
        
        return jobs
    
    def scrape_remote_ok_api(self, query: str = "", limit: int = 20) -> List[JobPosting]:
        """Scrape remote jobs using Remote OK API."""
        jobs = []
        try:
            url = "https://remoteok.com/api"
            params = {}
            if query:
                params['search'] = query
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                for job_data in data[:limit]:
                    try:
                        # Clean HTML from description
                        description = BeautifulSoup(job_data.get('description', ''), 'html.parser').get_text()
                        
                        job = JobPosting(
                            title=job_data.get('position', 'N/A'),
                            company=job_data.get('company', 'N/A'),
                            location="Remote",
                            description=description,
                            url=job_data.get('url', ''),
                            salary=job_data.get('salary', ''),
                            posted_date=job_data.get('date', ''),
                            source="Remote OK"
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.error(f"Error parsing Remote OK job: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Remote OK: {e}")
        
        return jobs
    
    def scrape_indeed_simple(self, query: str, location: str = "", limit: int = 20) -> List[JobPosting]:
        """Simplified Indeed scraper with better selectors."""
        jobs = []
        try:
            search_url = "https://www.indeed.com/jobs"
            params = {
                'q': query,
                'l': location,
                'sort': 'date'
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors for job cards
                selectors = [
                    'div[data-jk]',
                    '.job_seen_beacon',
                    '.tapItem',
                    '[data-testid="job-card"]',
                    '.jobsearch-ResultsList li'
                ]
                
                job_cards = []
                for selector in selectors:
                    job_cards = soup.select(selector)
                    if job_cards:
                        logger.info(f"Found {len(job_cards)} job cards using selector: {selector}")
                        break
                
                for card in job_cards[:limit]:
                    try:
                        # Extract job title with multiple selectors
                        title = self._extract_text(card, [
                            'h2[data-testid="jobsearch-JobComponent-title"]',
                            'h2.jobTitle',
                            'h2 a',
                            'h3 a',
                            'a[data-jk]'
                        ])
                        
                        # Extract company name
                        company = self._extract_text(card, [
                            '[data-testid="jobsearch-JobComponent-company"]',
                            '.companyName',
                            '.company',
                            '[data-testid="company-name"]'
                        ])
                        
                        # Extract location
                        location = self._extract_text(card, [
                            '[data-testid="jobsearch-JobComponent-location"]',
                            '.companyLocation',
                            '.location'
                        ])
                        
                        # Extract job URL
                        job_url = self._extract_url(card, [
                            'a[data-jk]',
                            'h2 a',
                            'h3 a',
                            '[data-testid="jobsearch-JobComponent-title"] a'
                        ])
                        
                        if job_url and not job_url.startswith('http'):
                            job_url = urljoin("https://www.indeed.com", job_url)
                        
                        # Extract salary
                        salary = self._extract_text(card, [
                            '.salary-snippet',
                            '[data-testid="salary"]',
                            '.salary'
                        ])
                        
                        # Extract posted date
                        posted_date = self._extract_text(card, [
                            '.date',
                            '[data-testid="date"]',
                            '.posted-date'
                        ])
                        
                        if title and company:  # Only add if we have basic info
                            job = JobPosting(
                                title=title,
                                company=company,
                                location=location or "N/A",
                                description="",  # Will be fetched separately
                                url=job_url or "",
                                salary=salary,
                                posted_date=posted_date,
                                source="Indeed"
                            )
                            jobs.append(job)
                        
                    except Exception as e:
                        logger.error(f"Error parsing Indeed job card: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Indeed: {e}")
        
        return jobs
    
    def _extract_text(self, element, selectors: List[str]) -> str:
        """Extract text using multiple selectors."""
        for selector in selectors:
            try:
                elem = element.select_one(selector)
                if elem:
                    text = elem.get_text(strip=True)
                    if text:
                        return text
            except:
                continue
        return ""
    
    def _extract_url(self, element, selectors: List[str]) -> str:
        """Extract URL using multiple selectors."""
        for selector in selectors:
            try:
                elem = element.select_one(selector)
                if elem and elem.has_attr('href'):
                    return elem['href']
            except:
                continue
        return ""
    
    def scrape_linkedin_simple(self, query: str, location: str = "", limit: int = 20) -> List[JobPosting]:
        """Simplified LinkedIn scraper."""
        jobs = []
        try:
            search_url = "https://www.linkedin.com/jobs/search"
            params = {
                'keywords': query,
                'location': location,
                'f_TPR': 'r86400'
            }
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors
                selectors = [
                    '.base-card',
                    '.job-search-card',
                    '[data-testid="job-card"]',
                    '.job-card-container'
                ]
                
                job_cards = []
                for selector in selectors:
                    job_cards = soup.select(selector)
                    if job_cards:
                        logger.info(f"Found {len(job_cards)} LinkedIn job cards using selector: {selector}")
                        break
                
                for card in job_cards[:limit]:
                    try:
                        title = self._extract_text(card, [
                            'h3.base-search-card__title',
                            'h3 a',
                            '.job-search-card__title'
                        ])
                        
                        company = self._extract_text(card, [
                            'h4.base-search-card__subtitle',
                            '.job-search-card__company',
                            '.company-name'
                        ])
                        
                        location = self._extract_text(card, [
                            '.job-search-card__location',
                            '.location'
                        ])
                        
                        job_url = self._extract_url(card, [
                            'a.base-card__full-link',
                            'h3 a',
                            '.job-search-card__link'
                        ])
                        
                        posted_date = self._extract_text(card, [
                            'time',
                            '.job-search-card__listdate'
                        ])
                        
                        if title and company:
                            job = JobPosting(
                                title=title,
                                company=company,
                                location=location or "N/A",
                                description="",
                                url=job_url or "",
                                posted_date=posted_date,
                                source="LinkedIn"
                            )
                            jobs.append(job)
                        
                    except Exception as e:
                        logger.error(f"Error parsing LinkedIn job card: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping LinkedIn: {e}")
        
        return jobs
    
    def scrape_stack_overflow_simple(self, query: str = "", limit: int = 20) -> List[JobPosting]:
        """Simplified Stack Overflow scraper."""
        jobs = []
        try:
            search_url = "https://stackoverflow.com/jobs"
            params = {'q': query} if query else {}
            
            response = self.session.get(search_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors
                selectors = [
                    '.js-result',
                    '.job-result',
                    '[data-jobid]',
                    '.job-listing'
                ]
                
                job_cards = []
                for selector in selectors:
                    job_cards = soup.select(selector)
                    if job_cards:
                        logger.info(f"Found {len(job_cards)} Stack Overflow job cards using selector: {selector}")
                        break
                
                for card in job_cards[:limit]:
                    try:
                        title = self._extract_text(card, [
                            'h2 a',
                            '.job-title',
                            '.job-link'
                        ])
                        
                        company = self._extract_text(card, [
                            '.company-name',
                            '.employer'
                        ])
                        
                        location = self._extract_text(card, [
                            '.location',
                            '.job-location'
                        ])
                        
                        job_url = self._extract_url(card, [
                            'h2 a',
                            '.job-link',
                            'a[href*="/jobs/"]'
                        ])
                        
                        if job_url and not job_url.startswith('http'):
                            job_url = urljoin("https://stackoverflow.com", job_url)
                        
                        if title and company:
                            job = JobPosting(
                                title=title,
                                company=company,
                                location=location or "N/A",
                                description="",
                                url=job_url or "",
                                source="Stack Overflow"
                            )
                            jobs.append(job)
                        
                    except Exception as e:
                        logger.error(f"Error parsing Stack Overflow job card: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Stack Overflow: {e}")
        
        return jobs
    
    def get_job_description(self, job_url: str) -> str:
        """Get job description from URL."""
        if not job_url:
            return ""
        
        try:
            time.sleep(random.uniform(1, 2))  # Be respectful
            
            response = self.session.get(job_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try multiple selectors for job description
                desc_selectors = [
                    '[data-testid="job-description"]',
                    '.job-description',
                    '.description',
                    '#job-description',
                    '.job-details',
                    'article',
                    '.content',
                    '.job-body',
                    '.job-content'
                ]
                
                for selector in desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        description = desc_elem.get_text(strip=True)
                        description = re.sub(r'\s+', ' ', description)
                        return description[:2000]
                
                # Fallback: get all text
                return soup.get_text()[:1000]
                
        except Exception as e:
            logger.error(f"Error getting job description from {job_url}: {e}")
        
        return ""
    
    def extract_skills_from_description(self, description: str) -> List[str]:
        """Extract skills from job description."""
        if not description:
            return []
        
        # Comprehensive skill patterns
        skills_patterns = [
            # Programming Languages
            r'\b(python|javascript|js|java|c\+\+|c#|php|ruby|go|rust|swift|kotlin|scala|typescript|html|css|sql|r|matlab|perl|bash|powershell|vba|dart|elixir|erlang|f#|groovy|haskell|julia|lua|nim|ocaml|pascal|prolog|racket|scheme|smalltalk|tcl|vb\.net)\b',
            
            # Frameworks & Libraries
            r'\b(react|angular|vue|node\.js|django|flask|spring|express|laravel|asp\.net|bootstrap|jquery|pandas|numpy|tensorflow|pytorch|scikit-learn|matplotlib|seaborn|plotly|bokeh|d3\.js|three\.js|ember|backbone|meteor|svelte|nuxt|next\.js|gatsby|jupyter|anaconda|conda)\b',
            
            # Cloud & DevOps
            r'\b(docker|kubernetes|aws|azure|gcp|heroku|jenkins|git|github|gitlab|bitbucket|travis|circleci|github actions|gitlab ci|jenkins|ansible|terraform|puppet|chef|vagrant|virtualbox|vmware|vsphere)\b',
            
            # Databases
            r'\b(mysql|postgresql|mongodb|redis|oracle|sql server|sqlite|elasticsearch|cassandra|dynamodb|firebase|supabase|cockroachdb|influxdb|neo4j|mariadb|db2|sybase|access|sqlite|hbase|couchdb|riak)\b',
            
            # Tools & Platforms
            r'\b(jira|confluence|slack|teams|zoom|figma|adobe|photoshop|illustrator|excel|powerpoint|word|outlook|salesforce|hubspot|tableau|power bi|looker|metabase|grafana|kibana|splunk|datadog|newrelic|sentry|loggly)\b',
            
            # Methodologies
            r'\b(agile|scrum|kanban|waterfall|devops|ci/cd|tdd|bdd|lean|six sigma|xp|pair programming|code review|git flow|trunk based development)\b',
            
            # Soft Skills
            r'\b(leadership|communication|teamwork|problem solving|critical thinking|project management|customer service|sales|marketing|research|analysis|planning|organization|time management|negotiation|presentation|mentoring|training|collaboration|adaptability|creativity|initiative|attention to detail)\b'
        ]
        
        found_skills = set()
        for pattern in skills_patterns:
            skills = re.findall(pattern, description.lower())
            found_skills.update(skills)
        
        return list(found_skills)
    
    def search_jobs(self, query: str, location: str = "", sources: List[str] = None, limit: int = 50) -> List[JobPosting]:
        """Search jobs across multiple sources."""
        if sources is None:
            sources = ['indeed', 'linkedin', 'stack_overflow', 'remote_ok', 'github_jobs']
        
        all_jobs = []
        
        for source in sources:
            try:
                logger.info(f"Searching {source} for: {query}")
                
                if source == 'indeed':
                    jobs = self.scrape_indeed_simple(query, location, limit // len(sources))
                elif source == 'linkedin':
                    jobs = self.scrape_linkedin_simple(query, location, limit // len(sources))
                elif source == 'stack_overflow':
                    jobs = self.scrape_stack_overflow_simple(query, limit // len(sources))
                elif source == 'remote_ok':
                    jobs = self.scrape_remote_ok_api(query, limit // len(sources))
                elif source == 'github_jobs':
                    jobs = self.scrape_github_jobs(query, location, limit // len(sources))
                else:
                    continue
                
                all_jobs.extend(jobs)
                logger.info(f"Found {len(jobs)} jobs from {source}")
                
                # Add delay between sources
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error searching {source}: {e}")
                continue
        
        # Extract skills from job descriptions
        for job in all_jobs:
            if not job.description and job.url:
                job.description = self.get_job_description(job.url)
            job.skills_required = self.extract_skills_from_description(job.description)
        
        return all_jobs[:limit]
    
    def filter_jobs_by_skills(self, jobs: List[JobPosting], required_skills: List[str], min_match: int = 1) -> List[JobPosting]:
        """Filter jobs based on required skills."""
        filtered_jobs = []
        
        for job in jobs:
            if not job.skills_required:
                continue
            
            # Count matching skills
            matches = sum(1 for skill in required_skills if skill.lower() in [s.lower() for s in job.skills_required])
            
            if matches >= min_match:
                job.experience_level = f"{matches}/{len(required_skills)} skills match"
                filtered_jobs.append(job)
        
        # Sort by skill match count
        filtered_jobs.sort(key=lambda x: len(x.skills_required), reverse=True)
        return filtered_jobs
    
    def save_jobs_to_json(self, jobs: List[JobPosting], filename: str):
        """Save jobs to JSON file."""
        try:
            jobs_data = []
            for job in jobs:
                job_dict = {
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'url': job.url,
                    'salary': job.salary,
                    'posted_date': job.posted_date,
                    'job_type': job.job_type,
                    'experience_level': job.experience_level,
                    'skills_required': job.skills_required,
                    'source': job.source
                }
                jobs_data.append(job_dict)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(jobs_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(jobs)} jobs to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving jobs to JSON: {e}")

def test_improved_scraper():
    """Test the improved job scraper."""
    scraper = ImprovedJobScraper()
    
    # Test search
    query = "python developer"
    location = "remote"
    
    print(f"Searching for: {query} in {location}")
    
    # Search jobs from multiple sources
    jobs = scraper.search_jobs(query, location, sources=['indeed', 'linkedin'], limit=10)
    
    print(f"\nFound {len(jobs)} jobs:")
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job.title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        print(f"   Source: {job.source}")
        print(f"   Skills: {job.skills_required[:5] if job.skills_required else 'None'}...")
        print(f"   URL: {job.url}")
    
    # Save to JSON
    scraper.save_jobs_to_json(jobs, 'improved_test_jobs.json')

if __name__ == "__main__":
    test_improved_scraper() 