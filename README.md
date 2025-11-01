# AI Career Suggester

A powerful AI/ML-based application that analyzes resumes and suggests optimal career paths using O*NET occupational data and machine learning.

##  Features

- **Resume Parsing**: Extract skills, education, and experience from PDF/DOCX files
- **AI-Powered Analysis**: Uses NLP and machine learning for accurate skill extraction
- **O*NET Integration**: Leverages official U.S. Department of Labor occupational data
- **Dual Prediction Methods**: Content-based matching + ML classification
- **Modern UI**: Beautiful, responsive React frontend with animations
- **Real-time Processing**: Fast, efficient backend with FastAPI

##Architecture

```
├── backend/                 # Python FastAPI backend
│   ├── main.py             # Main API server
│   ├── resume_parser.py    # Resume parsing logic
│   ├── skills_taxonomy.py  # Dynamic skills extraction
│   ├── onet_sync.py        # O*NET data synchronization
│   ├── ml_model/           # Machine learning components
│   │   └── train_model.py  # ML model training
│   └── db.py              # Database operations
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main React component
│   │   └── App.css        # Modern styling
│   └── package.json       # Frontend dependencies
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Download spaCy language model**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. **Sync O*NET data** (downloads ~50MB):
   ```bash
   python onet_sync.py
   ```

5. **Train ML model**:
   ```bash
   mkdir ml_model
   cd ml_model
   python ../ml_model/train_model.py
   cd ..
   ```

6. **Start backend server**:
   ```bash
   python main.py
   ```
   Backend runs on: http://localhost:8000

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Start development server**:
   ```bash
   npm start
   ```
   Frontend runs on: http://localhost:3000

## API Endpoints

### Core Endpoints

- `POST /upload_resume/` - Upload resume file
- `POST /parse_resume/` - Extract information from resume
- `POST /suggest_careers/` - Get AI career suggestions
- `GET /health/` - Health check
- `GET /stats/` - System statistics

### Admin Endpoints

- `POST /sync_onet/` - Manually sync O*NET data

## How It Works

### 1. Resume Upload & Parsing
- Supports PDF and DOCX formats
- Extracts text using pdfplumber and python-docx
- Uses spaCy NLP for intelligent text processing

### 2. Skills Extraction
- **Dynamic Skills Database**: 1000+ skills from O*NET
- **Fuzzy Matching**: Handles variations and typos
- **Context-Aware**: Considers skill context and relevance

### 3. Career Matching
- **Content-Based**: Jaccard similarity with O*NET skills
- **ML Classification**: Random Forest trained on occupational data
- **Hybrid Approach**: Combines both methods for accuracy

### 4. O*NET Integration
- **Authoritative Data**: Official U.S. Department of Labor database
- **Multi-Source Skills**: Skills, Technology, Knowledge, Tools
- **Regular Updates**: Automated sync capability

## Configuration

### Environment Variables
```bash
# Optional: Custom O*NET database URL
ONET_URL=https://www.onetcenter.org/dl_files/database/db_29_3_text.zip

# Optional: Custom upload directory
UPLOAD_DIR=uploads

# Optional: Custom database path
DB_PATH=career_skills.db
```

### Model Configuration
- **ML Algorithm**: Random Forest Classifier
- **Feature Extraction**: TF-IDF Vectorization
- **Training Data**: O*NET occupational profiles
- **Accuracy**: Typically 75-85% on test data

## Performance

- **Resume Processing**: ~2-5 seconds
- **Career Suggestions**: ~1-3 seconds
- **Database Size**: ~50MB (923 occupations, 10,000+ skills)
- **Memory Usage**: ~200MB backend, ~100MB frontend

## Development

### Adding New Skills
Skills are automatically extracted from O*NET. To add custom skills:

1. Edit `skills_taxonomy.py`
2. Add to `CUSTOM_SKILLS` list
3. Restart backend

### Improving ML Model
1. Collect more training data
2. Experiment with different algorithms in `train_model.py`
3. Tune hyperparameters
4. Retrain model

### Frontend Customization
- Modify `App.js` for functionality changes
- Update `App.css` for styling changes
- Add new components in `src/components/`

## Troubleshooting

### Common Issues

**Backend won't start**:
- Check Python version (3.8+)
- Install all requirements: `pip install -r requirements.txt`
- Download spaCy model: `python -m spacy download en_core_web_sm`

**No career suggestions**:
- Ensure O*NET data is synced: `python onet_sync.py`
- Check if skills are extracted from resume
- Verify database has data: `python debug_db.py`

**ML model not found**:
- Train the model: `python ml_model/train_model.py`
- Check model file exists: `ml_model/career_model.joblib`

**Frontend connection issues**:
- Ensure backend is running on port 8000
- Check CORS settings in `main.py`
- Verify API_BASE_URL in `App.js`

### Debug Commands

```bash
# Check database contents
python debug_db.py

# Test O*NET sync
python onet_sync.py

# Verify API health
curl http://localhost:8000/health/

# Check system stats
curl http://localhost:8000/stats/
```

## Sample Usage

1. **Upload Resume**: Select PDF/DOCX file
2. **View Extracted Data**: Skills, education, experience
3. **Get Suggestions**: Top 5 career matches with confidence scores
4. **Analyze Results**: Method used, skills matched, accuracy

## Production Deployment

### Backend (FastAPI)
```bash
# Using Gunicorn
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker

# Using Docker
docker build -t career-backend .
docker run -p 8000:8000 career-backend
```

### Frontend (React)
```bash
# Build for production
npm run build

# Serve with nginx/apache
# Or deploy to Vercel/Netlify
```

## Data Sources

- **O*NET Database**: Official occupational data from U.S. Department of Labor
- **Skills Taxonomy**: 1000+ standardized skills across industries
- **Technology Skills**: Software, tools, and platforms by occupation
- **Knowledge Areas**: Domain-specific knowledge requirements

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **O*NET Program**: For providing comprehensive occupational data
- **U.S. Department of Labor**: For maintaining the O*NET database
- **Open Source Libraries**: FastAPI, React, scikit-learn, spaCy, and others

---


