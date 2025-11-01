from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime
import os

Base = declarative_base()

# Define database models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(50), nullable=True)  # programming, soft_skills, etc.
    created_at = Column(DateTime, default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    application_url = Column(String(500), nullable=True)  # Direct application link
    salary = Column(String(100), nullable=True)
    posted_date = Column(String(100), nullable=True)
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract, etc.
    experience_level = Column(String(50), nullable=True)  # entry, mid, senior, etc.
    source = Column(String(50), nullable=False)  # indeed, linkedin, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    skills = relationship("Skill", secondary="job_skills", back_populates="jobs")

class JobSkill(Base):
    __tablename__ = "job_skills"
    
    job_id = Column(Integer, ForeignKey("jobs.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)

class Education(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    degree = Column(String(200), nullable=True)
    institution = Column(String(200), nullable=True)
    year = Column(String(10), nullable=True)
    gpa = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Experience(Base):
    __tablename__ = "experience"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200), nullable=True)
    company = Column(String(200), nullable=True)
    duration = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CareerRecommendation(Base):
    __tablename__ = "career_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    similarity_score = Column(Float, nullable=True)
    matching_skills = Column(Text, nullable=True)  # JSON string of matching skills
    missing_skills = Column(Text, nullable=True)   # JSON string of missing skills
    created_at = Column(DateTime, default=datetime.utcnow)

# Set up relationships
Skill.jobs = relationship("Job", secondary="job_skills", back_populates="skills")

class DatabaseManager:
    def __init__(self, db_url="sqlite:///./career_guidance.db"):
        self.engine = create_engine(db_url, echo=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Recreate tables to ensure schema is up to date
        self.recreate_tables()
    
    def recreate_tables(self):
        """Drop and recreate all tables to ensure schema is current."""
        try:
            # Drop all tables
            Base.metadata.drop_all(self.engine)
            # Create all tables
            Base.metadata.create_all(self.engine)
            print("Database tables recreated successfully!")
        except Exception as e:
            print(f"Error recreating tables: {e}")
    
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get a database session."""
        return self.SessionLocal()
    
    def add_user(self, user_data: dict):
        """Add a new user."""
        session = self.get_session()
        try:
            user = User(**user_data)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_skill(self, name: str, category: str = None):
        """Add a new skill."""
        session = self.get_session()
        try:
            # Check if skill already exists
            existing_skill = session.query(Skill).filter(Skill.name == name).first()
            if existing_skill:
                return existing_skill
            
            skill = Skill(name=name, category=category)
            session.add(skill)
            session.commit()
            session.refresh(skill)
            return skill
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_job(self, job_data: dict):
        """Add a new job."""
        session = self.get_session()
        try:
            # Check if job already exists
            existing_job = session.query(Job).filter(
                Job.title == job_data['title'],
                Job.company == job_data['company'],
                Job.source == job_data['source']
            ).first()
            
            if existing_job:
                return existing_job
            
            # Extract skills from job data
            skills_data = job_data.pop('skills_required', [])
            
            # Create job
            job = Job(**job_data)
            session.add(job)
            session.flush()  # Get the job ID
            
            # Add skills
            for skill_name in skills_data:
                if skill_name:
                    skill = self.add_skill(skill_name)
                    if skill:
                        job.skills.append(skill)
            
            session.commit()
            session.refresh(job)
            return job
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_jobs_by_skills(self, skills: list, limit: int = 20):
        """Get jobs that match the given skills."""
        session = self.get_session()
        try:
            # Find jobs that have any of the specified skills
            jobs = session.query(Job).join(Job.skills).filter(
                Skill.name.in_(skills)
            ).limit(limit).all()
            return jobs
        except Exception as e:
            raise e
        finally:
            session.close()
    
    def create_recommendations(self, user_id: int, jobs: list):
        """Create career recommendations for a user."""
        session = self.get_session()
        try:
            recommendations = []
            for job in jobs:
                # Calculate similarity score (simplified)
                similarity_score = 0.8  # Placeholder
                
                recommendation = CareerRecommendation(
                    user_id=user_id,
                    job_id=job.id,
                    similarity_score=similarity_score
                )
                session.add(recommendation)
                recommendations.append(recommendation)
            
            session.commit()
            return recommendations
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_database_stats(self):
        """Get database statistics."""
        session = self.get_session()
        try:
            user_count = session.query(User).count()
            job_count = session.query(Job).count()
            skill_count = session.query(Skill).count()
            
            return {
                'users': user_count,
                'jobs': job_count,
                'skills': skill_count
            }
        except Exception as e:
            raise e
        finally:
            session.close()

# Initialize database manager
db_manager = DatabaseManager()

def test_database():
    """Test the database functionality."""
    try:
        # Test adding a skill
        skill = db_manager.add_skill("python", "programming")
        print(f"Added skill: {skill.name}")
        
        # Test adding a job
        job_data = {
            'title': 'Python Developer',
            'company': 'Test Company',
            'location': 'Remote',
            'description': 'Python development role',
            'url': 'https://example.com',
            'application_url': 'https://example.com/apply',
            'source': 'test',
            'skills_required': ['python', 'django', 'sql']
        }
        job = db_manager.add_job(job_data)
        print(f"Added job: {job.title}")
        
        # Test getting database stats
        stats = db_manager.get_database_stats()
        print(f"Database stats: {stats}")
        
        print("Database test completed successfully!")
        
    except Exception as e:
        print(f"Database test failed: {e}")

if __name__ == "__main__":
    test_database() 