// import React, { useState } from 'react';
// import axios from 'axios';
// import { motion, AnimatePresence } from 'framer-motion';
// import Chatbot from './components/Chatbot';
// import './App.css';

// const API_BASE_URL = 'http://localhost:8000';

// function App() {
//   const [selectedFile, setSelectedFile] = useState(null);
//   const [uploadStatus, setUploadStatus] = useState('');
//   const [parsedData, setParsedData] = useState(null);
//   const [careerSuggestions, setCareerSuggestions] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [currentStep, setCurrentStep] = useState(1);
//   const [appMode, setAppMode] = useState('home'); // 'home', 'chat', 'resume'

//   const handleFileSelect = (event) => {
//     const file = event.target.files[0];
//     if (file && (file.type === 'application/pdf' || file.name.endsWith('.docx'))) {
//       setSelectedFile(file);
//       setUploadStatus('');
//       setParsedData(null);
//       setCareerSuggestions(null);
//       setCurrentStep(1);
//     } else {
//       setUploadStatus('Please select a PDF or DOCX file');
//     }
//   };

//   const uploadResume = async () => {
//     if (!selectedFile) return;

//     setLoading(true);
//     const formData = new FormData();
//     formData.append('file', selectedFile);

//     try {
//       await axios.post(`${API_BASE_URL}/upload_resume`, formData, {
//         headers: { 'Content-Type': 'multipart/form-data' }
//       });
//       setUploadStatus('Resume uploaded successfully!');
//       setCurrentStep(2);
//       await parseResume(selectedFile.name);
//     } catch (error) {
//       setUploadStatus(`Upload failed: ${error.response?.data?.detail || error.message}`);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const parseResume = async (filename) => {
//     setLoading(true);
//     try {
//       const response = await axios.get(`${API_BASE_URL}/parse_resume/`, {
//         params: { filename }
//       });
//       setParsedData(response.data);
//       setCurrentStep(3);
//       await getCareerSuggestions(filename);
//     } catch (error) {
//       setUploadStatus(`Parsing failed: ${error.response?.data?.detail || error.message}`);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const getCareerSuggestions = async (filename) => {
//     setLoading(true);
//     try {
//       const response = await axios.post(`${API_BASE_URL}/suggest_careers/`, null, {
//         params: { filename }
//       });
//       setCareerSuggestions(response.data);
//       setCurrentStep(4);
//     } catch (error) {
//       setUploadStatus(`Career suggestion failed: ${error.response?.data?.detail || error.message}`);
//     } finally {
//       setLoading(false);
//     }
//   };

//   const resetApp = () => {
//     setSelectedFile(null);
//     setUploadStatus('');
//     setParsedData(null);
//     setCareerSuggestions(null);
//     setCurrentStep(1);
//   };

//   return (
//     <div className="App">
//       {appMode === 'home' && (
//         <>
//           <header className="app-header">
//             <motion.h1 
//               initial={{ opacity: 0, y: -50 }}
//               animate={{ opacity: 1, y: 0 }}
//               transition={{ duration: 0.8 }}
//             >
//               🤖 AI-Based Career Guidance System
//             </motion.h1>
//             <motion.p 
//               initial={{ opacity: 0 }}
//               animate={{ opacity: 1 }}
//               transition={{ delay: 0.3, duration: 0.8 }}
//             >
//               Get personalized career recommendations through AI-powered chatbot guidance or resume analysis
//             </motion.p>
//           </header>

//           <div className="mode-selection">
//             <motion.div
//               initial={{ opacity: 0, x: -50 }}
//               animate={{ opacity: 1, x: 0 }}
//               transition={{ delay: 0.5 }}
//               className="mode-card"
//               onClick={() => setAppMode('chat')}
//             >
//               <div className="mode-icon">💬</div>
//               <h3>Interactive Career Chat</h3>
//               <p>Talk with our AI assistant to discover careers based on your interests, skills, and goals</p>
//               <div className="mode-features">
//                 <span>✓ Personalized Q&A</span>
//                 <span>✓ Interest Analysis</span>
//                 <span>✓ Market Trends</span>
//               </div>
//               <button className="mode-btn">Start Chat Guidance</button>
//             </motion.div>

