import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import './SettingsPanel.css'

const API_BASE = '/api'

function SettingsPanel({ settings, onSettingsChange, onClose }) {
  const [localSettings, setLocalSettings] = useState(settings)
  const [providers, setProviders] = useState([])
  const [ollamaAvailable, setOllamaAvailable] = useState(false)

  useEffect(() => {
    fetchProviders()
    checkOllama()
  }, [])

  const fetchProviders = async () => {
    try {
      const response = await axios.get(`${API_BASE}/rag/providers`)
      console.debug('Fetched providers:', response.data)
      setProviders(response.data.providers)
    } catch (error) {
      console.error('Error fetching providers:', error)
    }
  }

  const checkOllama = async () => {
    try {
      // Try both modern and legacy endpoints
      let ok = false
      for (const ep of ['/api/models', '/api/tags']) {
        try {
          const response = await fetch(`http://localhost:11434${ep}`)
          if (response.ok) { ok = true; break }
        } catch (e) {
          // ignore and try next
        }
      }
      setOllamaAvailable(ok)
    } catch (error) {
      setOllamaAvailable(false)
    }
  }

  const handleChange = (key, value) => {
    const newSettings = { ...localSettings, [key]: value }
    setLocalSettings(newSettings)
    onSettingsChange(newSettings)
  }

  const handleSave = () => {
    onSettingsChange(localSettings)
    onClose()
  }

  const selectedProvider = providers.find(p => p.name === localSettings.llmProvider)
  
  // Set default model if not set or if provider changed
  useEffect(() => {
    if (selectedProvider && selectedProvider.default && !localSettings.model) {
      handleChange('model', selectedProvider.default)
    }
  }, [selectedProvider])

  const overlayVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  }

  const panelVariants = {
    initial: { scale: 0.95, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 0.95, opacity: 0 }
  }

  const itemVariants = {
    initial: { opacity: 0, y: 10 },
    animate: { opacity: 1, y: 0 }
  }

  return (
    <AnimatePresence>
      <motion.div 
        className="settings-overlay" 
        onClick={onClose}
        variants={overlayVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.2 }}
      >
        <motion.div 
          className="settings-panel" 
          onClick={(e) => e.stopPropagation()}
          variants={panelVariants}
          initial="initial"
          animate="animate"
          exit="exit"
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <div className="settings-header">
            <h2>╔─ Settings ─╗</h2>
            <motion.button 
              className="close-button" 
              onClick={onClose}
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.95 }}
            >
              [×]
            </motion.button>
          </div>

          <motion.div 
            className="settings-content"
            variants={{ animate: { transition: { staggerChildren: 0.05 } } }}
            initial="initial"
            animate="animate"
          >
            <motion.div className="setting-group" variants={itemVariants}>
              <label>┌─ LLM Provider</label>
              <select
                value={localSettings.llmProvider}
                onChange={(e) => {
                  handleChange('llmProvider', e.target.value)
                  const newProvider = providers.find(p => p.name === e.target.value)
                  if (newProvider?.default) {
                    handleChange('model', newProvider.default)
                  }
                }}
              >
                <option value="">Select Provider</option>
                {providers.map(provider => (
                  <option key={provider.name} value={provider.name}>
                    {provider.name} {provider.name === 'ollama' && !ollamaAvailable && '(Not Available)'}
                  </option>
                ))}
              </select>
              {localSettings.llmProvider === 'ollama' && !ollamaAvailable && (
                <motion.p 
                  className="warning"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  ⚠ Ollama not running. Start Ollama to use local models.
                </motion.p>
              )}
            </motion.div>

            <motion.div className="setting-group" variants={itemVariants}>
              <label>┌─ Model</label>
              <select
                value={localSettings.model || selectedProvider?.default || ''}
                onChange={(e) => handleChange('model', e.target.value)}
              >
                <option value="">Select Model</option>
                {selectedProvider?.models?.map(model => (
                  <option key={model} value={model}>
                    {model} {model === selectedProvider?.default && '(Default)'}
                  </option>
                ))}
              </select>
              {selectedProvider?.default && (
                <p className="setting-description">
                  Default: {selectedProvider.default}
                </p>
              )}
            </motion.div>

            <motion.div className="setting-group" variants={itemVariants}>
              <label>
                <input
                  type="checkbox"
                  checked={localSettings.includeWeb}
                  onChange={(e) => handleChange('includeWeb', e.target.checked)}
                />
                ☐ Include Web Search
              </label>
              <p className="setting-description">
                Search the internet for latest information
              </p>
            </motion.div>

            <motion.div className="setting-group" variants={itemVariants}>
              <label>
                <input
                  type="checkbox"
                  checked={localSettings.includeImages}
                  onChange={(e) => handleChange('includeImages', e.target.checked)}
                />
                ☐ Include Image Search
              </label>
              <p className="setting-description">
                Retrieve relevant images for queries
              </p>
            </motion.div>

            {localSettings.llmProvider === 'openai' && (
              <motion.div className="setting-group" variants={itemVariants}>
                <label>┌─ OpenAI API Key</label>
                <input
                  type="password"
                  placeholder="Set in .env file"
                  disabled
                  className="api-key-input"
                />
                <p className="setting-description">
                  Configure OPENAI_API_KEY in backend/.env
                </p>
              </motion.div>
            )}
          </motion.div>

          <div className="settings-footer">
            <motion.button 
              className="save-button" 
              onClick={handleSave}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              ► Save Settings
            </motion.button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default SettingsPanel
