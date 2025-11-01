import os
import requests
import zipfile
import sqlite3
import csv
import time
import socket
import logging
from typing import Optional, Tuple, Dict, List, Any
from urllib.parse import urlparse
from skills_taxonomy import refresh_skills_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# O*NET database mirrors - try these in order if primary fails
ONET_MIRRORS = [
    "https://www.onetcenter.org/dl_files/database/db_29_3_text.zip",  # Primary
    "https://storage.googleapis.com/onet-database/db_29_3_text.zip",  # Mirror 1
    "https://github.com/your-org/onet-mirror/raw/main/db_29_3_text.zip"  # Fallback mirror
]

DB_PATH = "career_skills.db"
TMP_DIR = "onet_tmp"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def check_internet_connection() -> bool:
    """Check if we have a working internet connection"""
    try:
        # Try to resolve a well-known domain
        socket.gethostbyname("onetcenter.org")
        return True
    except socket.gaierror:
        logger.warning("No internet connection or DNS resolution failed")
        return False

def download_file(url: str, dest_path: str, timeout: int = 300) -> bool:
    """Download a file with retries and progress tracking"""
    for attempt in range(MAX_RETRIES):
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                r.raise_for_status()
                total_size = int(r.headers.get('content-length', 0))
                downloaded = 0
                
                with open(dest_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive chunks
                            f.write(chunk)
                            downloaded += len(chunk)
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.info(f"Downloading: {progress:.1f}%")
                
                logger.info(f"Successfully downloaded {os.path.basename(dest_path)}")
                return True
                
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.error(f"Failed to download {url} after {MAX_RETRIES} attempts")
                return False
    return False

def extract_zip(zip_path: str, extract_to: str) -> bool:
    """Extract zip file with error handling"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
        # Verify extraction
        if not os.path.exists(extract_to) or not os.listdir(extract_to):
            logger.error(f"Failed to extract files to {extract_to}")
            return False
            
        logger.info("Extracted files:")
        for root, dirs, files in os.walk(extract_to):
            for file in files:
                logger.info(f"  {os.path.join(root, file)}")
                
        return True
    except (zipfile.BadZipFile, OSError) as e:
        logger.error(f"Error extracting {zip_path}: {e}")
        return False

def download_onet() -> Tuple[bool, str]:
    """Download and extract O*NET database with fallback mirrors"""
    os.makedirs(TMP_DIR, exist_ok=True)
    zip_path = os.path.join(TMP_DIR, "onet.zip")
    
    # Clean up any existing files
    if os.path.exists(zip_path):
        try:
            os.remove(zip_path)
        except OSError as e:
            logger.warning(f"Could not remove existing zip file: {e}")
    
    # Check internet connection first
    if not check_internet_connection():
        return False, "No internet connection available"
    
    # Try each mirror in order
    for mirror_url in ONET_MIRRORS:
        logger.info(f"Attempting to download from: {mirror_url}")
        
        if download_file(mirror_url, zip_path):
            # Verify the downloaded file
            if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1024:  # At least 1KB
                logger.warning("Downloaded file is too small or corrupted")
                continue
                
            # Extract the zip file
            if extract_zip(zip_path, TMP_DIR):
                return True, f"Successfully downloaded and extracted from {urlparse(mirror_url).netloc}"
    
    return False, "All download attempts failed"

def parse_skills():
    """Parse O*NET skills and occupation data from multiple sources"""
    try:
        # Parse occupation titles - files are in db_29_3_text subdirectory
        occ_file = os.path.join(TMP_DIR, "db_29_3_text", "Occupation Data.txt")
        if not os.path.exists(occ_file):
            print(f"Error: {occ_file} not found")
            return []
        
        occ_map = {}
        with open(occ_file, encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                occ_map[row["O*NET-SOC Code"]] = row["Title"]
        
        print(f"Loaded {len(occ_map)} occupations")
        
        skill_map = {}
        
        # 1. Parse general skills from Skills.txt (but with higher threshold)
        skills_file = os.path.join(TMP_DIR, "db_29_3_text", "Skills.txt")
        if os.path.exists(skills_file):
            with open(skills_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    try:
                        soc = row["O*NET-SOC Code"]
                        skill = row["Element Name"]
                        importance = float(row["Data Value"])
                        
                        # Higher threshold for general skills (4.0+)
                        if importance >= 4.0:
                            if soc not in skill_map:
                                skill_map[soc] = set()
                            skill_map[soc].add(skill.lower().strip())
                    except (ValueError, KeyError):
                        continue
        
        # 2. Parse technology skills from Technology Skills.txt
        tech_file = os.path.join(TMP_DIR, "db_29_3_text", "Technology Skills.txt")
        tech_count = 0
        if os.path.exists(tech_file):
            with open(tech_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                print(f"Technology Skills.txt columns: {reader.fieldnames}")
                for row in reader:
                    try:
                        soc = row["O*NET-SOC Code"]
                        # Use Example column which likely contains the actual technology names
                        tech_skill = row.get("Example", "").strip()
                        
                        if tech_skill and len(tech_skill) > 2:
                            if soc not in skill_map:
                                skill_map[soc] = set()
                            skill_map[soc].add(tech_skill.lower().strip())
                            tech_count += 1
                    except KeyError:
                        continue
            print(f"Added {tech_count} technology skills")
        else:
            print("Technology Skills.txt not found")
        
        # 3. Parse knowledge areas from Knowledge.txt
        knowledge_count = 0
        knowledge_file = os.path.join(TMP_DIR, "db_29_3_text", "Knowledge.txt")
        if os.path.exists(knowledge_file):
            with open(knowledge_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    try:
                        soc = row["O*NET-SOC Code"]
                        knowledge = row["Element Name"]
                        importance = float(row["Data Value"])
                        
                        # Include important knowledge areas
                        if importance >= 3.5:
                            if soc not in skill_map:
                                skill_map[soc] = set()
                            skill_map[soc].add(f"{knowledge.lower().strip()} knowledge")
                            knowledge_count += 1
                    except (ValueError, KeyError):
                        continue
            print(f"Added {knowledge_count} knowledge areas")
        else:
            print("Knowledge.txt not found")
        
        # 4. Parse tools from Tools Used.txt
        tools_file = os.path.join(TMP_DIR, "db_29_3_text", "Tools Used.txt")
        tools_count = 0
        if os.path.exists(tools_file):
            with open(tools_file, encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                print(f"Tools Used.txt columns: {reader.fieldnames}")
                for row in reader:
                    try:
                        soc = row["O*NET-SOC Code"]
                        # Try different possible column names for tools
                        tool = None
                        for col in ["Hot Technology", "Technology", "Example", "Commodity Title"]:
                            if col in row and row[col]:
                                tool = row[col]
                                break
                        
                        if tool and len(tool.strip()) > 2:
                            if soc not in skill_map:
                                skill_map[soc] = set()
                            skill_map[soc].add(tool.lower().strip())
                            tools_count += 1
                    except KeyError:
                        continue
            print(f"Added {tools_count} tools")
        else:
            print("Tools Used.txt not found")
        
        print(f"Processed skills for {len(skill_map)} occupations")
        
        # Build final mapping
        career_skills = []
        for soc, skills in skill_map.items():
            title = occ_map.get(soc, soc)
            if skills and len(skills) > 0:
                # Clean and filter skills
                clean_skills = [s for s in skills if len(s) > 2 and len(s) < 100]
                if clean_skills:
                    career_skills.append((title, ",".join(sorted(clean_skills))))
        
        print(f"Created {len(career_skills)} career-skill mappings")
        
        # Debug: Show a few examples
        if career_skills:
            print("Sample mappings:")
            for i, (title, skills) in enumerate(career_skills[:3]):
                skills_list = skills.split(",")[:5]  # First 5 skills
                print(f"  {title}: {', '.join(skills_list)} (total: {len(skills.split(','))})")
        
        return career_skills
        
    except Exception as e:
        print(f"Error parsing O*NET data: {e}")
        return []

def update_db(career_skills):
    """Update SQLite database with career-skills mappings"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create table if it doesn't exist
        c.execute("""
            CREATE TABLE IF NOT EXISTS career_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                career_title TEXT,
                skills TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Clear old data
        c.execute("DELETE FROM career_skills")
        
        # Insert new data
        for title, skills in career_skills:
            c.execute(
                "INSERT INTO career_skills (career_title, skills) VALUES (?, ?)", 
                (title, skills)
            )
        
        conn.commit()
        conn.close()
        
        print(f"Database updated with {len(career_skills)} records")
        
        # Refresh the skills cache
        refresh_skills_cache()
        print("Skills cache refreshed")
        
        return True
        
    except Exception as e:
        print(f"Error updating database: {e}")
        return False

def cleanup_temp_files():
    """Clean up temporary files"""
    try:
        import shutil
        if os.path.exists(TMP_DIR):
            shutil.rmtree(TMP_DIR)
            print("Temporary files cleaned up")
    except Exception as e:
        print(f"Warning: Could not clean up temp files: {e}")

def main() -> bool:
    """
    Main function to sync O*NET data with improved error handling and logging.
    
    Returns:
        bool: True if sync was successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("Starting O*NET Data Synchronization")
    logger.info("=" * 60)
    
    try:
        # Step 1: Download O*NET data
        logger.info("\n[1/3] Downloading O*NET database...")
        success, message = download_onet()
        if not success:
            logger.error(f"Failed to download O*NET data: {message}")
            return False
        logger.info(f"✓ {message}")
        
        # Step 2: Parse skills and careers
        logger.info("\n[2/3] Parsing skills and careers...")
        try:
            career_skills = parse_skills()
            if not career_skills:
                logger.error("No career skills data was parsed")
                return False
            logger.info(f"✓ Successfully parsed {len(career_skills)} career entries")
        except Exception as e:
            logger.error(f"Error parsing skills: {e}", exc_info=True)
            return False
        
        # Step 3: Update database
        logger.info("\n[3/3] Updating database...")
        try:
            if not update_db(career_skills):
                logger.error("Failed to update database")
                return False
            logger.info("✓ Database updated successfully")
        except Exception as e:
            logger.error(f"Database update failed: {e}", exc_info=True)
            return False
        
        # Refresh skills cache if available
        try:
            logger.info("\nRefreshing skills cache...")
            refresh_skills_cache()
            logger.info("✓ Skills cache refreshed")
        except Exception as e:
            logger.warning(f"Could not refresh skills cache (this is non-fatal): {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("O*NET SYNC COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.critical(f"Critical error during sync: {e}", exc_info=True)
        return False
    
    finally:
        # Always clean up temp files
        try:
            cleanup_temp_files()
            logger.debug("Temporary files cleaned up")
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