//             <motion.div
//               initial={{ opacity: 0, x: 50 }}
//               animate={{ opacity: 1, x: 0 }}
//               transition={{ delay: 0.7 }}
//               className="mode-card"
//               onClick={() => setAppMode('resume')}
//             >
//               <div className="mode-icon">📄</div>
//               <h3>Resume Analysis</h3>
//               <p>Upload your resume for detailed skill extraction and AI-powered career matching</p>
//               <div className="mode-features">
//                 <span>✓ Skill Extraction</span>
//                 <span>✓ ML Predictions</span>
//                 <span>✓ Detailed Analysis</span>
//               </div>
//               <button className="mode-btn">Upload Resume</button>
//             </motion.div>
//           </div>
//         </>
//       )}

//       {appMode === 'chat' && (
//         <div className="chat-mode">
//           <div className="mode-header">
//             <button className="back-btn" onClick={() => setAppMode('home')}>← Back to Home</button>
//             <h2>🤖 AI Career Guidance Chat</h2>
//           </div>
//           <Chatbot onResumeUploadRequest={() => setAppMode('resume')} />
//         </div>
//       )}

//       {appMode === 'resume' && (
//         <>
//           <header className="app-header">
//             <div className="mode-header">
//               <button className="back-btn" onClick={() => setAppMode('home')}>← Back to Home</button>
//               <motion.h1 
//                 initial={{ opacity: 0, y: -50 }}
//                 animate={{ opacity: 1, y: 0 }}
//                 transition={{ duration: 0.8 }}
//               >
//                 📄 Resume Analysis
//               </motion.h1>
//             </div>
//             <motion.p 
//               initial={{ opacity: 0 }}
//               animate={{ opacity: 1 }}
//               transition={{ delay: 0.3, duration: 0.8 }}
//             >
//               Upload your resume for detailed analysis and career recommendations
//             </motion.p>
//           </header>

//           <div className="progress-bar">
//             {[1, 2, 3, 4].map((step) => (
//               <div 
//                 key={step} 
//                 className={`progress-step ${currentStep >= step ? 'active' : ''}`}
//               >
//                 {step}
//               </div>
//             ))}
//           </div>

//           <main className="main-content">
//             <AnimatePresence mode="wait">
//               {currentStep === 1 && (
//                 <motion.div
//                   key="upload"
//                   initial={{ opacity: 0, x: -100 }}
//                   animate={{ opacity: 1, x: 0 }}
//                   exit={{ opacity: 0, x: 100 }}
//                   className="upload-section"
//                 >
//                   <div className="upload-card">
//                     <h2>📄 Upload Your Resume</h2>
//                     <div className="file-input-wrapper">
//                       <input
//                         type="file"
//                         accept=".pdf,.docx,.doc"
//                         onChange={handleFileSelect}
//                         id="file-input"
//                         className="file-input"
//                       />
//                       <label htmlFor="file-input" className="file-input-label">
//                         {selectedFile ? selectedFile.name : 'Choose PDF or DOCX file'}
//                       </label>
//                     </div>
                    
//                     {selectedFile && (
//                       <motion.button
//                         initial={{ scale: 0 }}
//                         animate={{ scale: 1 }}
//                         whileHover={{ scale: 1.05 }}
//                         whileTap={{ scale: 0.95 }}
//                         onClick={uploadResume}
//                         disabled={loading}
//                         className="upload-btn"
//                       >
//                         {loading ? '⏳ Processing...' : '🚀 Analyze Resume'}
//                       </motion.button>
//                     )}
                    
//                     {uploadStatus && (
//                       <motion.p 
//                         initial={{ opacity: 0 }}
//                         animate={{ opacity: 1 }}
//                         className={`status ${uploadStatus.includes('failed') ? 'error' : 'success'}`}
//                       >
//                         {uploadStatus}
//                       </motion.p>
//                     )}
//                   </div>
//                 </motion.div>
//               )}

//               {currentStep >= 2 && parsedData && (
//                 <motion.div
//                   key="parsed"
//                   initial={{ opacity: 0, y: 50 }}
//                   animate={{ opacity: 1, y: 0 }}
//                   className="parsed-section"
//                 >
//                   <div className="parsed-card">
//                     <h2>📊 Extracted Information</h2>
                    
//                     <div className="info-grid">
//                       <div className="info-item">
//                         <h3>🎯 Skills ({parsedData.skills?.length || 0})</h3>
//                         <div className="skills-container">
//                           {parsedData.skills?.map((skill, index) => (
//                             <motion.span
//                               key={index}
//                               initial={{ opacity: 0, scale: 0 }}
//                               animate={{ opacity: 1, scale: 1 }}
//                               transition={{ delay: index * 0.1 }}
//                               className="skill-tag"
//                             >
//                               {skill}
//                             </motion.span>
//                           ))}
//                         </div>
//                       </div>

