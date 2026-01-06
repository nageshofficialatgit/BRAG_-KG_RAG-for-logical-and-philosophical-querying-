import React, { useState, useEffect } from 'react'
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

  return (
    <div className="book-manager">
      <div className="book-manager-header">
        <h3>Reference Books</h3>
        <div className="book-manager-actions">
          <button
            className="refresh-button"
            onClick={() => { loadBooks(); loadSources(); }}
            title="Refresh"
          >
            🔄
          </button>
          <button
            className="process-all-button"
            onClick={handleProcessAll}
            disabled={loading || books.length === 0}
          >
            {loading ? 'Processing...' : 'Process All'}
          </button>
        </div>
      </div>

      <div className="sources-filter">
        <h4>Filter by Source:</h4>
        <div className="source-checkboxes">
          <label>
            <input
              type="checkbox"
              checked={!selectedSources || selectedSources.length === 0}
              onChange={() => onSourcesChange([])}
            />
            All Sources
          </label>
          {sources.map(source => (
            <label key={source.source}>
              <input
                type="checkbox"
                checked={selectedSources?.includes(source.source) || false}
                onChange={() => toggleSourceSelection(source.source)}
              />
              {source.source} ({source.nodes} nodes)
            </label>
          ))}
        </div>
      </div>

      <div className="books-list">
        {books.length === 0 ? (
          <div className="empty-state">
            <p>No books found in reference_texts folder.</p>
            <p className="hint">Add .txt, .md, or .pdf files to the reference_texts folder.</p>
          </div>
        ) : (
          books.map(book => {
            const isProcessed = isSourceProcessed(book.name)
            const stats = getSourceStats(book.name)
            
            return (
              <div key={book.filename} className="book-item">
                <div className="book-info">
                  <div className="book-name">{book.name}</div>
                  <div className="book-meta">
                    {book.size_mb} MB • {book.extension.toUpperCase()}
                    {isProcessed && stats && (
                      <span className="processed-badge">
                        ✓ {stats.nodes} nodes, {stats.relationships} rels
                      </span>
                    )}
                  </div>
                </div>
                <div className="book-actions">
                  <button
                    className={`process-button ${isProcessed ? 'processed' : ''}`}
                    onClick={() => handleProcessBook(book.filename)}
                    disabled={processing[book.filename]}
                  >
                    {processing[book.filename] ? 'Processing...' : isProcessed ? 'Reprocess' : 'Process'}
                  </button>
                  <button
                    className="delete-button"
                    onClick={() => handleDeleteBook(book.filename)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default BookManager
