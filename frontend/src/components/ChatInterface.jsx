import React, { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './ChatInterface.css'

const API_BASE = '/api'

function ChatInterface({ onGraphUpdate, settings, selectedSources = [] }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [referenceText, setReferenceText] = useState('')
  const [showReferenceInput, setShowReferenceInput] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleCreateGraph = async () => {
    if (!referenceText.trim()) return

    setLoading(true)
    try {
      const response = await axios.post(`${API_BASE}/kg/create`, {
        text: referenceText,
        source_name: 'reference_text',
        llm_provider: settings.llmProvider,
        model: settings.model
      })

      if (response.data.success) {
        setMessages(prev => [...prev, {
          type: 'system',
          content: `Knowledge graph created! ${response.data.statistics?.total_nodes || 0} nodes, ${response.data.statistics?.total_relationships || 0} relationships.`
        }])
        setShowReferenceInput(false)
        setReferenceText('')
      }
    } catch (error) {
      console.error('Error creating graph:', error)
      setMessages(prev => [...prev, {
        type: 'error',
        content: `Error creating graph: ${error.response?.data?.detail || error.message}`
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages(prev => [...prev, { type: 'user', content: userMessage }])
    setLoading(true)

    try {
      const chatHistory = messages
        .filter(m => m.type === 'user' || m.type === 'assistant')
        .map((m, i, arr) => {
          if (m.type === 'user') {
            const nextAssistant = arr.slice(i + 1).find(a => a.type === 'assistant')
            if (nextAssistant) {
              return [m.content, nextAssistant.content]
            }
          }
          return null
        })
        .filter(Boolean)

      const response = await axios.post(`${API_BASE}/rag/query`, {
        question: userMessage,
        chat_history: chatHistory,
        llm_provider: settings.llmProvider,
        model: settings.model,
        include_web: settings.includeWeb,
        include_images: settings.includeImages,
        sources: selectedSources.length > 0 ? selectedSources : null
      })

      const data = response.data

      // Update graph visualization
      if (data.graph) {
        onGraphUpdate(data.graph)
      }

      // Add assistant response
      setMessages(prev => [...prev, {
        type: 'assistant',
        content: data.answer,
        sources: data.sources,
        images: data.images || []
      }])
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => [...prev, {
        type: 'error',
        content: `Error: ${error.response?.data?.detail || error.message}`
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const messageVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -10 }
  }

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>╔─ Chat ─╗</h2>
        <motion.button
          className="add-reference-button"
          onClick={() => setShowReferenceInput(!showReferenceInput)}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          {showReferenceInput ? '[−] Close' : '[+] Add Reference'}
        </motion.button>
      </div>

      <AnimatePresence>
        {showReferenceInput && (
          <motion.div 
            className="reference-input-panel"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <textarea
              className="reference-textarea"
              placeholder="Paste your reference text here (e.g., philosophy book content)..."
              value={referenceText}
              onChange={(e) => setReferenceText(e.target.value)}
              rows={6}
            />
            <motion.button
              className="create-graph-button"
              onClick={handleCreateGraph}
              disabled={!referenceText.trim() || loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              {loading ? '⟳ Creating...' : '► Create Graph'}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="messages-container">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 && !loading && (
            <motion.div 
              className="welcome-message"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
            >
              <h3>Welcome to Knowledge Graph RAG</h3>
              <div className="welcome-ascii">
{`╔═══════════════════════════════════════╗
║   Start by adding reference text     ║
║   or ask a question about your      ║
║   knowledge domain!                 ║
╚═══════════════════════════════════════╝`}
              </div>
            </motion.div>
          )}
          
          {messages.map((msg, idx) => (
            <motion.div 
              key={idx} 
              className={`message ${msg.type}`}
              variants={messageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.2 }}
            >
              <div className="message-content">
                <span className="message-icon">
                  {msg.type === 'user' && '►'}
                  {msg.type === 'assistant' && '◄'}
                  {msg.type === 'system' && '◊'}
                  {msg.type === 'error' && '✕'}
                </span>
                
                <div className="message-text">
                  <div className={`message-body ${msg.type === 'assistant' ? 'markdown-content' : ''}`}>
                    {msg.type === 'assistant' ? (
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({node, ...props}) => <h1 className="md-h1" {...props} />,
                          h2: ({node, ...props}) => <h2 className="md-h2" {...props} />,
                          h3: ({node, ...props}) => <h3 className="md-h3" {...props} />,
                          h4: ({node, ...props}) => <h4 className="md-h4" {...props} />,
                          p: ({node, ...props}) => <p className="md-p" {...props} />,
                          ul: ({node, ...props}) => <ul className="md-ul" {...props} />,
                          ol: ({node, ...props}) => <ol className="md-ol" {...props} />,
                          li: ({node, ...props}) => <li className="md-li" {...props} />,
                          blockquote: ({node, ...props}) => <blockquote className="md-blockquote" {...props} />,
                          strong: ({node, ...props}) => <strong className="md-strong" {...props} />,
                          em: ({node, ...props}) => <em className="md-em" {...props} />,
                          code: ({node, inline, ...props}) => 
                            inline ? <code className="md-code-inline" {...props} /> : <code className="md-code-block" {...props} />,
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    ) : (
                      msg.content
                    )}
                  </div>
                  
                  {msg.sources && Object.keys(msg.sources).length > 0 && (
                    <motion.div 
                      className="message-sources"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      <strong>┌─ Sources ─┐</strong>
                      {msg.sources.knowledge_graph?.length > 0 && (
                        <div>KG: {msg.sources.knowledge_graph.join(', ')}</div>
                      )}
                      {msg.sources.web?.length > 0 && (
                        <div>
                          Web: {msg.sources.web.slice(0, 3).map((s, i) => (
                            <a key={i} href={s.url} target="_blank" rel="noopener noreferrer">
                              {s.title || s.url}
                            </a>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )}

                  {msg.images && msg.images.length > 0 && (
                    <motion.div 
                      className="message-images"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      {msg.images.map((img, i) => (
                        <motion.img
                          key={i}
                          src={img.thumbnail || img.url}
                          alt={img.title || 'Image'}
                          className="message-image"
                          onClick={() => window.open(img.url, '_blank')}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        />
                      ))}
                    </motion.div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
          
          {loading && (
            <motion.div 
              className="message assistant"
              variants={messageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <div className="message-content">
                <span className="message-icon">◄</span>
                <div className="message-text">
                  <div className="loading-dots">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
        
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        <textarea
          className="message-input"
          placeholder="Ask about philosophy, references, or concepts..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          rows={1}
          disabled={loading}
        />
        <motion.button
          className="send-button"
          onClick={handleSendMessage}
          disabled={!input.trim() || loading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
        >
          ►
        </motion.button>
      </div>
    </div>
  )
}

export default ChatInterface