//                       <div className="info-item">
//                         <h3>🎓 Education</h3>
//                         <div className="education-list">
//                           {parsedData.education?.map((edu, index) => (
//                             <div key={index} className="education-item">
//                               {edu}
//                             </div>
//                           ))}
//                         </div>
//                       </div>

//                       <div className="info-item">
//                         <h3>💼 Experience</h3>
//                         <div className="experience-list">
//                           {parsedData.experience?.map((exp, index) => (
//                             <div key={index} className="experience-item">
//                               <p><strong>Role:</strong> {exp.role || 'N/A'}</p>
//                               <p><strong>Company:</strong> {exp.company || 'N/A'}</p>
//                               <p><strong>Location:</strong> {exp.location || 'N/A'}</p>
//                               <p><strong>Duration:</strong> {exp.duration || 'N/A'}</p>
//                               <p><strong>Description:</strong> {exp.description || 'N/A'}</p>
//                             </div>
//                           ))}
//                         </div>

//                       </div>
//                     </div>
//                   </div>
//                 </motion.div>
//               )}

//               {currentStep >= 4 && careerSuggestions && (
//                 <motion.div
//                   key="suggestions"
//                   initial={{ opacity: 0, y: 50 }}
//                   animate={{ opacity: 1, y: 0 }}
//                   className="suggestions-section"
//                 >
//                   <div className="suggestions-card">
//                     <h2>🎯 Career Suggestions</h2>
//                     <div className="stats-bar">
//                       <div className="stat-item">
//                         <span className="stat-label">Method:</span>
//                         <span className="stat-value">{careerSuggestions.method_used}</span>
//                       </div>
//                       <div className="stat-item">
//                         <span className="stat-label">Skills Analyzed:</span>
//                         <span className="stat-value">{careerSuggestions.skills_count || '0'}</span>
//                       </div>
//                     </div>
                    
//                     <div className="careers-grid">
//                       {careerSuggestions.suggested_careers?.map((career, index) => (
//                         <motion.div
//                           key={index}
//                           initial={{ opacity: 0, x: -50 }}
//                           animate={{ opacity: 1, x: 0 }}
//                           transition={{ delay: index * 0.2 }}
//                           whileHover={{ scale: 1.02, boxShadow: "0 8px 25px rgba(0,0,0,0.15)" }}
//                           className="career-card"
//                         >
//                           <div className="career-rank">#{index + 1}</div>
//                           <h3>{career.title}</h3>
                          
//                           <div className="career-stats">
//                             <div className="stat">
//                               <span className="stat-label">Confidence:</span>
//                               <span className="stat-value">
//                                 {career.confidence ? `${(career.confidence * 100).toFixed(1)}%` : 'N/A'}
//                               </span>
//                             </div>
                            
//                             <div className="stat">
//                               <span className="stat-label">Skill Match:</span>
//                               <span className="stat-value">
//                                 {career.score ? `${(career.score * 100).toFixed(1)}%` : 'N/A'}
//                               </span>
//                             </div>
//                           </div>
                          
//                           <div className="skills-section">
//                             <h4>Key Skills:</h4>
//                             <div className="skills-container">
//                               {(career.skills || []).slice(0, 5).map((skill, i) => (
//                                 <span key={i} className="skill-tag">{skill}</span>
//                               ))}
//                               {(career.skills || []).length > 5 && (
//                                 <span className="skill-more">+{(career.skills || []).length - 5} more</span>
//                               )}
//                               {(career.skills || []).length === 0 && (
//                                 <span className="no-skills">No specific skills identified</span>
//                               )}
//                             </div>
//                           </div>
//                           <div className="career-match">
//                             <div className="match-bar">
//                               <div 
//                                 className="match-fill" 
//                                 style={{ width: `${career.skill_match || 50}%` }}
//                               ></div>
//                             </div>
//                           </div>
//                         </motion.div>
//                       ))}
//                     </div>

//                     <motion.button
//                       initial={{ opacity: 0 }}
//                       animate={{ opacity: 1 }}
//                       transition={{ delay: 1 }}
//                       whileHover={{ scale: 1.05 }}
//                       whileTap={{ scale: 0.95 }}
//                       onClick={resetApp}
//                       className="reset-btn"
//                     >
//                       🔄 Analyze Another Resume
//                     </motion.button>
//                   </div>
//                 </motion.div>
//               )}
//             </AnimatePresence>

