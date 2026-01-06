import React, { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import GraphVisualization from './components/GraphVisualization'
import SettingsPanel from './components/SettingsPanel'
import BookManager from './components/BookManager'
import './App.css'

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [showSettings, setShowSettings] = useState(false)
  const [showBooks, setShowBooks] = useState(true)
  const [selectedSources, setSelectedSources] = useState([])
  const [settings, setSettings] = useState({
    llmProvider: 'ollama',
    model: 'gemma3:4b',
    includeWeb: true,
    includeImages: true
  })

  const handleGraphUpdate = (newGraphData) => {
    setGraphData(newGraphData)
  }

  const handleBooksProcessed = () => {
    // Refresh graph or show notification
    console.log('Books processed')
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Knowledge Graph RAG System</h1>
        <div className="header-actions">
          <button
            className={`toggle-button ${showBooks ? 'active' : ''}`}
            onClick={() => setShowBooks(!showBooks)}
            title="Toggle Books Panel"
          >
            📚 Books
          </button>
          <button
            className="settings-button"
            onClick={() => setShowSettings(!showSettings)}
          >
            ⚙️ Settings
          </button>
        </div>
      </header>
      
      {showSettings && (
        <SettingsPanel
          settings={settings}
          onSettingsChange={setSettings}
          onClose={() => setShowSettings(false)}
        />
      )}

      <div className="app-content">
        {showBooks && (
          <div className="books-panel">
            <BookManager
              onBooksProcessed={handleBooksProcessed}
              selectedSources={selectedSources}
              onSourcesChange={setSelectedSources}
            />
          </div>
        )}
        <div className="chat-panel">
          <ChatInterface
            onGraphUpdate={handleGraphUpdate}
            settings={settings}
            selectedSources={selectedSources}
          />
        </div>
        <div className="graph-panel">
          <GraphVisualization graphData={graphData} />
        </div>
      </div>
    </div>
  )
}

export default App
