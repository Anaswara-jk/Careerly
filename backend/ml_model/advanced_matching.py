# ml_model/advanced_matching.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any, Tuple
import joblib
import os
from backend.db import get_career_skills
from sklearn.feature_extraction.text import TfidfVectorizer
import re
from collections import defaultdict

class CareerMatcher:
    def __init__(self, model_path: str = "career_model.joblib"):
        """
        Initialize the AI-powered career matcher with pre-trained models and database connection
        """
        try:
            # Load ML model components
            self.model_data = joblib.load(model_path)
            self.vectorizer = self.model_data['vectorizer']
            self.label_encoder = self.model_data['label_encoder']
            self.model = self.model_data['model']
            
            # Load career skills from database
            self.career_skills = self._load_career_skills()
            self.skill_frequencies = self._calculate_skill_frequencies()
            
            # Initialize TF-IDF for skill matching
            self.skill_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,
                max_features=10000
            )
            self._initialize_skill_vectors()
            
        except Exception as e:
            raise ValueError(f"Failed to initialize CareerMatcher: {str(e)}")

    def _load_career_skills(self) -> Dict[str, List[str]]:
        """Load career skills from database into a dictionary"""
        career_skills = {}
        try:
            for career, skills in get_career_skills():
                career_skills[career.lower()] = [s.lower().strip() for s in skills]
        except Exception as e:
            print(f"Warning: Could not load career skills: {e}")
        return career_skills

    def _calculate_skill_frequencies(self) -> Dict[str, int]:
        """Calculate inverse document frequency for skills"""
        skill_counts = defaultdict(int)
        for skills in self.career_skills.values():
            for skill in set(skills):  # Count each skill only once per career
                skill_counts[skill] += 1
        return skill_counts

    def _initialize_skill_vectors(self):
        """Initialize TF-IDF vectors for skill matching"""
        if not self.career_skills:
            return
            
        # Create documents for each career (space-separated skills)
        documents = [' '.join(skills) for skills in self.career_skills.values()]
        self.skill_vectorizer.fit(documents)

    def calculate_relevance_scores(self, resume_text: str, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Calculate relevance scores between resume and all careers using ML model
        """
        if not resume_text.strip():
            return []
            
        try:
            # Transform resume text to TF-IDF features
            resume_tfidf = self.vectorizer.transform([resume_text])
            
            # Get prediction probabilities for all classes
            probabilities = self.model.predict_proba(resume_tfidf)[0]
            
            # Get top N careers with highest probabilities
            top_indices = np.argsort(probabilities)[-top_n:][::-1]
            
            results = []
            for idx in top_indices:
                career = self.label_encoder.inverse_transform([idx])[0]
                score = float(probabilities[idx])
                
                # Get skill match details
                career_skills = self.career_skills.get(career.lower(), [])
                skill_match = self._calculate_skill_match(resume_text, career_skills)
                
                results.append({
                    "career": career,
                    "relevance_score": score,
                    "confidence": self._get_confidence_level(score),
                    "skill_match": skill_match
                })
                
            return results
            
        except Exception as e:
            print(f"Error calculating relevance scores: {e}")
            return []

    def _calculate_skill_match(self, text: str, required_skills: List[str]) -> Dict[str, Any]:
        """
        Calculate detailed skill match between text and required skills
        """
        if not required_skills:
            return {
                "match_percentage": 0,
                "matched_skills": [],
                "missing_skills": required_skills,
                "total_required": 0
            }
            
        # Tokenize and clean text
        tokens = set(re.findall(r'\b\w+\b', text.lower()))
        
        # Find matched and missing skills
        matched = [s for s in required_skills if s.lower() in tokens]
        missing = [s for s in required_skills if s.lower() not in tokens]
        
        # Calculate match percentage with IDF weighting
        total_weight = sum(1.0 / (1 + np.log1p(self.skill_frequencies.get(s.lower(), 1))) 
                          for s in required_skills)
        matched_weight = sum(1.0 / (1 + np.log1p(self.skill_frequencies.get(s.lower(), 1))) 
                           for s in matched)
        
        match_percentage = (matched_weight / total_weight) if total_weight > 0 else 0
        
        return {
            "match_percentage": match_percentage,
            "matched_skills": matched,
            "missing_skills": missing,
            "total_required": len(required_skills)
        }

    def get_skill_match_analysis(self, resume_text: str, career_title: str) -> Dict[str, Any]:
        """
        Get detailed skill match analysis for a specific career
        """
        career_title_lower = career_title.lower()
        career_skills = self.career_skills.get(career_title_lower, [])
        
        if not career_skills:
            # Try to find similar career title
            similar_careers = self._find_similar_careers(career_title_lower)
            if similar_careers:
                career_title_lower = similar_careers[0]
                career_skills = self.career_skills.get(career_title_lower, [])
        
        skill_match = self._calculate_skill_match(resume_text, career_skills)
        
        return {
            "career": career_title_lower.title(),
            "skill_match": skill_match,
            "key_skills": career_skills[:10]  # Top 10 key skills
        }

    def _find_similar_careers(self, career: str, top_n: int = 3) -> List[str]:
        """Find similar career titles using fuzzy matching"""
        from fuzzywuzzy import process
        careers = list(self.career_skills.keys())
        matches = process.extract(career, careers, limit=top_n)
        return [match[0] for match in matches if match[1] > 70]  # Threshold of 70%

    def _get_confidence_level(self, score: float) -> str:
        """Convert numerical score to confidence level"""
        if score >= 0.9:
            return "Very High"
        elif score >= 0.7:
            return "High"
        elif score >= 0.5:
            return "Moderate"
        else:
            return "Low"

# Example usage
if __name__ == "__main__":
    try:
        # Initialize the matcher with the trained model
        matcher = CareerMatcher("career_model.joblib")
        
        # Example resume text
        resume_text = """
        Experienced Python developer with 5 years of web development.
        Skills: Python, Django, Flask, SQL, JavaScript, React, Docker, AWS.
        Education: BS in Computer Science.
        Worked on machine learning projects using scikit-learn and TensorFlow.
        """
        
        # Get top career matches
        print("Top Career Matches:")
        matches = matcher.calculate_relevance_scores(resume_text, top_n=3)
        
        for match in matches:
            print(f"\nCareer: {match['career']}")
            print(f"Relevance Score: {match['relevance_score']:.2f} ({match['confidence']} confidence)")
            print(f"Skill Match: {match['skill_match']['match_percentage']:.0%}")
            print(f"Matched Skills: {', '.join(match['skill_match']['matched_skills'][:5])}")
            
    except Exception as e:
        print(f"Error: {e}")