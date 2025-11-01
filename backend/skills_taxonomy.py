# skills_taxonomy.py
from fuzzywuzzy import process
from db import get_career_skills

# Cache to avoid reloading skills from DB repeatedly
skills_cache = []

def refresh_skills_cache():
    """
    Refreshes the cached skills list from the database dynamically.
    Called by onet_sync during startup or scheduled syncs.
    """
    global skills_cache
    career_skills_data = get_career_skills()
    # Flatten and deduplicate all skills
    skills_cache = sorted(
        set(skill.strip().lower() for _, skills in career_skills_data for skill in skills if skill),
        key=lambda x: x.lower()
    )
    return skills_cache

def get_dynamic_skills_list():
    """
    Returns a dynamic list of all unique skills from cache (or DB if cache empty).
    """
    global skills_cache
    if not skills_cache:
        refresh_skills_cache()
    return skills_cache

def find_similar_skills(query, limit=5, score_cutoff=70):
    """
    Finds skills similar to the query using fuzzy matching against the dynamic skill list.
    Returns a list of (skill, score) tuples.
    """
    skills = get_dynamic_skills_list()
    if not query or not skills:
        return []
    results = process.extract(query.lower(), skills, limit=limit, scorer=process.fuzz.ratio)
    return [(skill, score) for skill, score in results if score >= score_cutoff]
