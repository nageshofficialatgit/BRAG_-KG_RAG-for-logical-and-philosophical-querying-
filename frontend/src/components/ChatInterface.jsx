import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
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

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Chat</h2>
        <button
          className="add-reference-button"
          onClick={() => setShowReferenceInput(!showReferenceInput)}
        >
          {showReferenceInput ? '✕' : '+ Add Reference Text'}
        </button>
      </div>

      {showReferenceInput && (
        <div className="reference-input-panel">
          <textarea
            className="reference-textarea"
            placeholder="Paste your reference text here (e.g., philosophy book content)..."
            value={referenceText}
            onChange={(e) => setReferenceText(e.target.value)}
            rows={6}
          />
          <button
            className="create-graph-button"
            onClick={handleCreateGraph}
            disabled={!referenceText.trim() || loading}
          >
            {loading ? 'Creating...' : 'Create Knowledge Graph'}
          </button>
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 && (
          <div className="welcome-message">
            <h3>Welcome to Knowledge Graph RAG</h3>
            <p>Start by adding reference text or ask a question about philosophy!</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.type}`}>
            <div className="message-content">
              {msg.type === 'user' && <span className="message-icon">👤</span>}
              {msg.type === 'assistant' && <span className="message-icon">🤖</span>}
              {msg.type === 'system' && <span className="message-icon">ℹ️</span>}
              {msg.type === 'error' && <span className="message-icon">⚠️</span>}
              
              <div className="message-text">
                <div className="message-body">{msg.content}</div>
                
                {msg.sources && Object.keys(msg.sources).length > 0 && (
                  <div className="message-sources">
                    <strong>Sources:</strong>
                    {msg.sources.knowledge_graph?.length > 0 && (
                      <div>KG Entities: {msg.sources.knowledge_graph.join(', ')}</div>
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
                  </div>
                )}

                {msg.images && msg.images.length > 0 && (
                  <div className="message-images">
                    {msg.images.map((img, i) => (
                      <img
                        key={i}
                        src={img.thumbnail || img.url}
                        alt={img.title || 'Image'}
                        className="message-image"
                        onClick={() => window.open(img.url, '_blank')}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message assistant">
            <div className="message-content">
              <span className="message-icon">🤖</span>
              <div className="message-text">
                <div className="loading-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          </div>
        )}
        
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
        <button
          className="send-button"
          onClick={handleSendMessage}
          disabled={!input.trim() || loading}
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default ChatInterface
