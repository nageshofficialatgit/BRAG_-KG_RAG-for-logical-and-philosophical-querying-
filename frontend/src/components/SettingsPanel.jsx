import React, { useState, useEffect } from 'react'
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
      setProviders(response.data.providers)
    } catch (error) {
      console.error('Error fetching providers:', error)
    }
  }

  const checkOllama = async () => {
    try {
      const response = await fetch('http://localhost:11434/api/tags')
      setOllamaAvailable(response.ok)
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

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Settings</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>

        <div className="settings-content">
          <div className="setting-group">
            <label>LLM Provider</label>
            <select
              value={localSettings.llmProvider}
              onChange={(e) => {
                handleChange('llmProvider', e.target.value)
                // Reset model when provider changes
                const newProvider = providers.find(p => p.name === e.target.value)
                if (newProvider?.default) {
                  handleChange('model', newProvider.default)
                }
              }}
            >
              {providers.map(provider => (
                <option key={provider.name} value={provider.name}>
                  {provider.name} {provider.name === 'ollama' && !ollamaAvailable && '(Not Available)'}
                </option>
              ))}
            </select>
            {localSettings.llmProvider === 'ollama' && !ollamaAvailable && (
              <p className="warning">Ollama is not running. Start Ollama to use local models.</p>
            )}
          </div>

          <div className="setting-group">
            <label>Model</label>
            <select
              value={localSettings.model || selectedProvider?.default || ''}
              onChange={(e) => handleChange('model', e.target.value)}
            >
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
          </div>

          <div className="setting-group">
            <label>
              <input
                type="checkbox"
                checked={localSettings.includeWeb}
                onChange={(e) => handleChange('includeWeb', e.target.checked)}
              />
              Include Web Search
            </label>
            <p className="setting-description">
              Search the internet for latest information beyond reference text
            </p>
          </div>

          <div className="setting-group">
            <label>
              <input
                type="checkbox"
                checked={localSettings.includeImages}
                onChange={(e) => handleChange('includeImages', e.target.checked)}
              />
              Include Image Search
            </label>
            <p className="setting-description">
              Retrieve relevant images for queries
            </p>
          </div>

          {localSettings.llmProvider === 'openai' && (
            <div className="setting-group">
              <label>OpenAI API Key</label>
              <input
                type="password"
                placeholder="Set in .env file"
                disabled
                className="api-key-input"
              />
              <p className="setting-description">
                Configure OPENAI_API_KEY in backend/.env file
              </p>
            </div>
          )}
        </div>

        <div className="settings-footer">
          <button className="save-button" onClick={handleSave}>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPanel
