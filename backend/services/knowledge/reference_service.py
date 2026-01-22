import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from pypdf import PdfReader

logger = logging.getLogger(__name__)

class ReferenceService:
    def __init__(self, reference_folder: str = None):
        # Make reference folder deterministic relative to repository root
        if reference_folder:
            self.reference_folder = Path(reference_folder)
        else:
            # Resolve to repository root (three levels up from this file)
            self.reference_folder = Path(__file__).resolve().parent.parent.parent / "reference_texts"
        self.reference_folder.mkdir(parents=True, exist_ok=True)
        self.supported_extensions = {'.txt', '.md', '.pdf'}
    
    def get_all_books(self) -> List[Dict[str, Any]]:
        """Get list of all books in the reference folder"""
        books = []
        
        if not self.reference_folder.exists():
            return books
        
        for file_path in self.reference_folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                try:
                    stat = file_path.stat()
                    books.append({
                        "filename": file_path.name,
                        "name": file_path.stem,
                        "extension": file_path.suffix.lower(),
                        "size": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": stat.st_mtime,
                        "path": str(file_path)
                    })
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {str(e)}")
        
        return sorted(books, key=lambda x: x["name"])
    
    def read_book_content(self, filename: str) -> Optional[str]:
        """Read content from a book file"""
        file_path = self.reference_folder / filename
        
        if not file_path.exists():
            logger.error(f"File not found: {filename}")
            return None
        
        try:
            extension = file_path.suffix.lower()
            
            if extension == '.pdf':
                return self._read_pdf(file_path)
            else:
                # Read as text (txt, md, etc.)
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            return None
    
    def _read_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            reader = PdfReader(file_path)
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return "\n".join(text_parts)
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {str(e)}")
            raise
    
    def add_book_from_text(self, filename: str, content: str) -> Dict[str, Any]:
        """Add a new book from text content"""
        # Ensure filename has proper extension
        if not any(filename.endswith(ext) for ext in self.supported_extensions):
            filename = f"{filename}.txt"
        
        file_path = self.reference_folder / filename
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            stat = file_path.stat()
            return {
                "success": True,
                "filename": filename,
                "name": file_path.stem,
                "size": stat.st_size,
                "message": f"Book '{filename}' added successfully"
            }
        except Exception as e:
            logger.error(f"Error adding book {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_book(self, filename: str) -> Dict[str, Any]:
        """Delete a book file"""
        file_path = self.reference_folder / filename
        
        if not file_path.exists():
            return {
                "success": False,
                "error": f"File '{filename}' not found"
            }
        
        try:
            file_path.unlink()
            return {
                "success": True,
                "message": f"Book '{filename}' deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting book {filename}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_book_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific book"""
        file_path = self.reference_folder / filename
        
        if not file_path.exists():
            return None
        
        try:
            stat = file_path.stat()
            content = self.read_book_content(filename)
            word_count = len(content.split()) if content else 0
            
            return {
                "filename": filename,
                "name": file_path.stem,
                "extension": file_path.suffix.lower(),
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "word_count": word_count,
                "modified": stat.st_mtime,
                "path": str(file_path),
                "preview": content[:500] if content else ""  # First 500 chars
            }
        except Exception as e:
            logger.error(f"Error getting book info {filename}: {str(e)}")
            return None
    
    def process_all_books(self) -> List[str]:
        """Get list of all book filenames"""
        return [book["filename"] for book in self.get_all_books()]
