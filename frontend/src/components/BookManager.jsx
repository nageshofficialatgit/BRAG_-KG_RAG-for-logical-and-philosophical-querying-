import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import './BookManager.css'

const API_BASE = '/api'

function BookManager({ onBooksProcessed, selectedSources, onSourcesChange }) {
  const [books, setBooks] = useState([])
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState({})

  useEffect(() => {
    loadBooks()
    loadSources()
  }, [])

  const loadBooks = async () => {
    try {
      const response = await axios.get(`${API_BASE}/books/list`)
      setBooks(response.data.books || [])
    } catch (error) {
      console.error('Error loading books:', error)
    }
  }

  const loadSources = async () => {
    try {
      const response = await axios.get(`${API_BASE}/books/sources/list`)
      setSources(response.data.sources || [])
    } catch (error) {
      console.error('Error loading sources:', error)
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
    if (!selectedSources) {
      onSourcesChange([sourceName])
      return
    }

    if (selectedSources.includes(sourceName)) {
      onSourcesChange(selectedSources.filter(s => s !== sourceName))
    } else {
      onSourcesChange([...selectedSources, sourceName])
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
              checked={!selectedSources || selectedSources.length === 0}
              onChange={() => onSourcesChange([])}
            />
            All Sources
          </motion.label>
          <AnimatePresence>
            {sources.map(source => (
              <motion.label 
                key={source.source}
                variants={itemVariants}
                initial="initial"
                animate="animate"
                exit={{ opacity: 0, x: -10 }}
              >
                <input
                  type="checkbox"
                  checked={selectedSources?.includes(source.source) || false}
                  onChange={() => toggleSourceSelection(source.source)}
                />
                {source.source} ({source.nodes})
              </motion.label>
            ))}
          </AnimatePresence>
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
            <p className="hint">Add files to reference_texts/</p>
          </motion.div>
        ) : (
          <motion.div
            variants={containerVariants}
            initial="initial"
            animate="animate"
          >
            {books.map(book => {
              const isProcessed = isSourceProcessed(book.name)
              const stats = getSourceStats(book.name)
              
              return (
                <motion.div 
                  key={book.filename} 
                  className="book-item"
                  variants={itemVariants}
                  whileHover={{ x: 4 }}
                >
                  <div className="book-info">
                    <div className="book-name">▪ {book.name}</div>
                    <div className="book-meta">
                      {book.size_mb} MB • {book.extension.toUpperCase()}
                      {isProcessed && stats && (
                        <span className="processed-badge">
                          ✓ {stats.nodes}
                        </span>
                      )}
                    </div>
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
    </div>
  )
}

export default BookManager
