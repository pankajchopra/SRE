"""
Document Processing Tool
Extracts and processes text from documents using LightRAG.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union

from langchain.tools import BaseTool

# Configure logging
logger = logging.getLogger(__name__)

class DocumentProcessorTool(BaseTool):
    """Tool for processing and extracting information from documents."""
    
    name = "document_processor"
    description = """
    Processes and extracts information from documents like PDFs, Word documents, and text files.
    Use this tool when the user uploads documents or needs information extracted from specific files.
    """
    
    def __init__(self, rag_manager):
        """
        Initialize the document processor tool.
        
        Args:
            rag_manager: The LightRAG manager instance for document processing
        """
        super().__init__()
        self.rag_manager = rag_manager
    
    def _extract_file_paths(self, query: str) -> List[str]:
        """
        Extract file paths from the query.
        
        Args:
            query: User query string
            
        Returns:
            List of file paths mentioned in the query
        """
        # This is a simplified implementation
        # In a real system, you would use a more sophisticated approach
        # to detect file paths or references in the query
        
        import re
        
        # Look for common file patterns and extensions
        file_patterns = [
            # Quoted file paths
            r'"([^"]+\.(pdf|docx?|txt|csv|xlsx?))"',
            r"'([^']+\.(pdf|docx?|txt|csv|xlsx?))'",
            
            # Unquoted paths with extensions
            r'\b([a-zA-Z0-9_\-\.\/\\]+\.(pdf|docx?|txt|csv|xlsx?))\b',
            
            # References to "the file X" or "document X"
            r'(?:the\s+)?(?:file|document|pdf|doc|text file|excel file|spreadsheet|csv)\s+(?:called|named)?\s+"([^"]+)"',
            r"(?:the\s+)?(?:file|document|pdf|doc|text file|excel file|spreadsheet|csv)\s+(?:called|named)?\s+'([^']+)'",
        ]
        
        file_paths = []
        for pattern in file_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                # Handle tuple returns from regex groups
                if isinstance(match, tuple):
                    file_paths.append(match[0])
                else:
                    file_paths.append(match)
        
        return file_paths
    
    def _process_document(self, file_path: str) -> Dict[str, Any]:
        """
        Process a document and extract its content.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary with document content and metadata
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {'error': f"File not found: {file_path}"}
            
            # Process based on file extension
            _, extension = os.path.splitext(file_path)
            extension = extension.lower()
            
            # Let the RAG manager handle the document processing
            return self.rag_manager.process_document(file_path)
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            return {'error': f"Error processing document: {str(e)}"}
    
    def _extract_specific_info(self, file_path: str, query: str) -> str:
        """
        Extract specific information from a document based on the query.
        
        Args:
            file_path: Path to the document file
            query: User query string
            
        Returns:
            Extracted information or error message
        """
        try:
            # Use the RAG manager to query the document
            return self.rag_manager.query_document(file_path, query)
            
        except Exception as e:
            logger.error(f"Error extracting info from {file_path}: {e}")
            return f"Error extracting information: {str(e)}"
    
    def _summarize_document(self, file_path: str) -> str:
        """
        Generate a summary of the document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Document summary
        """
        try:
            # Use the RAG manager to summarize the document
            return self.rag_manager.summarize_document(file_path)
            
        except Exception as e:
            logger.error(f"Error summarizing {file_path}: {e}")
            return f"Error generating summary: {str(e)}"
    
    def _run(self, query: str) -> str:
        """
        Process the document based on the query.
        
        Args:
            query: User query string
            
        Returns:
            Document processing results
        """
        try:
            logger.info(f"Processing document query: {query}")
            
            # Extract file paths from the query
            file_paths = self._extract_file_paths(query)
            
            if not file_paths:
                return """No document file paths found in your request. 
                Please specify the document file(s) you want to process, for example:
                - "Extract information from report.pdf"
                - "Summarize the content of financial_data.docx"
                - "What does the document 'meeting_notes.txt' say about the project timeline?"
                """
            
            # Determine the operation based on the query
            query_lower = query.lower()
            
            # Process each file
            results = []
            
            for file_path in file_paths:
                # Determine what operation to perform
                if 'summary' in query_lower or 'summarize' in query_lower:
                    result = self._summarize_document(file_path)
                    results.append(f"Summary of {os.path.basename(file_path)}:\n\n{result}")
                    
                elif any(term in query_lower for term in ['extract', 'find', 'what does it say', 'what does the document say']):
                    # Extract specific information
                    result = self._extract_specific_info(file_path, query)
                    results.append(f"Information from {os.path.basename(file_path)}:\n\n{result}")
                    
                else:
                    # Default to general processing
                    result = self._process_document(file_path)
                    
                    if 'error' in result:
                        results.append(f"Error processing {os.path.basename(file_path)}: {result['error']}")
                    else:
                        metadata = result.get('metadata', {})
                        content_preview = result.get('content', '')[:500] + '...' if len(result.get('content', '')) > 500 else result.get('content', '')
                        
                        file_info = f"Document: {os.path.basename(file_path)}\n"
                        file_info += f"Type: {metadata.get('type', 'Unknown')}\n"
                        file_info += f"Pages: {metadata.get('pages', 'Unknown')}\n"
                        file_info += f"Size: {metadata.get('size', 'Unknown')}\n\n"
                        file_info += f"Content Preview:\n{content_preview}"
                        
                        results.append(file_info)
            
            # Combine results
            return "\n\n" + "\n\n---\n\n".join(results)
            
        except Exception as e:
            logger.error(f"Error in document processor tool: {e}")
            return f"Error processing document request: {str(e)}"
