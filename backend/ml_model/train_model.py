#!/usr/bin/env python3
"""
Train ML model for career prediction using Naukri.com data
"""
import sys
import os
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_career_skills
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import numpy as np
import pandas as pd

# Path to the database
DB_PATH = os.path.join(os.path.dirname(__file__), "../career_skills.db")

def load_data_from_db():
    """Load career-skills data from SQLite database"""
    print("Loading data from Naukri.com database...")
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT career_title, skills FROM career_skills")
    rows = c.fetchall()
    conn.close()
    
    careers = []
    skills_lists = []
    
    for career_title, skills_str in rows:
        if skills_str and len(skills_str.strip()) > 0:
            # Clean and process skills
            skills_list = [skill.strip().lower() for skill in skills_str.split(",") if skill.strip()]
            if len(skills_list) > 5:  # Only include careers with sufficient skills
                careers.append(career_title)
                skills_lists.append(" ".join(skills_list))  # Join skills as text for TF-IDF
    
    print(f"Loaded {len(careers)} career records")
    return skills_lists, careers

def train_model():
    """Train ML model for career prediction"""
    print("Starting ML model training...")
    
    # Load data
    X_text, y = load_data_from_db()
    
    if len(X_text) < 10:
        print("Error: Not enough data to train model. Need at least 10 career records.")
        return False
    
    # Convert text skills to TF-IDF features
    print("Converting skills to TF-IDF features...")
    vectorizer = TfidfVectorizer(
        max_features=1000,  # Top 1000 most important skills
        ngram_range=(1, 2),  # Include single words and bigrams
        min_df=2,  # Skill must appear in at least 2 careers
        max_df=0.8  # Ignore skills that appear in >80% of careers
    )
    
    X = vectorizer.fit_transform(X_text)
    
    # Encode career labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    print(f"Feature matrix shape: {X.shape}")
    print(f"Number of unique careers: {len(label_encoder.classes_)}")
    
    # Split data - remove stratification since each career appears only once
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )
    
    # Train Random Forest model
    print("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate model
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Model Accuracy: {accuracy:.3f}")
    print("\nTop 10 Most Important Features (Skills):")
    
    # Get feature importance
    feature_names = vectorizer.get_feature_names_out()
    importances = model.feature_importances_
    top_indices = np.argsort(importances)[-10:][::-1]
    
    for i, idx in enumerate(top_indices):
        print(f"{i+1}. {feature_names[idx]}: {importances[idx]:.4f}")
    
    # Save model and components
    print("Saving model...")
    model_data = {
        'model': model,
        'vectorizer': vectorizer,
        'label_encoder': label_encoder,
        'accuracy': accuracy,
        'feature_names': feature_names
    }
    
    joblib.dump(model_data, 'career_model.joblib')
    print("Model saved as 'career_model.joblib'")
    
    # Print sample predictions
    print("\nSample Predictions:")
    sample_size = min(5, X_test.shape[0])  # Use shape[0] instead of len() for sparse arrays
    sample_indices = np.random.choice(X_test.shape[0], sample_size, replace=False)
    for idx in sample_indices:
        actual_career = label_encoder.inverse_transform([y_test[idx]])[0]
        predicted_career = label_encoder.inverse_transform([y_pred[idx]])[0]
        print(f"Actual: {actual_career}")
        print(f"Predicted: {predicted_career}")
        print(f"Match: {'✓' if actual_career == predicted_career else '✗'}")
        print("-" * 50)
    
    return True

def test_model_prediction(skills_text):
    """Test the trained model with sample skills"""
    try:
        # Load the trained model
        model_data = joblib.load('career_model.joblib')
        model = model_data['model']
        vectorizer = model_data['vectorizer']
        label_encoder = model_data['label_encoder']
        
        # Transform input skills
        X_test = vectorizer.transform([skills_text])
        
        # Get prediction probabilities
        probabilities = model.predict_proba(X_test)[0]
        
        # Get top 3 predictions
        top_indices = np.argsort(probabilities)[-3:][::-1]
        
        print(f"\nPredictions for skills: '{skills_text}'")
        print("-" * 50)
        
        for i, idx in enumerate(top_indices):
            career = label_encoder.inverse_transform([idx])[0]
            confidence = probabilities[idx]
            print(f"{i+1}. {career}: {confidence:.3f}")
        
    except FileNotFoundError:
        print("Model not found. Please train the model first.")

if __name__ == "__main__":
    # Train the model
    success = train_model()
    
    if success:
        print("\n" + "="*60)
        print("MODEL TRAINING COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        # Test with sample skills
        print("\nTesting model with sample skills...")
        test_samples = [
            "python javascript sql git software development",
            "marketing communication social media campaign management",
            "patient care medical knowledge healthcare nursing",
            "accounting excel financial analysis budgeting"
        ]
        
        for sample in test_samples:
            test_model_prediction(sample)
    else:
        print("Model training failed!")
        exit(1)
