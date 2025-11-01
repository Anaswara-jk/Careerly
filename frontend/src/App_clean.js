import React, { useState } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import Chatbot from './components/Chatbot';
import './App.css';

const API_BASE_URL = 'http://localhost:8007';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [parsedData, setParsedData] = useState(null);
  const [careerSuggestions, setCareerSuggestions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [appMode, setAppMode] = useState('home'); // 'home', 'chat', 'resume'

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && (file.type === 'application/pdf' || file.name.endsWith('.docx'))) {
      setSelectedFile(file);
      setUploadStatus('');
      setParsedData(null);
      setCareerSuggestions(null);
      setCurrentStep(1);
    } else {
      setUploadStatus('Please select a PDF or DOCX file');
    }
  };

  const uploadResume = async () => {
    if (!selectedFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await axios.post(`${API_BASE_URL}/upload_resume/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setUploadStatus('Resume uploaded successfully!');
      setCurrentStep(2);
      await parseResume(selectedFile.name);
    } catch (error) {
      setUploadStatus(`Upload failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const parseResume = async (filename) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/parse_resume/`, null, {
        params: { filename }
      });
      setParsedData(response.data);
      setCurrentStep(3);
      await getCareerSuggestions(filename);
    } catch (error) {
      setUploadStatus(`Parsing failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getCareerSuggestions = async (filename) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/suggest_careers/`, null, {
        params: { filename }
      });
      setCareerSuggestions(response.data);
      setCurrentStep(4);
    } catch (error) {
      setUploadStatus(`Career suggestion failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const resetApp = () => {
    setSelectedFile(null);
    setUploadStatus('');
    setParsedData(null);
    setCareerSuggestions(null);
    setCurrentStep(1);
  };

  return (
    <div className="App">
      {appMode === 'home' && (
        <>
          <header className="app-header">
            <motion.h1 
              initial={{ opacity: 0, y: -50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              🤖 AI-Based Career Guidance System
            </motion.h1>
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.8 }}
            >
              Get personalized career recommendations through AI-powered chatbot guidance or resume analysis
            </motion.p>
          </header>

          <div className="mode-selection">
            <motion.div
              initial={{ opacity: 0, x: -50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
              className="mode-card"
              onClick={() => setAppMode('chat')}
            >
              <div className="mode-icon">💬</div>
              <h3>Interactive Career Chat</h3>
              <p>Talk with our AI assistant to discover careers based on your interests, skills, and goals</p>
              <div className="mode-features">
                <span>✓ Personalized Q&A</span>
                <span>✓ Interest Analysis</span>
                <span>✓ Market Trends</span>
              </div>
              <button className="mode-btn">Start Chat Guidance</button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 }}
              className="mode-card"
              onClick={() => setAppMode('resume')}
            >
              <div className="mode-icon">📄</div>
              <h3>Resume Analysis</h3>
              <p>Upload your resume for detailed skill extraction and AI-powered career matching</p>
              <div className="mode-features">
                <span>✓ Skill Extraction</span>
                <span>✓ ML Predictions</span>
                <span>✓ Detailed Analysis</span>
              </div>
              <button className="mode-btn">Upload Resume</button>
            </motion.div>
          </div>
        </>
      )}

      {appMode === 'chat' && (
        <div className="chat-mode">
          <div className="mode-header">
            <button className="back-btn" onClick={() => setAppMode('home')}>← Back to Home</button>
            <h2>🤖 AI Career Guidance Chat</h2>
          </div>
          <Chatbot onResumeUploadRequest={() => setAppMode('resume')} />
        </div>
      )}

      {appMode === 'resume' && (
        <>
          <header className="app-header">
            <div className="mode-header">
              <button className="back-btn" onClick={() => setAppMode('home')}>← Back to Home</button>
              <motion.h1 
                initial={{ opacity: 0, y: -50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
              >
                📄 Resume Analysis
              </motion.h1>
            </div>
            <motion.p 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.8 }}
            >
              Upload your resume for detailed analysis and career recommendations
            </motion.p>
          </header>

          <div className="progress-bar">
            {[1, 2, 3, 4].map((step) => (
              <div 
                key={step} 
                className={`progress-step ${currentStep >= step ? 'active' : ''}`}
              >
                {step}
              </div>
            ))}
          </div>

          <main className="main-content">
            <AnimatePresence mode="wait">
              {currentStep === 1 && (
                <motion.div
                  key="upload"
                  initial={{ opacity: 0, x: -100 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 100 }}
                  className="upload-section"
                >
                  <div className="upload-card">
                    <h2>📄 Upload Your Resume</h2>
                    <div className="file-input-wrapper">
                      <input
                        type="file"
                        accept=".pdf,.docx,.doc"
                        onChange={handleFileSelect}
                        id="file-input"
                        className="file-input"
                      />
                      <label htmlFor="file-input" className="file-input-label">
                        {selectedFile ? selectedFile.name : 'Choose PDF or DOCX file'}
                      </label>
                    </div>
                    
                    {selectedFile && (
                      <motion.button
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={uploadResume}
                        disabled={loading}
                        className="upload-btn"
                      >
                        {loading ? '⏳ Processing...' : '🚀 Analyze Resume'}
                      </motion.button>
                    )}
                    
                    {uploadStatus && (
                      <motion.p 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className={`status ${uploadStatus.includes('failed') ? 'error' : 'success'}`}
                      >
                        {uploadStatus}
                      </motion.p>
                    )}
                  </div>
                </motion.div>
              )}

              {currentStep >= 2 && parsedData && (
                <motion.div
                  key="parsed"
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="parsed-section"
                >
                  <div className="parsed-card">
                    <h2>📊 Extracted Information</h2>
                    
                    <div className="info-grid">
                      <div className="info-item">
                        <h3>🎯 Skills ({parsedData.skills?.length || 0})</h3>
                        <div className="skills-container">
                          {parsedData.skills?.map((skill, index) => (
                            <motion.span
                              key={index}
                              initial={{ opacity: 0, scale: 0 }}
                              animate={{ opacity: 1, scale: 1 }}
                              transition={{ delay: index * 0.1 }}
                              className="skill-tag"
                            >
                              {skill}
                            </motion.span>
                          ))}
                        </div>
                      </div>

                      <div className="info-item">
                        <h3>🎓 Education</h3>
                        <div className="education-list">
                          {parsedData.education?.map((edu, index) => (
                            <div key={index} className="education-item">
                              {edu}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="info-item">
                        <h3>💼 Experience</h3>
                        <div className="experience-list">
                          {parsedData.experience?.map((exp, index) => (
                            <div key={index} className="experience-item">
                              {exp}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {currentStep >= 4 && careerSuggestions && (
                <motion.div
                  key="suggestions"
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="suggestions-section"
                >
                  <div className="suggestions-card">
                    <h2>🎯 Career Suggestions</h2>
                    <p className="method-info">
                      Method: {careerSuggestions.method_used} | 
                      Skills Analyzed: {careerSuggestions.skills_count} |
                      ML Model: {careerSuggestions.ml_available ? '✅' : '❌'}
                    </p>
                    
                    <div className="careers-grid">
                      {careerSuggestions.suggested_careers?.map((career, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -50 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.2 }}
                          whileHover={{ scale: 1.02, boxShadow: "0 8px 25px rgba(0,0,0,0.15)" }}
                          className="career-card"
                        >
                          <div className="career-rank">#{index + 1}</div>
                          <h3>{career}</h3>
                          <div className="career-match">
                            <div className="match-bar">
                              <div 
                                className="match-fill" 
                                style={{ width: `${Math.max(20, 100 - index * 15)}%` }}
                              ></div>
                            </div>
                            <span>{Math.max(20, 100 - index * 15)}% Match</span>
                          </div>
                        </motion.div>
                      ))}
                    </div>

                    <motion.button
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 1 }}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={resetApp}
                      className="reset-btn"
                    >
                      🔄 Analyze Another Resume
                    </motion.button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="loading-overlay"
              >
                <div className="loading-spinner"></div>
                <p>Processing your resume with AI...</p>
              </motion.div>
            )}
          </main>

          <footer className="app-footer">
            <p>Powered by AI & Dynamic Market Data</p>
          </footer>
        </>
      )}
    </div>
  );
}

export default App;
