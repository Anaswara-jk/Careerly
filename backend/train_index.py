# train_index.py (Generic for any job table, no job_description)
import sqlite3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import pickle

DB_PATH = "career_skills.db"
INDEX_PATH = "job_index.faiss"
META_PATH = "job_metadata.pkl"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def detect_or_create_table():
    """Detect the first suitable job table or create career_skills if missing."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    
    # Prefer career_skills, then job_training_data, else pick first table
    if "career_skills" in tables:
        table_name = "career_skills"
    elif "job_training_data" in tables:
        table_name = "job_training_data"
    elif tables:
        table_name = tables[0]
        print(f"Using table {table_name} as job table")
    else:
        raise RuntimeError("No tables found in database!")

    # Create career_skills if missing but job_training_data exists
    if "career_skills" not in tables and "job_training_data" in tables:
        print("Creating career_skills table and populating from job_training_data...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS career_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                career_title TEXT,
                skills TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO career_skills (career_title, skills)
            SELECT career_title, skills     
            FROM job_training_data
        """)
        conn.commit()
        table_name = "career_skills"

    conn.close()
    return table_name

def fetch_jobs_from_db():
    table_name = detect_or_create_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Fetch id, title, skills           
    cursor.execute(f"SELECT id, career_title, skills FROM {table_name}")
    jobs = cursor.fetchall()
    conn.close()
    return jobs

def build_index():
    model = SentenceTransformer(EMBEDDING_MODEL)
    jobs = fetch_jobs_from_db()
    
    if not jobs:
        raise RuntimeError("No jobs found in database to index!")

    # Combine title + skills only
    texts = [
        f"{career_title} {' '.join(skills.split(',')) if isinstance(skills, str) else skills}" 
        for _, career_title, skills in jobs
    ]

    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity
    index.add(embeddings)
    
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(jobs, f)
    
    print(f"FAISS index built with {len(jobs)} jobs from {DB_PATH}")

if __name__ == "__main__":
    build_index()
