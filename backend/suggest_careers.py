'''
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
import torch.nn as nn
from resume_parser import parse_resume  # Your parser script

INDEX_PATH = "job_index.faiss"
META_PATH = "job_metadata.pkl"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Simple ranker (optional, can be trained)
class Ranker(nn.Module):
    def __init__(self, input_dim=384):  # MiniLM output dim
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, 1)

    def forward(self, x):
        return torch.sigmoid(self.fc2(self.relu(self.fc1(x))))


def suggest_careers(resume_path, top_k=5):
    # Load FAISS index & metadata
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        jobs = pickle.load(f)

    model = SentenceTransformer(EMBEDDING_MODEL)

    # Parse resume
    resume_data = parse_resume(resume_path)
    print("Resume Data:", resume_data)

    # Combine all relevant text fields to form a full resume string
    resume_text_parts = []

    if "skills" in resume_data:
        resume_text_parts.append(" ".join(resume_data["skills"]))
    if "education" in resume_data:
        resume_text_parts.append(" ".join(resume_data["education"]))
    if "experience" in resume_data:
        for exp in resume_data["experience"]:
            resume_text_parts.append(" ".join(str(v) for v in exp.values()))

    resume_text = " ".join(resume_text_parts)
    skills = resume_data.get("skills", [])


    print("Extracted Text:", resume_text[:200])
    print("Skills:", skills)

    if not resume_text:
        # Return empty structure instead of list
        return {
            "method_used": "Error",
            "skills_count": len(skills),
            "suggested_careers": []
        }

    # Embed resume
    resume_embedding = model.encode([resume_text], normalize_embeddings=True)
    resume_embedding = np.array(resume_embedding, dtype="float32")

    # FAISS search
    scores, idxs = index.search(resume_embedding, top_k)
    scores, idxs = scores[0], idxs[0]

    results = []
    for i, idx in enumerate(idxs):
        if 0 <= idx < len(jobs):
            job = jobs[idx]
            title = job.get("title", "Unknown") if isinstance(job, dict) else str(job)
            skills_list = job.get("skills", []) if isinstance(job, dict) else []
            results.append({
                "title": title,
                "skills": skills_list,
                "faiss_score": float(scores[i])
            })

    return {
        "method_used": "FAISS Search",
        "skills_count": len(skills),
        "suggested_careers": results
    }



# ----------------- Test -----------------
if __name__ == "__main__":
    careers = suggest_careers("uploads/sample_resume.pdf", top_k=3)
    for c in careers:
        print(c)
'''
import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from resume_parser import parse_resume  # your parser

INDEX_PATH = "job_index.faiss"
META_PATH = "job_metadata.pkl"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def suggest_careers(resume_path, top_k=5):
    # Load FAISS index and job metadata
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        jobs = pickle.load(f)

    model = SentenceTransformer(EMBEDDING_MODEL)

    # Parse resume data
    resume_data = parse_resume(resume_path)
    print("\n📄 Parsed Resume Data:", resume_data)

    # Build a combined text for embedding
    resume_text_parts = []

    # Get fields from parsed data
    skills = resume_data.get("skills", [])
    education = resume_data.get("education", [])
    experience = resume_data.get("experience", [])

    if isinstance(skills, list):
        resume_text_parts.append(" ".join(skills))
    elif isinstance(skills, str):
        resume_text_parts.append(skills)

    if isinstance(education, list):
        resume_text_parts.append(" ".join(education))
    elif isinstance(education, str):
        resume_text_parts.append(education)

    if isinstance(experience, list):
        for exp in experience:
            if isinstance(exp, dict):
                resume_text_parts.append(" ".join(str(v) for v in exp.values()))
            else:
                resume_text_parts.append(str(exp))
    elif isinstance(experience, str):
        resume_text_parts.append(experience)

    resume_text = " ".join(resume_text_parts)
    print("\n🧠 Final Resume Text (first 200 chars):", resume_text[:200])

    print("\n🚨 DEBUG: resume_text length =", len(resume_text))
    print("🚨 DEBUG: sample resume_text:", resume_text[:300])
    if not resume_text.strip():
        return {
            "method_used": "Error",
            "skills_count": len(skills),
            "suggested_careers": []
        }

    # If no text, return error result
    if not resume_text.strip():
        return {
            "method_used": "Error",
            "skills_count": len(resume_data.get("skills", [])),
            "suggested_careers": []
        }

    # Embed the resume
    resume_embedding = model.encode([resume_text], normalize_embeddings=True)
    resume_embedding = np.array(resume_embedding, dtype="float32")

    # Search FAISS index
    scores, idxs = index.search(resume_embedding, top_k)
    scores, idxs = scores[0], idxs[0]

    # Collect top career suggestions
    results = []
    for i, idx in enumerate(idxs):
        if 0 <= idx < len(jobs):
            job = jobs[idx]
            if isinstance(job, dict):
                title = job.get("title", "Unknown")
                skills_list = job.get("skills", [])
            else:
                title = str(job)
                skills_list = []

            results.append({
                "title": title,
                "skills": skills_list,
                "faiss_score": float(scores[i])
            })

    # Return final result
    return {
        "method_used": "FAISS Search",
        "skills_count": len(resume_data.get("skills", [])),
        "suggested_careers": results
    }


# ----------------- Test -----------------
if __name__ == "__main__":
    careers = suggest_careers("uploads/Priya Nair.pdf", top_k=3)
    print("\n🎯 Final Career Suggestions:")
    for c in careers["suggested_careers"]:
        print("-", c["title"], "| Score:", round(c["faiss_score"], 3))