//             {loading && (
//               <motion.div
//                 initial={{ opacity: 0 }}
//                 animate={{ opacity: 1 }}
//                 className="loading-overlay"
//               >
//                 <div className="loading-spinner"></div>
//                 <p>Processing your resume with AI...</p>
//               </motion.div>
//             )}
//           </main>

//           <footer className="app-footer">
//             <p>Powered by AI & Dynamic Market Data</p>
//           </footer>
//         </>
//       )}
//     </div>
//   );
// }

// export default App;
// import React, { useState } from 'react';
// import { Chatbot } from './components';
// import axios from 'axios';
// import { motion } from 'framer-motion';
// import './App.css';

// const API_BASE_URL = 'http://localhost:8000';

// const App = () => {
//   const [uploadedFile, setUploadedFile] = useState(null);
//   const [uploadProgress, setUploadProgress] = useState(0);
//   const [parsedData, setParsedData] = useState(null);
//   const [isUploading, setIsUploading] = useState(false);

//   const handleFileChange = (e) => setUploadedFile(e.target.files[0]);

//   const uploadResume = async () => {
//     if (!uploadedFile) return;
//     const formData = new FormData();
//     formData.append('resume', uploadedFile);

//     try {
//       setIsUploading(true);
//       const response = await axios.post(`${API_BASE_URL}/upload_resume`, formData, {
//         headers: { 'Content-Type': 'multipart/form-data' },
//         onUploadProgress: (progressEvent) => {
//           const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
//           setUploadProgress(percent);
//         }
//       });
//       setParsedData(response.data);
//     } catch (err) {
//       alert('Upload failed! Try again.');
//     } finally {
//       setIsUploading(false);
//       setUploadProgress(0);
//     }
//   };

//   const handleResumeUploadRequest = () => {
//     document.getElementById('resume-upload-input')?.scrollIntoView({ behavior: 'smooth' });
//   };

//   return (
//     <div className="app-container">
//       <div className="header">
//         <h1>AI Career Guidance Platform</h1>
//         <p>Upload your resume and get personalized career guidance.</p>
//       </div>

//       <div className="main-content">
//         <motion.div className="upload-card" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
//           <h2>📄 Upload Your Resume</h2>
//           <input
//             type="file"
//             id="resume-upload-input"
//             accept=".pdf,.doc,.docx"
//             onChange={handleFileChange}
//             disabled={isUploading}
//           />
//           <button onClick={uploadResume} disabled={!uploadedFile || isUploading}>
//             {isUploading ? `Uploading ${uploadProgress}%` : 'Upload Resume'}
//           </button>
//           {uploadProgress > 0 && (
//             <div className="progress-bar">
//               <motion.div
//                 className="progress-fill"
//                 initial={{ width: 0 }}
//                 animate={{ width: `${uploadProgress}%` }}
//                 transition={{ duration: 0.3 }}
//               />
//             </div>
//           )}
//         </motion.div>

//         {parsedData && (
//           <motion.div className="parsed-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
//             <h2>📝 Parsed Resume Data</h2>
//             <div className="parsed-section">
//               <strong>Name:</strong> {parsedData.name || 'N/A'}
//             </div>
//             <div className="parsed-section">
//               <strong>Email:</strong> {parsedData.email || 'N/A'}
//             </div>
//             <div className="parsed-section">
//               <strong>Skills:</strong> {parsedData.skills?.join(', ') || 'N/A'}
//             </div>
//             <div className="parsed-section">
//               <strong>Experience:</strong> {parsedData.experience || 'N/A'}
//             </div>
//           </motion.div>
//         )}

//         <motion.div className="chatbot-section" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
//           <Chatbot onResumeUploadRequest={handleResumeUploadRequest} />
//         </motion.div>
//       </div>
//     </div>
//   );
// };

