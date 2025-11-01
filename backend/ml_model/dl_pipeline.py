import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Paths (backend/ml_model/ -> backend/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "job_index.faiss")
META_PATH = os.path.join(BASE_DIR, "job_metadata.pkl")
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class DLPipeline:
    def __init__(self):
        # Load embedding model
        print(f"Loading embedding model: {EMBEDDING_MODEL} ...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.index = None
        self.metadata = None
        self.load_index()

    def load_index(self):
        """Load FAISS index and metadata if available."""
        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            try:
                self.index = faiss.read_index(INDEX_PATH)
                with open(META_PATH, "rb") as f:
                    self.metadata = pickle.load(f)
                print(f"✅ Successfully loaded FAISS index and metadata")
                print(f"Loaded jobs: {len(self.metadata)}")
            except Exception as e:
                print(f"⚠️ Error loading FAISS index: {e}")
                self.index = None
                self.metadata = None
        else:
            print("⚠️ FAISS index or metadata not found.")
            self.index = None
            self.metadata = None

    def search_jobs(self, resume_text, top_n=5):
        """Search for top N matching jobs dynamically using FAISS."""
        if not self.index or not self.metadata:
            print("⚠️ FAISS index not available. Returning empty results dynamically.")
            return []

        # Encode resume text
        query_embedding = self.model.encode([resume_text], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding, top_n)

        # Convert resume text into a rough skill list (you can refine this)
        user_skills = [s.lower().strip() for s in resume_text.split()]

        results = []
        # Encode resume with normalized embeddings
        query_embedding = self.model.encode([resume_text], convert_to_numpy=True, normalize_embeddings=True)
        scores, indices = self.index.search(query_embedding, top_n)

        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            job = self.metadata[idx]

            if isinstance(job, tuple):
                _, title, skills = job
                skills_list = skills.split(",") if isinstance(skills, str) else skills
            elif isinstance(job, dict):
                title = job.get("career_title", "Unknown")
                skills_list = job.get("skills", [])
            else:
                title, skills_list = "Unknown", []

            # Cosine similarity score is already in [0, 1] if normalized embeddings used
            confidence = float(score * 100)  # multiply by 100 for percentage

            results.append({
                "title": title,
                "skills": skills_list,
                "score": float(score),
                "confidence": round(confidence, 1)
            })





        return results


# Quick test
if __name__ == "__main__":
    pipeline = DLPipeline()
    test_resume = "I love working with data, Python, and machine learning"
    matches = pipeline.search_jobs(test_resume)
    print("Top job matches:")
    for job in matches:
        print(f"{job['title']} | Skills: {job['skills']} | Score: {job['score']:.3f}")
