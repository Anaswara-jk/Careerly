
// import React, { useState, useEffect, useRef } from 'react';
// import { motion, AnimatePresence } from 'framer-motion';
// import axios from 'axios';
// import './Chatbot.css';

// const API_BASE_URL = 'http://localhost:8000';


// const Chatbot = ({ onResumeUploadRequest }) => {
//   const [messages, setMessages] = useState([]);
//   const [inputMessage, setInputMessage] = useState('');
//   const [isLoading, setIsLoading] = useState(false);
//   const [userId] = useState(() => `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
//   const [currentStage, setCurrentStage] = useState('greeting');
//   const [progress, setProgress] = useState(0);
//   const [suggestions, setSuggestions] = useState([]);
//   const [isTyping, setIsTyping] = useState(false);
//   const messagesEndRef = useRef(null);
//   const inputRef = useRef(null);

//   const scrollToBottom = () => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   };

//   useEffect(() => {
//     scrollToBottom();
//   }, [messages]);

//   useEffect(() => {
//     startChatSession();
//   }, []);

//   const startChatSession = async () => {
//     try {
//       setIsLoading(true);
//       const response = await axios.post(`${API_BASE_URL}/chat/start?user_id=${userId}`);
      
//       if (response.data.success) {
//         const botResponse = response.data.response;
//         addMessage('bot', botResponse.message);
//         setCurrentStage(botResponse.stage);
//         setProgress(botResponse.progress || 0);
//         setSuggestions(botResponse.suggestions || []);
//       }
//     } catch (error) {
//       console.error('Error starting chat session:', error);
//       addMessage('bot', "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.");
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const sendMessage = async (message = inputMessage) => {
//     if (!message.trim() || isLoading) return;

//     // Add user message immediately
//     addMessage('user', message);
//     setInputMessage('');
//     setIsLoading(true);
//     setIsTyping(true);

//     try {
//       const response = await axios.post(`${API_BASE_URL}/chat/message`, {
//         user_id: userId,
//         message: message
//       });

//       if (response.data.success) {
//         const botResponse = response.data.response;
        
//         // Simulate typing delay for better UX
//         setTimeout(() => {
//           setIsTyping(false);
//           addMessage('bot', botResponse.message, botResponse);
//           setCurrentStage(botResponse.stage);
//           setProgress(botResponse.progress || 0);
//           setSuggestions(botResponse.suggestions || []);
          
//           // Handle special actions
//           if (botResponse.action === 'redirect_to_resume_upload') {
//             setTimeout(() => {
//               onResumeUploadRequest && onResumeUploadRequest();
//             }, 2000);
//           }
//         }, 1000 + Math.random() * 1000); // Random delay between 1-2 seconds
//       }
//     } catch (error) {
//       console.error('Error sending message:', error);
//       setIsTyping(false);
//       addMessage('bot', "I'm sorry, I encountered an error. Please try again.");
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   const addMessage = (sender, text, metadata = {}) => {
//     const newMessage = {
//       id: Date.now() + Math.random(),
//       sender,
//       text,
//       timestamp: new Date(),
//       metadata
//     };
//     setMessages(prev => [...prev, newMessage]);
//   };

//   const handleSuggestionClick = (suggestion) => {
//     sendMessage(suggestion);
//   };

//   const handleKeyPress = (e) => {
//     if (e.key === 'Enter' && !e.shiftKey) {
//       e.preventDefault();
//       sendMessage();
//     }
//   };

//   const resetChat = async () => {
//     try {
//       await axios.post(`${API_BASE_URL}/chat/reset/${userId}`);
//       setMessages([]);
//       setProgress(0);
//       setSuggestions([]);
//       setCurrentStage('greeting');
//       startChatSession();
//     } catch (error) {
//       console.error('Error resetting chat:', error);
//     }
//   };

//   const formatMessage = (text) => {
//     // Convert markdown-style formatting to HTML
//     return text
//       .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
//       .replace(/\*(.*?)\*/g, '<em>$1</em>')
//       .replace(/•/g, '•')
//       .replace(/\n/g, '<br/>');
//   };

//   return (
//     <div className="chatbot-container">
//       <div className="chatbot-header">
//         <div className="header-content">
//           <div className="bot-avatar">
//             <span className="bot-icon">🤖</span>
//           </div>
//           <div className="header-info">
//             <h3>AI Career Guidance Assistant</h3>
//             <p className="status">
//               {isTyping ? 'Typing...' : 'Online'}
//               {progress > 0 && (
//                 <span className="progress-indicator">
//                   • Progress: {progress}%
//                 </span>
//               )}
//             </p>
//           </div>
//           <button className="reset-btn" onClick={resetChat} title="Start New Conversation">
//             🔄
//           </button>
//         </div>
//         {progress > 0 && (
//           <div className="progress-bar">
//             <motion.div 
//               className="progress-fill"
//               initial={{ width: 0 }}
//               animate={{ width: `${progress}%` }}
//               transition={{ duration: 0.5 }}
//             />
//           </div>
//         )}
//       </div>

//       <div className="chatbot-messages">
//         <AnimatePresence>
//           {messages.map((message) => (
//             <motion.div
//               key={message.id}
//               initial={{ opacity: 0, y: 20 }}
//               animate={{ opacity: 1, y: 0 }}
//               exit={{ opacity: 0, y: -20 }}
//               className={`message ${message.sender}`}
//             >
//               <div className="message-content">
//                 <div 
//                   className="message-text"
//                   dangerouslySetInnerHTML={{ __html: formatMessage(message.text) }}
//                 />
//                 <div className="message-time">
//                   {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
//                 </div>
//               </div>
              
//               {/* Show recommendations if available */}
//               {message.metadata?.recommendations && (
//                 <div className="recommendations-container">
//                   <h4>🎯 Your Career Recommendations:</h4>
//                   {message.metadata.recommendations.slice(0, 3).map((career, index) => (
//                     <motion.div
//                       key={index}
//                       initial={{ opacity: 0, x: -20 }}
//                       animate={{ opacity: 1, x: 0 }}
//                       transition={{ delay: index * 0.2 }}
//                       className="recommendation-card"
//                     >
//                       <div className="career-title">{career.title}</div>
//                       <div className="match-score">
//                         Match: {(career.match_score * 100).toFixed(0)}%
//                       </div>
//                       <div className="key-skills">
//                         Skills: {career.key_skills?.slice(0, 3).join(', ')}
//                       </div>
//                     </motion.div>
//                   ))}
//                 </div>
//               )}
//             </motion.div>
//           ))}
//         </AnimatePresence>

//         {isTyping && (
//           <motion.div
//             initial={{ opacity: 0, y: 20 }}
//             animate={{ opacity: 1, y: 0 }}
//             className="message bot typing"
//           >
//             <div className="message-content">
//               <div className="typing-indicator">
//                 <span></span>
//                 <span></span>
//                 <span></span>
//               </div>
//             </div>
//           </motion.div>
//         )}

//         <div ref={messagesEndRef} />
//       </div>

//       {/* Quick suggestions */}
//       {suggestions.length > 0 && (
//         <div className="suggestions-container">
//           <div className="suggestions-label">Quick responses:</div>
//           <div className="suggestions">
//             {suggestions.map((suggestion, index) => (
//               <motion.button
//                 key={index}
//                 initial={{ opacity: 0, scale: 0.8 }}
//                 animate={{ opacity: 1, scale: 1 }}
//                 transition={{ delay: index * 0.1 }}
//                 className="suggestion-btn"
//                 onClick={() => handleSuggestionClick(suggestion)}
//               >
//                 {suggestion}
//               </motion.button>
//             ))}
//           </div>
//         </div>
//       )}

//       <div className="chatbot-input">
//         <div className="input-container">
//           <textarea
//             ref={inputRef}
//             value={inputMessage}
//             onChange={(e) => setInputMessage(e.target.value)}
//             onKeyPress={handleKeyPress}
//             placeholder="Type your message here..."
//             className="message-input"
//             rows="1"
//             disabled={isLoading}
//           />
//           <motion.button
//             whileHover={{ scale: 1.05 }}
//             whileTap={{ scale: 0.95 }}
//             className={`send-btn ${inputMessage.trim() ? 'active' : ''}`}
//             onClick={() => sendMessage()}
//             disabled={isLoading || !inputMessage.trim()}
//           >
//             {isLoading ? '⏳' : '📤'}
//           </motion.button>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default Chatbot;
// */
import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import './Chatbot.css';

const API_BASE_URL = 'http://localhost:8000';

const Chatbot = ({ onResumeUploadRequest }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userId] = useState(() => `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`);
  const [currentStage, setCurrentStage] = useState('greeting');
  const [progress, setProgress] = useState(0);
  const [suggestions, setSuggestions] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    startChatSession();
  }, []);

  const startChatSession = async () => {
    try {
      setIsLoading(true);
      const response = await axios.post(`${API_BASE_URL}/chat/start?user_id=${userId}`);
      if (response.data.success) {
        const botResponse = response.data.response;
        addMessage('bot', botResponse.message);
        setCurrentStage(botResponse.stage);
        setProgress(botResponse.progress || 0);
        setSuggestions(botResponse.suggestions || []);
      }
    } catch (error) {
      addMessage('bot', "Connection error! Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (message = inputMessage) => {
    if (!message.trim() || isLoading) return;
    addMessage('user', message);
    setInputMessage('');
    setIsLoading(true);
    setIsTyping(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat/message`, { user_id: userId, message });
      if (response.data.success) {
        const botResponse = response.data.response;
        setTimeout(() => {
          setIsTyping(false);
          addMessage('bot', botResponse.message, botResponse);
          setCurrentStage(botResponse.stage);
          setProgress(botResponse.progress || 0);
          setSuggestions(botResponse.suggestions || []);
          if (botResponse.action === 'redirect_to_resume_upload') {
            setTimeout(() => onResumeUploadRequest && onResumeUploadRequest(), 1500);
          }
        }, 1000 + Math.random() * 1000);
      }
    } catch (error) {
      setIsTyping(false);
      addMessage('bot', "Error occurred! Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (sender, text, metadata = {}) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), sender, text, timestamp: new Date(), metadata }]);
  };

  const handleSuggestionClick = (suggestion) => sendMessage(suggestion);
  const handleKeyPress = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };

  const resetChat = async () => {
    try {
      await axios.post(`${API_BASE_URL}/chat/reset/${userId}`);
      setMessages([]);
      setProgress(0);
      setSuggestions([]);
      setCurrentStage('greeting');
      startChatSession();
    } catch (error) {
      console.error(error);
    }
  };

  const formatMessage = (text) => text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/•/g, '•')
    .replace(/\n/g, '<br/>');

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">
        <div className="header-content">
          <div className="bot-avatar">🤖</div>
          <div className="header-info">
            <h3>AI Career Guidance Assistant</h3>
            <p className="status">
              {isTyping ? 'Typing...' : 'Online'}
              {progress > 0 && <span className="progress-indicator">• Progress: {progress}%</span>}
            </p>
          </div>
          <button className="reset-btn" onClick={resetChat}>🔄</button>
        </div>
        {progress > 0 && (
          <div className="progress-bar">
            <motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ duration: 0.5 }} />
          </div>
        )}
      </div>

      <div className="chatbot-messages">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div key={msg.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className={`message ${msg.sender}`}>
              <div className="message-content">
                <div className="message-text" dangerouslySetInnerHTML={{ __html: formatMessage(msg.text) }} />
                <div className="message-time">{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
              </div>

              {msg.metadata?.recommendations && (
                <div className="recommendations-container">
                  <h4>🎯 Career Recommendations:</h4>
                  {msg.metadata.recommendations.slice(0, 3).map((career, index) => (
                    <motion.div key={index} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: index * 0.2 }} className="recommendation-card">
                      <div className="career-title">{career.title}</div>
                      <div className="match-score">Match: {(career.match_score * 100).toFixed(0)}%</div>
                      <div className="key-skills">Skills: {career.key_skills?.slice(0, 3).join(', ')}</div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="message bot typing"><div className="message-content"><div className="typing-indicator"><span></span><span></span><span></span></div></div></motion.div>}
        <div ref={messagesEndRef} />
      </div>

      {suggestions.length > 0 && (
        <div className="suggestions-container">
          <div className="suggestions-label">Quick responses:</div>
          <div className="suggestions">
            {suggestions.map((s, i) => (
              <motion.button key={i} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.1 }} className="suggestion-btn" onClick={() => handleSuggestionClick(s)}>{s}</motion.button>
            ))}
          </div>
        </div>
      )}

      <div className="chatbot-input">
        <div className="input-container">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="message-input"
            rows="1"
            disabled={isLoading}
          />
          <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} className={`send-btn ${inputMessage.trim() ? 'active' : ''}`} onClick={sendMessage} disabled={isLoading || !inputMessage.trim()}>{isLoading ? '⏳' : '📤'}</motion.button>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
