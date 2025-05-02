"""
Enhanced Search Tool
Utilizes an LLM to rephrase and optimize search queries.
"""

import logging
from typing import Dict, Any, List, Optional

from langchain.tools import BaseTool
from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.tools import Tool
from langchain.memory.chat_memory import BaseChatMemory

# Configure logging
logger = logging.getLogger(__name__)

class EnhancedSearchTool(BaseTool):
    """Tool for enhanced search with query optimization."""
    
    name = "enhanced_search"
    description = """
    Performs internet searches with optimized queries based on the user's intent.
    Use this tool when the user needs factual information, current events, or data
    that would be available through web search.
    """
    
    def __init__(self, llm: BaseChatModel, api_key: Optional[str] = None, 
                 search_engine: str = 'google', top_k: int = 5,
                 memory: Optional[BaseChatMemory] = None):
        """
        Initialize the enhanced search tool.
        
        Args:
            llm: Language model for query optimization
            api_key: API key for search service
            search_engine: Search engine to use ('google', 'duckduckgo', etc.)
            top_k: Number of results to return
            memory: Optional memory for context
        """
        super().__init__()
        self.llm = llm
        self.api_key = api_key
        self.search_engine = search_engine
        self.top_k = top_k
        self.memory = memory
        
        # Initialize the search tool based on the search engine
        if search_engine.lower() == 'google':
            self.search_wrapper = GoogleSearchAPIWrapper(k=top_k)
            self.search_tool = Tool(
                name="google_search",
                description="Search Google for relevant information",
                func=self.search_wrapper.run
            )
        else:
            # Fallback to a mock search for demonstration
            self.search_tool = Tool(
                name="mock_search",
                description="Mock search implementation",
                func=self._mock_search
            )
    
    def _mock_search(self, query: str) -> str:
        """
        Mock search function for demonstration purposes.
        
        Args:
            query: Search query string
            
        Returns:
            Mock search results
        """
        return f"Mock search results for: {query}\n\n" + \
               "This is a placeholder for actual search results. " + \
               "In a production environment, this would connect to a real search API."
    
    def _optimize_query(self, original_query: str, conversation_context: Optional[str] = None) -> str:
        """
        Optimize the search query using an LLM.
        
        Args:
            original_query: Original user query
            conversation_context: Context from conversation history
            
        Returns:
            Optimized search query
        """
        try:
            context_str = ""
            if conversation_context:
                context_str = f"\nRelevant conversation context: {conversation_context}"
                
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
                You are a search query optimizer. Your task is to transform user questions into 
                effective search queries that will yield the most relevant results.
                
                Guidelines for optimization:
                1. Remove unnecessary words like "please", "I want to know", etc.
                2. Include specific keywords relevant to the topic
                3. Use precise terminology where possible
                4. Add disambiguating terms if the query could be interpreted multiple ways
                5. Focus on the core information need{context_str}
                """),
                ("human", f"Original query: {original_query}")
            ])
            
            response = self.llm.invoke(prompt.format_messages())
            optimized_query = response.content.strip()
            
            logger.info(f"Optimized query: '{original_query}' → '{optimized_query}'")
            return optimized_query
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return original_query  # Fall back to original query
    
    def _extract_conversation_context(self) -> Optional[str]:
        """
        Extract relevant context from conversation history.
        
        Returns:
            Relevant conversation context or None
        """
        if not self.memory:
            return None
            
        try:
            # Get recent conversation history
            history = self.memory.load_memory_variables({})
            
            if not history or 'chat_history' not in history:
                return None
                
            # Extract last few exchanges
            recent_messages = history['chat_history'][-6:]  # Last 3 exchanges (user and assistant)
            
            context = "\n".join([f"{msg.type}: {msg.content}" for msg in recent_messages])
            return context
            
        except Exception as e:
            logger.error(f"Error extracting conversation context: {e}")
            return None
    
    def _format_search_results(self, results: str) -> str:
        """
        Format search results for better readability.
        
        Args:
            results: Raw search results
            
        Returns:
            Formatted search results
        """
        # In a real implementation, this would parse structured results
        # and format them in a user-friendly way
        # For the mock version, we'll just return the results
        return results
    
    def _run(self, query: str) -> str:
        """
        Run the enhanced search tool.
        
        Args:
            query: User query string
            
        Returns:
            Search results
        """
        try:
            logger.info(f"Processing search query: {query}")
            
            # Extract conversation context if available
            context = self._extract_conversation_context()
            
            # Optimize the query
            optimized_query = self._optimize_query(query, context)
            
            # skip the search tool
            # Run the search
            # search_results = self.search_tool.run(optimized_query)
            
            # Format the results
            # formatted_results = self._format_search_results(search_results)
            
            # Add context about query optimization
            # response = f"Search results for optimized query: \"{optimized_query}\"\n\n"
            # response += formatted_results
            # response += "\n\nNote: These search results are based on publicly available information and may not be completely up to date."
            
            return response
            
        except Exception as e:
            logger.error(f"Error in enhanced search tool: {e}")
            return f"Error performing search: {str(e)}"
