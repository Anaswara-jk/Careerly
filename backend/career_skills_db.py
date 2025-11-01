import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_NAME = "career_skills.db"

def init_db():
    """Initialize the career skills database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            career TEXT NOT NULL,
            skill TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_career_skills():
    """
    Returns a list of (career_title, [skills]) from the database.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT career, GROUP_CONCAT(skill) FROM skills GROUP BY career")
    rows = c.fetchall()
    conn.close()
    return [(r[0], r[1].split(",")) if r[1] else (r[0], []) for r in rows]

def add_career_skills(career, skills):
    """
    Adds a career and its skills to the database.
    Avoids duplicates.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    for skill in skills:
        skill = skill.strip()
        if skill:
            c.execute("INSERT INTO skills (career, skill) VALUES (?, ?)", (career, skill))
    conn.commit()
    conn.close()

def get_career_count():
    """
    Returns the number of unique careers in the database.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT career) FROM skills")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_skills_by_career(career: str) -> List[str]:
    """
    Get all skills for a specific career.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT skill FROM skills WHERE career = ?", (career,))
    skills = [row[0] for row in c.fetchall()]
    conn.close()
    return skills

def get_careers_by_skill(skill: str) -> List[str]:
    """
    Get all careers that require a specific skill.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT career FROM skills WHERE skill = ?", (skill,))
    careers = [row[0] for row in c.fetchall()]
    conn.close()
    return careers

def get_all_skills() -> List[str]:
    """
    Get all unique skills from the database.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT skill FROM skills")
    skills = [row[0] for row in c.fetchall()]
    conn.close()
    return skills

def get_all_careers() -> List[str]:
    """
    Get all unique careers from the database.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT DISTINCT career FROM skills")
    careers = [row[0] for row in c.fetchall()]
    conn.close()
    return careers

def add_job_skills_from_scraper(job_title: str, skills: List[str]):
    """
    Add skills from job scraper to the career skills database.
    This helps build a comprehensive skills database from real job postings.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Clean job title to use as career name
    career_name = job_title.strip()
    
    for skill in skills:
        skill = skill.strip().lower()
        if skill and len(skill) > 1:  # Avoid single characters
            # Check if this skill-career combination already exists
            c.execute("SELECT id FROM skills WHERE career = ? AND skill = ?", (career_name, skill))
            if not c.fetchone():
                c.execute("INSERT INTO skills (career, skill) VALUES (?, ?)", (career_name, skill))
    
    conn.commit()
    conn.close()

def get_skill_frequency() -> Dict[str, int]:
    """
    Get the frequency of each skill across all careers.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT skill, COUNT(*) as frequency FROM skills GROUP BY skill ORDER BY frequency DESC")
    skill_freq = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return skill_freq

def get_career_skill_matrix() -> Dict[str, List[str]]:
    """
    Get a matrix of careers and their skills.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT career, GROUP_CONCAT(skill) FROM skills GROUP BY career")
    matrix = {}
    for row in c.fetchall():
        career, skills_str = row
        skills = skills_str.split(",") if skills_str else []
        matrix[career] = skills
    conn.close()
    return matrix

def search_careers_by_skills(user_skills: List[str], min_match: int = 1) -> List[Dict[str, Any]]:
    """
    Search for careers that match user skills.
    Returns careers with match count and matching skills.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Convert skills to lowercase for matching
    user_skills_lower = [skill.lower() for skill in user_skills]
    
    # Get all careers and their skills
    c.execute("SELECT career, GROUP_CONCAT(skill) FROM skills GROUP BY career")
    matches = []
    
    for row in c.fetchall():
        career, skills_str = row
        career_skills = [skill.lower() for skill in skills_str.split(",")] if skills_str else []
        
        # Find matching skills
        matching_skills = [skill for skill in career_skills if skill in user_skills_lower]
        match_count = len(matching_skills)
        
        if match_count >= min_match:
            matches.append({
                'career': career,
                'match_count': match_count,
                'matching_skills': matching_skills,
                'total_skills': len(career_skills),
                'match_percentage': (match_count / len(career_skills)) * 100 if career_skills else 0
            })
    
    conn.close()
    
    # Sort by match count and percentage
    matches.sort(key=lambda x: (x['match_count'], x['match_percentage']), reverse=True)
    return matches

def populate_sample_data():
    """
    Populate the database with sample career skills data.
    """
    sample_data = {
        "Software Engineer": ["python", "javascript", "java", "sql", "git", "agile", "problem solving"],
        "Data Scientist": ["python", "r", "sql", "machine learning", "statistics", "pandas", "numpy"],
        "Frontend Developer": ["javascript", "html", "css", "react", "angular", "vue", "responsive design"],
        "Backend Developer": ["python", "java", "node.js", "sql", "api", "microservices", "docker"],
        "DevOps Engineer": ["docker", "kubernetes", "aws", "jenkins", "git", "linux", "ci/cd"],
        "Product Manager": ["project management", "agile", "scrum", "user research", "data analysis", "communication"],
        "UX Designer": ["user research", "wireframing", "prototyping", "figma", "user testing", "design thinking"],
        "Data Analyst": ["sql", "excel", "python", "tableau", "power bi", "statistics", "data visualization"],
        "Marketing Manager": ["digital marketing", "seo", "social media", "content marketing", "analytics", "strategy"],
        "Sales Representative": ["sales", "crm", "negotiation", "communication", "lead generation", "customer service"]
    }
    
    for career, skills in sample_data.items():
        add_career_skills(career, skills)
    
    print(f"Added {len(sample_data)} careers with skills to the database")

def export_to_json(filename: str = "career_skills.json"):
    """
    Export career skills data to JSON file.
    """
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT career, GROUP_CONCAT(skill) FROM skills GROUP BY career")
    
    data = {}
    for row in c.fetchall():
        career, skills_str = row
        skills = skills_str.split(",") if skills_str else []
        data[career] = skills
    
    conn.close()
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported career skills data to {filename}")

def import_from_json(filename: str = "career_skills.json"):
    """
    Import career skills data from JSON file.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for career, skills in data.items():
            add_career_skills(career, skills)
        
        print(f"Imported {len(data)} careers from {filename}")
    except FileNotFoundError:
        print(f"File {filename} not found")
    except Exception as e:
        print(f"Error importing data: {e}")

def test_career_skills_db():
    """
    Test the career skills database functionality.
    """
    print("Testing Career Skills Database...")
    
    # Initialize database
    init_db()
    print("Database initialized")
    
    # Add sample data
    populate_sample_data()
    
    # Test getting career skills
    careers = get_career_skills()
    print(f"Found {len(careers)} careers in database")
    
    # Test skill frequency
    skill_freq = get_skill_frequency()
    print(f"Top 5 most common skills: {list(skill_freq.items())[:5]}")
    
    # Test career search
    user_skills = ["python", "javascript", "sql"]
    matches = search_careers_by_skills(user_skills, min_match=2)
    print(f"Found {len(matches)} careers matching user skills")
    
    # Test adding job skills
    add_job_skills_from_scraper("Senior Python Developer", ["python", "django", "postgresql", "aws"])
    print("Added job skills from scraper")
    
    # Export data
    export_to_json()
    
    print("Career skills database test completed!")

if __name__ == "__main__":
    test_career_skills_db() 