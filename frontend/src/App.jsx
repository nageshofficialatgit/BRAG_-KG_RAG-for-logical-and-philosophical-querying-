import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import ChatInterface from './components/ChatInterface'
import GraphVisualization from './components/GraphVisualization'
import SettingsPanel from './components/SettingsPanel'
import BookManager from './components/BookManager'
import './App.css'

function App() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [showSettings, setShowSettings] = useState(false)
  const [showBooks, setShowBooks] = useState(true)
  const [selectedSources, setSelectedSources] = useState(null)
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
    console.log('Books processed')
  }

  // Resizable panes: left = books, middle = chat, right = graph (flex)
  const containerRef = useRef(null)
  const [leftWidth, setLeftWidth] = useState(300)
  const [chatWidth, setChatWidth] = useState(600)
  const draggingRef = useRef(null)



  const startDrag = (type, e) => {
    draggingRef.current = {
      type,
      startX: e.clientX,
      startLeftWidth: leftWidth,
      startChatWidth: chatWidth
    }
    document.body.style.cursor = 'col-resize'
    e.preventDefault()
  }

  // Refresh coordination
  const [refreshBooksTrigger, setRefreshBooksTrigger] = useState(0)

  const handleBookAdded = () => {
    setRefreshBooksTrigger(prev => prev + 1)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="ascii-header">╔════════════════════════════════════════╗
          ║   Knowledge Graph RAG System           ║
          ╚════════════════════════════════════════╝</h1>
        <div className="header-actions">
          <motion.button
            className={`toggle-button ${showBooks ? 'active' : ''}`}
            onClick={() => setShowBooks(!showBooks)}
            title="Toggle Books Panel"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            ┌─ Books ─┐
          </motion.button>
          <motion.button
            className="settings-button"
            onClick={() => setShowSettings(!showSettings)}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            ⚙ Settings
          </motion.button>
        </div>
      </header>

      {showSettings && (
        <SettingsPanel
          settings={settings}
          onSettingsChange={setSettings}
          onClose={() => setShowSettings(false)}
        />
      )}

      <div className="app-content" ref={containerRef}>
        {showBooks && (
          <motion.div
            className="books-panel"
            style={{ width: leftWidth }}
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -20, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <BookManager
              onBooksProcessed={handleBooksProcessed}
              selectedSources={selectedSources}
              onSourcesChange={setSelectedSources}
              refreshTrigger={refreshBooksTrigger}
            />
          </motion.div>
        )}

        {/* Resizer between Books and Chat */}
        {showBooks && <div className="resizer" onMouseDown={(e) => startDrag('left', e)} />}

        <div className="chat-panel" style={{ width: chatWidth }}>
          <ChatInterface
            onGraphUpdate={handleGraphUpdate}
            settings={settings}
            selectedSources={selectedSources}
            onBookAdded={handleBookAdded}
          />
        </div>

        {/* Resizer between Chat and Graph */}
        <div className="resizer" onMouseDown={(e) => startDrag('right', e)} />

        <div className="graph-panel">
          <GraphVisualization graphData={graphData} />
        </div>
      </div>
    </div>
  )
}

export default App
