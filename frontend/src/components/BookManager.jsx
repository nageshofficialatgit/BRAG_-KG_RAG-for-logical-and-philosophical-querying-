import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import './BookManager.css'

const API_BASE = '/api'

function BookManager({ onBooksProcessed, selectedSources, onSourcesChange, refreshTrigger }) {
  const [books, setBooks] = useState([])
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState({})
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    loadBooks()
    loadSources()
  }, [refreshTrigger])

  const loadBooks = async () => {
    try {
      const response = await axios.get(`${API_BASE}/books/list`, {
        timeout: 30000 // 30s timeout
      })
      console.debug('Loaded books:', response.data)
      setBooks(response.data.books || [])
    } catch (error) {
      console.error('Error loading books:', error)
    }
  }

  const loadSources = async () => {
    try {
      const response = await axios.get(`${API_BASE}/books/sources/list`, {
        timeout: 30000
      })
      console.debug('Loaded sources:', response.data)
      setSources(response.data.sources || [])
    } catch (error) {
      console.error('Error loading sources:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    try {
      await axios.post(`${API_BASE}/books/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      await loadBooks()
    } catch (error) {
      console.error('Error uploading file:', error)
      alert(`Error uploading file: ${error.response?.data?.detail || error.message}`)
    } finally {
      setUploading(false)
      // Reset input
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const handleProcessBook = async (filename) => {
    setProcessing({ ...processing, [filename]: true })
    try {
      const response = await axios.post(`${API_BASE}/books/process`, {
        filename,
        llm_provider: 'ollama',
        overwrite: false
      })

      if (response.data.success) {
        await loadSources()
        if (onBooksProcessed) onBooksProcessed()
      }
    } catch (error) {
      console.error('Error processing book:', error)
      alert(`Error: ${error.response?.data?.detail || error.message}`)
    } finally {
      setProcessing({ ...processing, [filename]: false })
    }
  }

  const handleProcessAll = async () => {
    if (!confirm('Process all books? This may take a while.')) return

    setLoading(true)
    try {
      const filenames = books.map(b => b.filename)
      const response = await axios.post(`${API_BASE}/books/process-multiple`, {
        filenames,
        llm_provider: 'ollama',
        overwrite: false
      })

      if (response.data.success) {
        await loadSources()
        if (onBooksProcessed) onBooksProcessed()
        alert(`Processed ${response.data.processed} books successfully!`)
      } else {
        alert(`Some errors occurred: ${response.data.errors.join(', ')}`)
      }
    } catch (error) {
      console.error('Error processing books:', error)
      alert(`Error: ${error.response?.data?.detail || error.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteBook = async (filename) => {
    if (!confirm(`Delete ${filename}?`)) return

    try {
      await axios.delete(`${API_BASE}/books/${filename}`)
      await loadBooks()
    } catch (error) {
      console.error('Error deleting book:', error)
      alert(`Error: ${error.response?.data?.detail || error.message}`)
    }
  }

  const isSourceProcessed = (bookName) => {
    return sources.some(s => s.source === bookName)
  }

  const getSourceStats = (bookName) => {
    return sources.find(s => s.source === bookName)
  }

  const toggleSourceSelection = (sourceName) => {
    console.debug('Toggling source:', sourceName, 'Current selection:', selectedSources)

    // Case 1: Currently "All Selected" (null)
    // We want to unselect this specific item, so we select everything ELSE.
    if (selectedSources === null) {
      if (!sources || sources.length === 0) {
        console.warn('Cannot toggle source: Source list is empty')
        return
      }

      const allOtherSources = sources
        .filter(s => s.source !== sourceName)
        .map(s => s.source)

      console.debug('Transitioning from All to Subset:', allOtherSources)
      onSourcesChange(allOtherSources)
      return
    }

    // Case 2: Currently a Subset
    if (selectedSources.includes(sourceName)) {
      // Removing item
      const newSelection = selectedSources.filter(s => s !== sourceName)
      console.debug('Removing source. New selection:', newSelection)
      onSourcesChange(newSelection)
    } else {
      // Adding item
      const newSelection = [...selectedSources, sourceName]
      console.debug('Adding source. New selection:', newSelection)
      // Note: We deliberately do NOT revert to 'null' (All) here even if valid.
      // This keeps the behavior deterministic (All = user explicitly clicked All).
      onSourcesChange(newSelection)
    }
  }

  const containerVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1, transition: { staggerChildren: 0.05 } }
  }

  const itemVariants = {
    initial: { opacity: 0, x: -10 },
    animate: { opacity: 1, x: 0 }
  }

  return (
    <div className="book-manager">
      <div className="book-manager-header">
        <h3>┌─ Books ─┐</h3>
        <div className="book-manager-actions">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            accept=".txt,.md,.pdf"
          />
          <motion.button
            className="attach-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            {uploading ? '...' : '+ Attach'}
          </motion.button>
          <motion.button
            className="refresh-button"
            onClick={() => { loadBooks(); loadSources(); }}
            title="Refresh"
            whileHover={{ scale: 1.1, rotate: 90 }}
            whileTap={{ scale: 0.95 }}
            transition={{ type: 'spring', stiffness: 400 }}
          >
            ⟳
          </motion.button>
          <motion.button
            className="process-all-button"
            onClick={handleProcessAll}
            disabled={loading || books.length === 0}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {loading ? '⟳...' : '► All'}
          </motion.button>
        </div>
      </div>

      <div className="sources-filter">
        <h4>┌─ Filter ─┐</h4>
        <motion.div
          className="source-checkboxes"
          variants={containerVariants}
          initial="initial"
          animate="animate"
        >
          <motion.label variants={itemVariants}>
            <input
              type="checkbox"
              // Checked if state is null (explicit All) OR if manual selection covers all sources
              checked={selectedSources === null || (sources.length > 0 && selectedSources.length === sources.length)}
              // Clicking always toggles to explicit All (null) or None ([])
              onChange={() => {
                const isAll = selectedSources === null || (sources.length > 0 && selectedSources.length === sources.length)
                onSourcesChange(isAll ? [] : null)
              }}
            />
            All Sources
          </motion.label>
          {/* Individual sources list removed - moved to book cards */}
        </motion.div>
      </div>

      <div className="books-list">
        {books.length === 0 ? (
          <motion.div
            className="empty-state"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <p>No books found</p>
            <p className="hint">Attach files to get started</p>
          </motion.div>
        ) : (
          <motion.div
            className="books-list-container"
          >
            {books.map(book => {
              const isProcessed = isSourceProcessed(book.name)
              const stats = getSourceStats(book.name)

              return (
                <motion.div
                  key={book.filename}
                  className={`book-item ${isProcessed ? 'processed' : 'unprocessed'}`}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  whileHover={{ x: 4 }}
                >
                  <div className="book-info">
                    <div className="book-name">
                      <span className={`status-dot ${isProcessed ? 'status-green' : 'status-grey'}`}>
                        {isProcessed ? '●' : '○'}
                      </span>
                      ▪ {book.name}
                    </div>
                    <div className="book-meta">
                      {book.size_mb} MB • {book.extension.toUpperCase()}
                      {isProcessed && stats && (
                        <span className="processed-badge">
                          ✓ {stats.nodes}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="book-select">
                    <label title={isProcessed ? "Use this source for answers" : "Source not processed yet (will return no results)"}>
                      <input
                        type="checkbox"
                        checked={selectedSources === null || (sources.length > 0 && selectedSources.length === sources.length) ? true : selectedSources.includes(book.name)}
                        onChange={(e) => {
                          e.stopPropagation()
                          toggleSourceSelection(book.name)
                        }}
                      />
                      <span>Use</span>
                    </label>
                  </div>
                  <div className="book-actions">
                    <motion.button
                      className={`process-button ${isProcessed ? 'processed' : ''}`}
                      onClick={() => handleProcessBook(book.filename)}
                      disabled={processing[book.filename]}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      {processing[book.filename] ? '⟳' : isProcessed ? '↻' : '►'}
                    </motion.button>
                    <motion.button
                      className="delete-button"
                      onClick={() => handleDeleteBook(book.filename)}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      ✕
                    </motion.button>
                  </div>
                </motion.div>
              )
            })}
          </motion.div>
        )}
      </div>
    </div >
  )
}

export default BookManager
