#!/usr/bin/env python3
"""
AI-Based Career Guidance Chatbot Service
Provides interactive career guidance through natural language processing
"""
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from db import get_career_skills, get_career_count
import random

class CareerGuidanceChatbot:
    def __init__(self):
        self.conversation_state = {}
        self.user_profiles = {}
        self.guidance_flow = {
            'greeting': self.handle_greeting,
            'interests': self.handle_interests,
            'skills': self.handle_skills,
            'academic_background': self.handle_academic_background,
            'career_goals': self.handle_career_goals,
            'experience_level': self.handle_experience_level,
            'experience_level': self.handle_experience_level,
            'recommendations': self.generate_recommendations,
            'followup': self.handle_followup
        }
        
    def start_conversation(self, user_id: str) -> Dict[str, Any]:
        """Initialize a new conversation with a user"""
        self.conversation_state[user_id] = {
            'stage': 'greeting',
            'collected_data': {},
            'conversation_history': [],
            'timestamp': datetime.now().isoformat()
        }
        
        return self.handle_greeting(user_id, "")
    
    def process_message(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process user message and return appropriate response"""
        if user_id not in self.conversation_state:
            return self.start_conversation(user_id)
        
        # Add user message to history
        self.conversation_state[user_id]['conversation_history'].append({
            'sender': 'user',
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Get current stage and process message
        current_stage = self.conversation_state[user_id]['stage']
        handler = self.guidance_flow.get(current_stage, self.handle_general_query)
        
        response = handler(user_id, message)
        
        # Add bot response to history
        self.conversation_state[user_id]['conversation_history'].append({
            'sender': 'bot',
            'message': response['message'],
            'timestamp': datetime.now().isoformat()
        })
        
        return response
    
    def handle_greeting(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle initial greeting and introduction"""
        greeting_messages = [
            "Hello! 👋 I'm your AI Career Guidance Assistant. I'm here to help you discover exciting career paths that match your interests, skills, and goals!",
            "Hi there! 🌟 Welcome to your personalized career guidance session. I'll ask you some questions to understand your background and provide tailored career recommendations.",
            "Greetings! 🚀 I'm excited to help you explore career opportunities that align with your unique profile. Let's start this journey together!"
        ]
        
        response_message = random.choice(greeting_messages)
        response_message += "\n\nTo get started, could you tell me about your main interests? For example:\n• Technology and programming\n• Business and entrepreneurship\n• Creative arts and design\n• Healthcare and medicine\n• Education and research\n• Or anything else you're passionate about!"
        
        # Move to next stage
        self.conversation_state[user_id]['stage'] = 'interests'
        
        return {
            'message': response_message,
            'stage': 'interests',
            'suggestions': ['Technology', 'Business', 'Creative Arts', 'Healthcare', 'Education', 'Science'],
            'progress': 10
        }
    
    def handle_interests(self, user_id: str, message: str) -> Dict[str, Any]:
        """Extract and process user interests"""
        interests = self.extract_interests(message)
        self.conversation_state[user_id]['collected_data']['interests'] = interests
        
        response_message = f"Great! I can see you're interested in: {', '.join(interests)}. 🎯\n\n"
        response_message += "Now, let's talk about your skills! What are you good at or what technical/professional skills do you have? This could include:\n"
        response_message += "• Programming languages (Python, Java, etc.)\n"
        response_message += "• Software tools (Excel, Photoshop, etc.)\n"
        response_message += "• Soft skills (Communication, Leadership, etc.)\n"
        response_message += "• Any certifications or specialized knowledge\n\n"
        response_message += "Please share whatever skills you have, even if you think they're basic!"
        
        self.conversation_state[user_id]['stage'] = 'skills'
        
        return {
            'message': response_message,
            'stage': 'skills',
            'extracted_data': {'interests': interests},
            'progress': 25
        }
    
    def handle_skills(self, user_id: str, message: str) -> Dict[str, Any]:
        """Extract and process user skills"""
        skills = self.extract_skills_from_text(message)
        self.conversation_state[user_id]['collected_data']['skills'] = skills
        
        response_message = f"Excellent! I've identified these skills: {', '.join(skills[:8])}{'...' if len(skills) > 8 else ''}. 💪\n\n"
        response_message += "Tell me about your academic background:\n"
        response_message += "• What's your current education level? (High School, Bachelor's, Master's, etc.)\n"
        response_message += "• What field/major are you studying or did you study?\n"
        response_message += "• Any specific courses or subjects you particularly enjoyed?\n"
        response_message += "• Current GPA or academic performance (if comfortable sharing)"
        
        self.conversation_state[user_id]['stage'] = 'academic_background'
        
        return {
            'message': response_message,
            'stage': 'academic_background',
            'extracted_data': {'skills': skills},
            'progress': 40
        }
    
    def handle_academic_background(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process academic background information"""
        academic_info = self.extract_academic_info(message)
        self.conversation_state[user_id]['collected_data']['academic_background'] = academic_info
        
        response_message = "Thanks for sharing your academic background! 🎓\n\n"
        response_message += "Now, let's discuss your career aspirations:\n"
        response_message += "• What type of work environment appeals to you? (Corporate, Startup, Remote, etc.)\n"
        response_message += "• Are you looking for immediate job opportunities or long-term career planning?\n"
        response_message += "• Any specific companies or industries you're interested in?\n"
        response_message += "• What's most important to you in a career? (Salary, Work-life balance, Growth, Impact, etc.)"
        
        self.conversation_state[user_id]['stage'] = 'career_goals'
        
        return {
            'message': response_message,
            'stage': 'career_goals',
            'extracted_data': {'academic_background': academic_info},
            'progress': 60
        }
    
    def handle_career_goals(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process career goals and preferences"""
        career_goals = self.extract_career_preferences(message)
        self.conversation_state[user_id]['collected_data']['career_goals'] = career_goals
        
        response_message = "Perfect! I'm getting a clear picture of what you're looking for. 🎯\n\n"
        response_message += "One more question - what's your current experience level?\n"
        response_message += "• Fresh graduate/student with no work experience\n"
        response_message += "• Some internship or part-time work experience\n"
        response_message += "• 1-3 years of professional experience\n"
        response_message += "• 3+ years of experience looking for career change\n"
        response_message += "• Other (please specify)"
        
        self.conversation_state[user_id]['stage'] = 'experience_level'
        
        return {
            'message': response_message,
            'stage': 'experience_level',
            'extracted_data': {'career_goals': career_goals},
            'progress': 80
        }
    
    def handle_experience_level(self, user_id: str, message: str) -> Dict[str, Any]:
        """Process experience level information"""
        experience_level = self.extract_experience_level(message)
        self.conversation_state[user_id]['collected_data']['experience_level'] = experience_level
        
        response_message = "Excellent! I now have all the information I need. 🚀\n\n"
        response_message += "Let me analyze your profile and generate personalized career recommendations based on:\n"
        response_message += f"✓ Your interests: {', '.join(self.conversation_state[user_id]['collected_data'].get('interests', []))}\n"
        response_message += f"✓ Your skills: {len(self.conversation_state[user_id]['collected_data'].get('skills', []))} identified skills\n"
        response_message += f"✓ Academic background and career goals\n"
        response_message += f"✓ Current market trends and in-demand skills\n\n"
        response_message += "Generating your personalized career roadmap... 🔄"
        
        self.conversation_state[user_id]['stage'] = 'recommendations'
        
        return {
            'message': response_message,
            'stage': 'recommendations',
            'extracted_data': {'experience_level': experience_level},
            'progress': 90,
            'action': 'generate_recommendations'
        }
    
    def generate_recommendations(self, user_id: str, message: str = "") -> Dict[str, Any]:
        """Generate personalized career recommendations"""
        user_data = self.conversation_state[user_id]['collected_data']
        
        # Get career recommendations based on collected data
        recommendations = self.get_personalized_careers(user_data)
        
        response_message = "🎉 Here are your personalized career recommendations:\n\n"
        
        for i, career in enumerate(recommendations[:5], 1):
            response_message += f"{i}. **{career['title']}**\n"
            response_message += f"   Match Score: {career['match_score']:.0%}\n"
            response_message += f"   Key Skills: {', '.join(career['key_skills'][:3])}\n"
            response_message += f"   Why it fits: {career['reasoning']}\n\n"
        
        response_message += "💡 **Next Steps:**\n"
        response_message += "• Would you like detailed information about any of these careers?\n"
        response_message += "• I can suggest specific skills to develop for your chosen path\n"
        response_message += "• Upload your resume for more detailed analysis\n"
        response_message += "• Get information about relevant courses and certifications\n\n"
        response_message += "What would you like to explore further?"
        
        self.conversation_state[user_id]['stage'] = 'followup'
        
        return {
            'message': response_message,
            'stage': 'followup',
            'recommendations': recommendations,
            'progress': 100,
            'actions': ['Career Details', 'Skill Development', 'Resume Analysis', 'Learning Path']
        }
    
    def handle_followup(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle follow-up questions and additional guidance"""
        if 'career details' in message.lower() or 'more about' in message.lower():
            return self.provide_career_details(user_id, message)
        elif 'skills' in message.lower() or 'develop' in message.lower():
            return self.suggest_skill_development(user_id, message)
        elif 'resume' in message.lower():
            return self.suggest_resume_analysis(user_id, message)
        elif 'courses' in message.lower() or 'learning' in message.lower():
            return self.suggest_learning_path(user_id, message)
        else:
            return self.handle_general_query(user_id, message)
    
    def extract_interests(self, text: str) -> List[str]:
        """Extract interests from user text using NLP"""
        interests = []
        text_lower = text.lower()
        
        # Interest categories mapping
        interest_keywords = {
            'technology': ['tech', 'programming', 'coding', 'software', 'computer', 'ai', 'machine learning', 'data'],
            'business': ['business', 'management', 'marketing', 'sales', 'finance', 'entrepreneurship'],
            'creative': ['creative', 'design', 'art', 'music', 'writing', 'photography', 'video'],
            'healthcare': ['health', 'medical', 'doctor', 'nurse', 'medicine', 'biology'],
            'education': ['teaching', 'education', 'training', 'academic', 'research'],
            'science': ['science', 'research', 'chemistry', 'physics', 'engineering'],
            'social': ['social', 'psychology', 'counseling', 'human resources', 'community']
        }
        
        for category, keywords in interest_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                interests.append(category.title())
        
        # Extract specific mentions
        specific_interests = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        interests.extend([interest for interest in specific_interests if len(interest) > 3])
        
        return list(set(interests)) if interests else ['General']
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract skills from user text"""
        from resume_parser import extract_skills
        return extract_skills(text) or ['Communication', 'Problem Solving']
    
    def extract_academic_info(self, text: str) -> Dict[str, str]:
        """Extract academic background information"""
        academic_info = {}
        text_lower = text.lower()
        
        # Education levels
        if any(term in text_lower for term in ['high school', 'secondary', '12th']):
            academic_info['level'] = 'High School'
        elif any(term in text_lower for term in ['bachelor', 'undergraduate', 'btech', 'bsc', 'ba']):
            academic_info['level'] = 'Bachelor\'s'
        elif any(term in text_lower for term in ['master', 'mtech', 'msc', 'mba', 'ma']):
            academic_info['level'] = 'Master\'s'
        elif any(term in text_lower for term in ['phd', 'doctorate']):
            academic_info['level'] = 'PhD'
        else:
            academic_info['level'] = 'Other'
        
        # Extract field/major
        fields = ['computer science', 'engineering', 'business', 'medicine', 'arts', 'science']
        for field in fields:
            if field in text_lower:
                academic_info['field'] = field.title()
                break
        
        return academic_info
    
    def extract_career_preferences(self, text: str) -> Dict[str, Any]:
        """Extract career preferences and goals"""
        preferences = {}
        text_lower = text.lower()
        
        # Work environment
        if any(term in text_lower for term in ['remote', 'work from home']):
            preferences['environment'] = 'Remote'
        elif any(term in text_lower for term in ['startup', 'small company']):
            preferences['environment'] = 'Startup'
        elif any(term in text_lower for term in ['corporate', 'large company']):
            preferences['environment'] = 'Corporate'
        
        # Priorities
        if 'salary' in text_lower or 'money' in text_lower:
            preferences['priority'] = 'Financial Growth'
        elif 'balance' in text_lower:
            preferences['priority'] = 'Work-Life Balance'
        elif 'growth' in text_lower or 'career' in text_lower:
            preferences['priority'] = 'Career Growth'
        elif 'impact' in text_lower or 'meaningful' in text_lower:
            preferences['priority'] = 'Social Impact'
        
        return preferences
    
    def extract_experience_level(self, text: str) -> str:
        """Extract experience level from user response"""
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['fresh', 'graduate', 'no experience', 'student']):
            return 'Entry Level'
        elif any(term in text_lower for term in ['internship', 'part-time']):
            return 'Some Experience'
        elif any(term in text_lower for term in ['1-3', '1 to 3', 'few years']):
            return 'Junior Level'
        elif any(term in text_lower for term in ['3+', 'experienced', 'senior']):
            return 'Senior Level'
        else:
            return 'Entry Level'
    
    def get_personalized_careers(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate personalized career recommendations based on user data"""
        career_skills_data = get_career_skills()
        user_skills = set(skill.lower() for skill in user_data.get('skills', []))
        user_interests = [interest.lower() for interest in user_data.get('interests', [])]
        
        career_matches = []
        
        for career_title, career_skills in career_skills_data:
            career_skills_set = set(skill.lower() for skill in career_skills)
            
            # Calculate skill match
            skill_overlap = len(user_skills & career_skills_set)
            skill_match_score = skill_overlap / max(len(user_skills), 1) if user_skills else 0
            
            # Calculate interest alignment
            interest_score = 0
            career_title_lower = career_title.lower()
            for interest in user_interests:
                if interest in career_title_lower:
                    interest_score += 0.3
            
            # Calculate overall match score
            overall_score = (skill_match_score * 0.7) + (interest_score * 0.3)
            
            if overall_score > 0.1:  # Minimum threshold
                career_matches.append({
                    'title': career_title,
                    'match_score': overall_score,
                    'skill_overlap': skill_overlap,
                    'key_skills': list(career_skills_set & user_skills) or career_skills[:3],
                    'reasoning': self.generate_reasoning(career_title, skill_overlap, user_interests)
                })
        
        # Sort by match score
        career_matches.sort(key=lambda x: x['match_score'], reverse=True)
        return career_matches[:10]
    
    def generate_reasoning(self, career_title: str, skill_overlap: int, interests: List[str]) -> str:
        """Generate reasoning for career recommendation"""
        reasons = []
        
        if skill_overlap > 0:
            reasons.append(f"You have {skill_overlap} relevant skills")
        
        career_lower = career_title.lower()
        for interest in interests:
            if interest in career_lower:
                reasons.append(f"Aligns with your {interest} interests")
        
        if 'engineer' in career_lower or 'developer' in career_lower:
            reasons.append("High demand in current job market")
        
        return "; ".join(reasons) if reasons else "Good match based on your profile"
    
    def provide_career_details(self, user_id: str, message: str) -> Dict[str, Any]:
        """Provide detailed information about specific careers"""
        return {
            'message': "I'd be happy to provide more details about any career! Which specific role would you like to know more about? I can share information about job responsibilities, required skills, salary ranges, and growth prospects.",
            'stage': 'followup',
            'progress': 100
        }
    
    def suggest_skill_development(self, user_id: str, message: str) -> Dict[str, Any]:
        """Suggest skills to develop for chosen career path"""
        return {
            'message': "Great question! Based on your chosen career path, I can suggest specific skills to develop. Which career from your recommendations interests you most? I'll provide a personalized skill development roadmap.",
            'stage': 'followup',
            'progress': 100
        }
    
    def suggest_resume_analysis(self, user_id: str, message: str) -> Dict[str, Any]:
        """Suggest resume analysis for detailed insights"""
        return {
            'message': "Excellent idea! Resume analysis can provide much deeper insights. You can upload your resume using the file upload feature, and I'll analyze it to provide more specific career recommendations and identify skill gaps.",
            'stage': 'followup',
            'progress': 100,
            'action': 'redirect_to_resume_upload'
        }
    
    def suggest_learning_path(self, user_id: str, message: str) -> Dict[str, Any]:
        """Suggest learning paths and courses"""
        return {
            'message': "I can definitely help with learning recommendations! Based on your career interests, I can suggest relevant courses, certifications, and learning platforms. Which specific area would you like to focus on?",
            'stage': 'followup',
            'progress': 100
        }
    
    def handle_general_query(self, user_id: str, message: str) -> Dict[str, Any]:
        """Handle general queries and provide helpful responses"""
        return {
            'message': "I'm here to help with your career guidance! You can ask me about:\n• Specific career paths and requirements\n• Skills you should develop\n• Educational recommendations\n• Job market trends\n• Resume analysis\n\nWhat would you like to know more about?",
            'stage': 'followup',
            'progress': 100
        }
    
    def get_conversation_summary(self, user_id: str) -> Dict[str, Any]:
        """Get summary of conversation and collected data"""
        if user_id not in self.conversation_state:
            return {}
        
        return {
            'user_id': user_id,
            'stage': self.conversation_state[user_id]['stage'],
            'collected_data': self.conversation_state[user_id]['collected_data'],
            'conversation_length': len(self.conversation_state[user_id]['conversation_history']),
            'timestamp': self.conversation_state[user_id]['timestamp']
        }
