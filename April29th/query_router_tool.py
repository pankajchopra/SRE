"""
Query Router Tool
This tool analyzes incoming queries and routes them to the appropriate specialized tool.
"""

from typing import List, Dict, Any, Optional, Type
import logging

from langchain.tools import BaseTool
from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

class ToolSelection(BaseModel):
    """Model for the tool selection output."""
    tool_name: str = Field(..., description="The name of the selected tool")
    confidence: float = Field(..., description="Confidence score between 0 and 1")
    reasoning: str = Field(..., description="Reasoning behind the tool selection")

class QueryRouterTool(BaseTool):
    """
    A meta-tool that analyzes queries and routes them to appropriate specialized tools.
    """
    name = "query_router"
    description = """
    Analyzes the user query and identifies the most appropriate tool to handle it. 
    Use this when you need to determine which specialized tool would best address the user's request.
    """
    
    llm: BaseChatModel
    tools: List[BaseTool]
    
    def __init__(self, llm: BaseChatModel, tools: List[BaseTool]):
        """
        Initialize the query router tool.
        
        Args:
            llm: The LLM to use for classification
            tools: The list of available tools to route to
        """
        super().__init__()
        self.llm = llm
        self.tools = tools
        self.output_parser = PydanticOutputParser(pydantic_object=ToolSelection)
    
    def _get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all available tools."""
        descriptions = []
        for tool in self.tools:
            if tool.name != self.name:  # Skip self to avoid recursion
                descriptions.append(f"- {tool.name}: {tool.description}")
        
        return "\n".join(descriptions)
    
    def _run(self, query: str) -> str:
        """
        Run the query router to determine the best tool.
        
        Args:
            query: The user query to analyze
            
        Returns:
            A recommendation of which tool to use
        """
        try:
            logger.info(f"Routing query: {query}")
            
            # Create the prompt for tool selection
            tool_descriptions = self._get_tool_descriptions()
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
                You are a query analyzer that determines which tool is most appropriate for handling a user's query.
                
                Available tools:
                {tool_descriptions}
                
                Analyze the user's query and recommend the most appropriate tool.
                Consider the purpose and capabilities of each tool when making your decision.
                
                Respond with JSON in the following format:
                {self.output_parser.get_format_instructions()}
                """),
                ("human", f"User query: {query}")
            ])
            
            # Get LLM response
            response = self.llm.invoke(prompt.format_messages())
            
            # Parse the tool selection
            try:
                tool_selection = self.output_parser.parse(response.content)
                
                # Find the selected tool
                selected_tool = None
                for tool in self.tools:
                    if tool.name == tool_selection.tool_name:
                        selected_tool = tool
                        break
                
                if not selected_tool:
                    return f"Tool '{tool_selection.tool_name}' not found. Please use one of the available tools."
                
                recommendation = f"""
                Based on the query analysis:
                
                Recommended tool: {tool_selection.tool_name}
                Confidence: {tool_selection.confidence:.2f}
                Reasoning: {tool_selection.reasoning}
                
                Tool description: {selected_tool.description}
                """
                
                logger.info(f"Routed to: {tool_selection.tool_name} with confidence {tool_selection.confidence:.2f}")
                return recommendation
                
            except Exception as e:
                logger.error(f"Error parsing tool selection: {e}")
                return f"Error parsing tool selection: {str(e)}"
            
        except Exception as e:
            logger.error(f"Error in query router: {e}")
            return f"Error routing query: {str(e)}"
