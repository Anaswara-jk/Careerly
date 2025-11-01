import json
import logging
import time
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from job_scraper_improved import ImprovedJobScraper
from database import DatabaseManager, Job, Skill
import requests
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MassJobScraper:
    """Mass job scraper for extracting thousands of jobs with full details."""
    
    def __init__(self):
        self.scraper = ImprovedJobScraper()
        self.db_manager = DatabaseManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_linkedin_mass(self, queries: List[str], locations: List[str] = None, max_jobs_per_query: int = 100) -> List[Dict[str, Any]]:
        """Mass scrape LinkedIn jobs with detailed extraction."""
        if locations is None:
            locations = ["", "remote", "United States", "United Kingdom", "Canada", "Australia", "Germany", "Netherlands"]
        
        all_jobs = []
        
        for query in queries:
            for location in locations:
                try:
                    logger.info(f"Scraping LinkedIn: {query} in {location}")
                    
                    # LinkedIn search URL
                    search_url = "https://www.linkedin.com/jobs/search"
                    params = {
                        'keywords': query,
                        'location': location,
                        'f_TPR': 'r86400',  # Last 24 hours
                        'position': 1,
                        'pageNum': 0
                    }
                    
                    response = self.session.get(search_url, params=params)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find job cards
                        job_cards = soup.find_all('div', class_='base-card')
                        
                        for card in job_cards[:max_jobs_per_query]:
                            try:
                                job_data = self._extract_linkedin_job_details(card)
                                if job_data:
                                    job_data['source'] = 'LinkedIn'
                                    job_data['search_query'] = query
                                    job_data['search_location'] = location
                                    all_jobs.append(job_data)
                                    
                            except Exception as e:
                                logger.error(f"Error extracting LinkedIn job: {e}")
                                continue
                    
                    # Be respectful with delays
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error scraping LinkedIn for {query} in {location}: {e}")
                    continue
        
        return all_jobs
    
    def _extract_linkedin_job_details(self, card) -> Optional[Dict[str, Any]]:
        """Extract detailed job information from LinkedIn job card."""
        try:
            # Basic info
            title_elem = card.find('h3', class_='base-search-card__title')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            company_elem = card.find('h4', class_='base-search-card__subtitle')
            company = company_elem.get_text(strip=True) if company_elem else None
            
            location_elem = card.find('span', class_='job-search-card__location')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Job URL
            job_link = card.find('a', class_='base-card__full-link')
            job_url = job_link['href'] if job_link else None
            
            # Posted date
            date_elem = card.find('time')
            posted_date = date_elem.get_text(strip=True) if date_elem else None
            
            if not title or not company:
                return None
            
            # Get detailed job description and application link
            job_details = self._get_linkedin_job_details(job_url) if job_url else {}
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'posted_date': posted_date,
                'description': job_details.get('description', ''),
                'application_url': job_details.get('application_url', ''),
                'salary': job_details.get('salary', ''),
                'job_type': job_details.get('job_type', ''),
                'experience_level': job_details.get('experience_level', ''),
                'skills_required': job_details.get('skills_required', [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job details: {e}")
            return None
    
    def _get_linkedin_job_details(self, job_url: str) -> Dict[str, Any]:
        """Get detailed job information from LinkedIn job page."""
        try:
            time.sleep(random.uniform(1, 3))  # Be respectful
            
            response = self.session.get(job_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract description
                desc_elem = soup.find('div', class_='show-more-less-html__markup')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                # Extract application URL
                apply_elem = soup.find('a', class_='jobs-apply-button')
                application_url = apply_elem['href'] if apply_elem else job_url
                
                # Extract salary
                salary_elem = soup.find('span', class_='compensation')
                salary = salary_elem.get_text(strip=True) if salary_elem else ''
                
                # Extract job type
                job_type_elem = soup.find('span', class_='job-type')
                job_type = job_type_elem.get_text(strip=True) if job_type_elem else ''
                
                # Extract experience level
                level_elem = soup.find('span', class_='experience-level')
                experience_level = level_elem.get_text(strip=True) if level_elem else ''
                
                # Extract skills from description
                skills_required = self._extract_skills_from_text(description)
                
                return {
                    'description': description,
                    'application_url': application_url,
                    'salary': salary,
                    'job_type': job_type,
                    'experience_level': experience_level,
                    'skills_required': skills_required
                }
                
        except Exception as e:
            logger.error(f"Error getting LinkedIn job details: {e}")
        
        return {}
    
    def scrape_indeed_mass(self, queries: List[str], locations: List[str] = None, max_jobs_per_query: int = 100) -> List[Dict[str, Any]]:
        """Mass scrape Indeed jobs with detailed extraction."""
        if locations is None:
            locations = ["", "remote", "United States", "United Kingdom", "Canada", "Australia"]
        
        all_jobs = []
        
        for query in queries:
            for location in locations:
                try:
                    logger.info(f"Scraping Indeed: {query} in {location}")
                    
                    # Indeed search URL
                    search_url = "https://www.indeed.com/jobs"
                    params = {
                        'q': query,
                        'l': location,
                        'sort': 'date'
                    }
                    
                    response = self.session.get(search_url, params=params)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Find job cards
                        job_cards = soup.find_all('div', class_='job_seen_beacon')
                        
                        for card in job_cards[:max_jobs_per_query]:
                            try:
                                job_data = self._extract_indeed_job_details(card)
                                if job_data:
                                    job_data['source'] = 'Indeed'
                                    job_data['search_query'] = query
                                    job_data['search_location'] = location
                                    all_jobs.append(job_data)
                                    
                            except Exception as e:
                                logger.error(f"Error extracting Indeed job: {e}")
                                continue
                    
                    time.sleep(random.uniform(2, 5))
                    
                except Exception as e:
                    logger.error(f"Error scraping Indeed for {query} in {location}: {e}")
                    continue
        
        return all_jobs
    
    def _extract_indeed_job_details(self, card) -> Optional[Dict[str, Any]]:
        """Extract detailed job information from Indeed job card."""
        try:
            # Basic info
            title_elem = card.find('h2', class_='jobTitle')
            title = title_elem.get_text(strip=True) if title_elem else None
            
            company_elem = card.find('span', class_='companyName')
            company = company_elem.get_text(strip=True) if company_elem else None
            
            location_elem = card.find('div', class_='companyLocation')
            location = location_elem.get_text(strip=True) if location_elem else None
            
            # Job URL
            job_link = card.find('a', class_='jcs-JobTitle')
            job_url = f"https://www.indeed.com{job_link['href']}" if job_link else None
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            salary = salary_elem.get_text(strip=True) if salary_elem else None
            
            # Posted date
            date_elem = card.find('span', class_='date')
            posted_date = date_elem.get_text(strip=True) if date_elem else None
            
            if not title or not company:
                return None
            
            # Get detailed job description and application link
            job_details = self._get_indeed_job_details(job_url) if job_url else {}
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'url': job_url,
                'posted_date': posted_date,
                'salary': salary,
                'description': job_details.get('description', ''),
                'application_url': job_details.get('application_url', ''),
                'job_type': job_details.get('job_type', ''),
                'experience_level': job_details.get('experience_level', ''),
                'skills_required': job_details.get('skills_required', [])
            }
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job details: {e}")
            return None
    
    def _get_indeed_job_details(self, job_url: str) -> Dict[str, Any]:
        """Get detailed job information from Indeed job page."""
        try:
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(job_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract description
                desc_elem = soup.find('div', id='jobDescriptionText')
                description = desc_elem.get_text(strip=True) if desc_elem else ''
                
                # Extract application URL
                apply_elem = soup.find('a', class_='ia-IndeedApplyButton')
                application_url = apply_elem['href'] if apply_elem else job_url
                
                # Extract job type
                job_type_elem = soup.find('span', class_='job-type')
                job_type = job_type_elem.get_text(strip=True) if job_type_elem else ''
                
                # Extract experience level
                level_elem = soup.find('span', class_='experience-level')
                experience_level = level_elem.get_text(strip=True) if level_elem else ''
                
                # Extract skills from description
                skills_required = self._extract_skills_from_text(description)
                
                return {
                    'description': description,
                    'application_url': application_url,
                    'job_type': job_type,
                    'experience_level': experience_level,
                    'skills_required': skills_required
                }
                
        except Exception as e:
            logger.error(f"Error getting Indeed job details: {e}")
        
        return {}
    
    def scrape_remote_ok_mass(self, queries: List[str], max_jobs_per_query: int = 100) -> List[Dict[str, Any]]:
        """Mass scrape Remote OK jobs."""
        all_jobs = []
        
        for query in queries:
            try:
                logger.info(f"Scraping Remote OK: {query}")
                
                url = "https://remoteok.com/api"
                params = {'search': query} if query else {}
                
                response = self.session.get(url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    
                    for job_data in data[:max_jobs_per_query]:
                        try:
                            # Clean HTML from description
                            description = BeautifulSoup(job_data.get('description', ''), 'html.parser').get_text()
                            
                            job = {
                                'title': job_data.get('position', 'N/A'),
                                'company': job_data.get('company', 'N/A'),
                                'location': 'Remote',
                                'description': description,
                                'url': job_data.get('url', ''),
                                'application_url': job_data.get('url', ''),
                                'salary': job_data.get('salary', ''),
                                'posted_date': job_data.get('date', ''),
                                'job_type': 'Remote',
                                'experience_level': '',
                                'skills_required': self._extract_skills_from_text(description),
                                'source': 'Remote OK',
                                'search_query': query,
                                'search_location': 'Remote'
                            }
                            all_jobs.append(job)
                            
                        except Exception as e:
                            logger.error(f"Error processing Remote OK job: {e}")
                            continue
                
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error scraping Remote OK for {query}: {e}")
                continue
        
        return all_jobs
    
    def _extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from job description text."""
        if not text:
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
            skills = re.findall(pattern, text.lower())
            found_skills.update(skills)
        
        return list(found_skills)
    
    def store_jobs_in_database(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store jobs in database with detailed information."""
        stored_count = 0
        error_count = 0
        
        for job_data in jobs:
            try:
                # Add application_url field to database if not exists
                job_data['application_url'] = job_data.get('application_url', job_data.get('url', ''))
                
                stored_job = self.db_manager.add_job(job_data)
                stored_count += 1
                
                if stored_count % 10 == 0:
                    logger.info(f"Stored {stored_count} jobs so far...")
                    
            except Exception as e:
                logger.error(f"Error storing job {job_data.get('title', 'Unknown')}: {e}")
                error_count += 1
                continue
        
        return {
            'total_jobs': len(jobs),
            'stored_count': stored_count,
            'error_count': error_count
        }
    
    def mass_scrape_and_store(self, queries: List[str] = None, max_jobs_per_query: int = 50) -> Dict[str, Any]:
        """Mass scrape and store jobs from multiple sources."""
        if queries is None:
            queries = [
                "python developer", "software engineer", "data scientist", "frontend developer", 
                "backend developer", "devops engineer", "machine learning engineer", "full stack developer",
                "react developer", "java developer", "javascript developer", "node.js developer",
                "django developer", "flask developer", "spring developer", "angular developer",
                "vue developer", "mobile developer", "ios developer", "android developer",
                "cloud engineer", "aws engineer", "azure engineer", "database administrator",
                "data analyst", "business analyst", "product manager", "project manager",
                "ui designer", "ux designer", "graphic designer", "content writer", "marketing manager",
                "sales representative", "customer service", "human resources", "finance analyst"
            ]
        
        all_jobs = []
        
        # Scrape from multiple sources
        sources = [
            ('LinkedIn', self.scrape_linkedin_mass),
            ('Indeed', self.scrape_indeed_mass),
            ('Remote OK', self.scrape_remote_ok_mass)
        ]
        
        for source_name, scraper_func in sources:
            try:
                logger.info(f"Starting {source_name} scraping...")
                
                if source_name == 'Remote OK':
                    jobs = scraper_func(queries, max_jobs_per_query)
                else:
                    jobs = scraper_func(queries, max_jobs_per_query=max_jobs_per_query)
                
                all_jobs.extend(jobs)
                logger.info(f"Scraped {len(jobs)} jobs from {source_name}")
                
            except Exception as e:
                logger.error(f"Error scraping from {source_name}: {e}")
                continue
        
        # Store in database
        logger.info(f"Storing {len(all_jobs)} jobs in database...")
        storage_result = self.store_jobs_in_database(all_jobs)
        
        return {
            'scraped_count': len(all_jobs),
            'storage_result': storage_result,
            'queries_processed': len(queries)
        }
    
    def prepare_ml_training_data(self) -> Dict[str, Any]:
        """Prepare data for ML model training."""
        try:
            db = self.db_manager.SessionLocal()
            
            # Get all jobs with skills
            jobs = db.query(Job).join(Job.skills).all()
            
            training_data = []
            for job in jobs:
                job_skills = [skill.name for skill in job.skills]
                
                training_data.append({
                    'job_id': job.id,
                    'title': job.title,
                    'company': job.company,
                    'location': job.location,
                    'description': job.description,
                    'skills': job_skills,
                    'source': job.source,
                    'job_type': job.job_type,
                    'experience_level': job.experience_level,
                    'salary': job.salary,
                    'application_url': getattr(job, 'application_url', '')
                })
            
            db.close()
            
            # Save training data to JSON
            with open('ml_training_data.json', 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            return {
                'total_records': len(training_data),
                'file_path': 'ml_training_data.json',
                'sample_data': training_data[:5] if training_data else []
            }
            
        except Exception as e:
            logger.error(f"Error preparing ML training data: {e}")
            return {'error': str(e)}

def test_mass_scraper():
    """Test the mass job scraper."""
    scraper = MassJobScraper()
    
    # Test with a few queries first
    test_queries = ["python developer", "software engineer", "data scientist"]
    
    print("Starting mass job scraping...")
    result = scraper.mass_scrape_and_store(test_queries, max_jobs_per_query=20)
    
    print(f"Scraping result: {json.dumps(result, indent=2)}")
    
    # Prepare ML training data
    print("\nPreparing ML training data...")
    ml_data = scraper.prepare_ml_training_data()
    print(f"ML data result: {json.dumps(ml_data, indent=2)}")

if __name__ == "__main__":
    test_mass_scraper() 