// export default App;
import React, { useState } from 'react';
import { Chatbot } from './components';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const App = () => {
  const [mode, setMode] = useState('landing'); // landing, resume
  const [chatOpen, setChatOpen] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [parsedData, setParsedData] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (e) => setUploadedFile(e.target.files[0]);

  const uploadResume = async () => {
    if (!uploadedFile) return;
    const formData = new FormData();
    formData.append('resume', uploadedFile);

    try {
      setIsUploading(true);
      const response = await axios.post(`${API_BASE_URL}/upload_resume`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percent);
        },
      });
      setParsedData(response.data);
    } catch (err) {
      alert('Upload failed! Try again.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const openChat = () => setChatOpen(true);
  const closeChat = () => setChatOpen(false);

  return (
    <div className="app-container">
      {/* Landing Page */}
      {mode === 'landing' && (
        <motion.div
          className="landing-page"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <div className="landing-hero">
            <div className="landing-icon">
              {/* Modern SVG icon */}
              <svg width="80" height="80" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L15 8H9L12 2Z" fill="#fff"/>
                <path d="M12 22L9 16H15L12 22Z" fill="#fff"/>
                <path d="M2 12L8 15V9L2 12Z" fill="#fff"/>
                <path d="M22 12L16 9V15L22 12Z" fill="#fff"/>
              </svg>
            </div>
            <h1>AI Career Guidance Platform</h1>
            <p>Discover your optimal career path using AI-powered resume analysis and interactive guidance.</p>
          </div>

          {/* Features */}
          <div className="features-grid">
            <motion.div className="feature-card" whileHover={{ scale: 1.05 }}>
              <div className="feature-icon">📈</div>
              <h3>Data-Driven Insights</h3>
              <p>Receive career suggestions based on market trends and your skills.</p>
            </motion.div>

            <motion.div className="feature-card" whileHover={{ scale: 1.05 }}>
              <div className="feature-icon">📝</div>
              <h3>Resume Parsing</h3>
              <p>Automatically extract your skills, education, and experience.</p>
            </motion.div>

            <motion.div className="feature-card" whileHover={{ scale: 1.05 }}>
              <div className="feature-icon">💬</div>
              <h3>Interactive Chatbot</h3>
              <p>Explore career paths by chatting with our AI assistant.</p>
            </motion.div>

            <motion.div className="feature-card" whileHover={{ scale: 1.05 }}>
              <div className="feature-icon">🎯</div>
              <h3>Personalized Recommendations</h3>
              <p>Get tailored career advice unique to your profile.</p>
            </motion.div>
          </div>

          {/* Resume Analysis Button */}
          <motion.button
            className="action-btn resume-btn"
            onClick={() => setMode('resume')}
            whileHover={{ scale: 1.05 }}
          >
            📄 Analyze Your Resume
          </motion.button>
        </motion.div>
      )}

      {/* Resume Analysis Page */}
      {mode === 'resume' && (
        <motion.div className="resume-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.8 }}>
          <button className="back-btn" onClick={() => setMode('landing')}>← Back</button>
          <h1>📄 Resume Analysis</h1>
          <div className="upload-section">
            <input type="file" accept=".pdf,.doc,.docx" onChange={handleFileChange} disabled={isUploading} />
            <button onClick={uploadResume} disabled={!uploadedFile || isUploading}>
              {isUploading ? `Uploading ${uploadProgress}%` : 'Upload Resume'}
            </button>
            {uploadProgress > 0 && (
              <div className="progress-bar">
                <motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${uploadProgress}%` }} transition={{ duration: 0.3 }} />
              </div>
            )}
          </div>

          {parsedData && (
            <motion.div className="parsed-card" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <h2>📝 Parsed Resume Data</h2>
              <div className="parsed-section"><strong>Name:</strong> {parsedData.name || 'N/A'}</div>
              <div className="parsed-section"><strong>Email:</strong> {parsedData.email || 'N/A'}</div>
              <div className="parsed-section"><strong>Skills:</strong> {parsedData.skills?.join(', ') || 'N/A'}</div>
              <div className="parsed-section"><strong>Experience:</strong> {parsedData.experience || 'N/A'}</div>
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Floating Chatbot */}
      <AnimatePresence>
        {chatOpen && (
          <motion.div className="chatbot-float" initial={{ opacity: 0, y: 50 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 50 }}>
            <div className="chatbot-header">
              <span>💬 AI Career Chatbot</span>
              <button onClick={() => setChatOpen(false)}>✖</button>
            </div>
            <Chatbot onResumeUploadRequest={() => setMode('resume')} />
          </motion.div>
        )}
      </AnimatePresence>

      {!chatOpen && (
        <motion.button className="chat-btn" onClick={openChat} whileHover={{ scale: 1.1 }}>
          💬
        </motion.button>
      )}
    </div>
  );
};

export default App;
