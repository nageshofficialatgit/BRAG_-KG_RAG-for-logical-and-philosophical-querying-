# Reference Texts Folder - User Guide

## Overview

The system now supports managing multiple reference books in a dedicated folder. You can:
- Add books to the `reference_texts/` folder
- Process books individually or in bulk to create knowledge graphs
- Filter queries by specific books
- View which books are processed in the knowledge graph

## Adding Books

### Method 1: Direct File Placement
1. Place your book files (`.txt`, `.md`, or `.pdf`) in the `reference_texts/` folder
2. Use descriptive filenames like:
   - `aristotle_nicomachean_ethics.txt`
   - `hume_treatise_human_nature.md`
   - `kant_critique_pure_reason.pdf`

### Method 2: Via API
Use the `/api/books/add` endpoint to add books programmatically.

### Method 3: Via Frontend
The frontend will show all books in the folder automatically.

## Processing Books

### Individual Processing
1. Open the Books panel (click "📚 Books" button)
2. Find your book in the list
3. Click "Process" to create a knowledge graph from that book
4. The system will extract entities and relationships

### Bulk Processing
1. Click "Process All" to process all books in the folder
2. This may take a while depending on the number and size of books

### Processing Status
- ✓ Green badge: Book is processed (shows node/relationship counts)
- No badge: Book not yet processed
- "Reprocess" button: Re-process an already processed book

## Filtering Queries by Books

### Using Source Filter
1. In the Books panel, use the "Filter by Source" section
2. Check/uncheck specific books to filter queries
3. When checked, queries will only retrieve information from selected books
4. "All Sources" retrieves from all processed books

### Example Use Cases
- **Compare philosophers**: Select only Aristotle's book to ask about his views
- **Cross-reference**: Select multiple books to see how different authors discuss the same topic
- **Focused research**: Filter to specific books when researching a particular concept

## API Endpoints

### List Books
```
GET /api/books/list
```
Returns all books in the reference_texts folder.

### Get Book Info
```
GET /api/books/{filename}
```
Returns detailed information about a specific book.

### Process Book
```
POST /api/books/process
{
  "filename": "aristotle_ethics.txt",
  "llm_provider": "ollama",
  "model": "llama3.2",
  "overwrite": false
}
```

### Process Multiple Books
```
POST /api/books/process-multiple
{
  "filenames": ["book1.txt", "book2.txt"],
  "llm_provider": "ollama",
  "overwrite": false
}
```

### List Sources in Graph
```
GET /api/books/sources/list
```
Returns all books that have been processed and are in the knowledge graph.

### Delete Book
```
DELETE /api/books/{filename}
```

## Knowledge Graph Structure

When books are processed:
- Each book becomes a "source" in the knowledge graph
- Entities and relationships are tagged with the source
- You can query by source to filter results
- Multiple books create a unified knowledge graph

## Best Practices

1. **File Naming**: Use clear, descriptive names without spaces
   - Good: `aristotle_nicomachean_ethics.txt`
   - Bad: `book1.txt` or `my book.txt`

2. **File Organization**: Keep related books together
   - Group by author, topic, or time period

3. **Processing Order**: Process books in logical order
   - Start with foundational texts
   - Then process texts that reference them

4. **Source Filtering**: Use source filtering for focused queries
   - When comparing views, select specific books
   - When researching broadly, use "All Sources"

5. **Reprocessing**: Reprocess books if you update the content
   - Use `overwrite: true` to replace existing graph data

## Troubleshooting

### Book Not Appearing
- Check file is in `reference_texts/` folder
- Verify file extension is `.txt`, `.md`, or `.pdf`
- Click refresh button in Books panel

### Processing Fails
- Check Neo4j connection
- Verify LLM (Ollama/OpenAI) is available
- Check file encoding (should be UTF-8 for text files)
- Review error message in console

### Query Not Finding Information
- Verify book is processed (check for green badge)
- Check source filter settings
- Try "All Sources" to see if data exists
- Verify entities are extracted correctly

## Example Workflow

1. **Add Books**:
   ```
   reference_texts/
   ├── aristotle_ethics.txt
   ├── hume_treatise.txt
   └── kant_critique.txt
   ```

2. **Process All Books**:
   - Click "Process All" in Books panel
   - Wait for processing to complete

3. **Query with Filtering**:
   - Select only "aristotle_ethics" in source filter
   - Ask: "What does Aristotle say about virtue?"
   - System retrieves only from Aristotle's book

4. **Cross-Reference**:
   - Select all three books
   - Ask: "How do Aristotle, Hume, and Kant differ on free will?"
   - System retrieves from all selected books

## Technical Details

- Books are stored as `Document` nodes in Neo4j with `source` property
- Source filtering uses Cypher queries to match documents by source
- Processing uses LangChain's `LLMGraphTransformer` to extract entities
- Each book maintains separate statistics (nodes, relationships)
