"""
LightRAG-enhanced Agentic Chatbot
Main application that ties together all components.
"""

import os
import logging
from typing import List, Dict, Any, Optional

import litellm
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.agents import AgentExecutor
from langchain.agents.agent_types import AgentType
from langchain.agents import create_react_agent, load_tools
from langchain.schema import SystemMessage
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

from tools.query_router import QueryRouterTool
from tools.stock_info import StockInfoTool
from tools.account_api import AccountAPITool
from tools.enhanced_search import EnhancedSearchTool
from tools.document_processor import DocumentProcessorTool
from tools.response_refiner import ResponseRefinerTool
from rag.lightrag_manager import LightRAGManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure environment (in production, use proper environment variables)
os.environ["OPENAI_API_KEY"] = "your-api-key"  # Replace with actual API key management

class AgenticChatbot:
    """Main chatbot class that integrates all components."""
    
    def __init__(self, model_name: str = "gpt-4o", temperature: float = 0.1):
        """
        Initialize the agentic chatbot with all required components.
        
        Args:
            model_name: The LLM model to use
            temperature: Creativity level for the LLM
        """
        self.model_name = model_name
        self.temperature = temperature
        
        # Initialize RAG system
        self.rag_manager = LightRAGManager()
        
        # Set up LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            streaming=True,
            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
        )
        
        # Set up memory system
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Create the agent
        self.agent = self._create_agent()
        
    def _initialize_tools(self) -> List[BaseTool]:
        """Initialize all the tools needed by the agent."""
        
        # Create individual tools
        stock_tool = StockInfoTool()
        account_tool = AccountAPITool()
        search_tool = EnhancedSearchTool(llm=self.llm)
        document_tool = DocumentProcessorTool(rag_manager=self.rag_manager)
        response_tool = ResponseRefinerTool(llm=self.llm)
        
        # Create the meta-tool for routing
        router_tool = QueryRouterTool(
            llm=self.llm,
            tools=[stock_tool, account_tool, search_tool, document_tool, response_tool]
        )
        
        # Combine all tools
        tools = [
            router_tool,
            stock_tool,
            account_tool, 
            search_tool,
            document_tool,
            response_tool
        ]
        
        # Add standard tools
        standard_tools = load_tools(["llm-math"], llm=self.llm)
        tools.extend(standard_tools)
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the ReAct agent with the defined tools and memory."""
        
        # System message that defines the agent's behavior
        system_message = SystemMessage(
            content="""You are an intelligent assistant that helps users by routing their queries to the most appropriate tools.
            
            Follow these guidelines:
            1. Analyze each query to understand what information or action is needed
            2. Select the most appropriate tool to handle the request
            3. Use the QueryRouterTool when you're unsure which tool to use
            4. Maintain conversation context across interactions
            5. Use retrieval-augmented generation when appropriate to enhance responses
            6. Keep responses concise and informative
            
            Available specialized tools:
            - QueryRouterTool: Analyzes queries and routes to the most appropriate tool
            - StockInfoTool: Fetches stock ticker information from Yahoo Finance
            - AccountAPITool: Interfaces with the account API for user data
            - EnhancedSearchTool: Performs optimized search queries with context
            - DocumentProcessorTool: Extracts and processes text from documents
            - ResponseRefinerTool: Adjusts tone and format of responses
            
            When given a query, first consider which tool would be most appropriate before responding.
            """
        )
        
        # Define the prompt for the agent
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="input"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create the agent
        agent = create_react_agent(
            self.llm,
            self.tools,
            prompt
        )
        
        # Create the agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            handle_parsing_errors=True,
            max_iterations=10,
            verbose=True
        )
    
    def process_query(self, query: str) -> str:
        """
        Process a user query and return the response.
        
        Args:
            query: The user's query text
            
        Returns:
            The agent's response
        """
        try:
            logger.info(f"Processing query: {query}")
            
            # First, see if RAG can enhance the context
            enhanced_query = self.rag_manager.enhance_query(query, self.memory)
            
            # Run the agent
            response = self.agent.run(input=enhanced_query)
            
            logger.info(f"Generated response: {response}")
            return response
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return f"I encountered an error while processing your request: {str(e)}"
    
    def load_documents(self, file_paths: List[str]) -> str:
        """
        Load documents into the RAG system.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            Status message
        """
        try:
            result = self.rag_manager.load_documents(file_paths)
            return f"Successfully loaded {len(file_paths)} documents into the knowledge base."
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return f"Error loading documents: {str(e)}"

def main():
    """Main function to run the chatbot."""
    print("Initializing Agentic Chatbot with LightRAG...")
    chatbot = AgenticChatbot()
    
    print("\nAgentic Chatbot is ready! Type 'exit' to quit.")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        # Special command to load documents
        if user_input.lower().startswith("load documents:"):
            file_paths = user_input[len("load documents:"):].strip().split(",")
            file_paths = [path.strip() for path in file_paths]
            result = chatbot.load_documents(file_paths)
            print(f"\nChatbot: {result}")
            continue
        
        response = chatbot.process_query(user_input)
        print(f"\nChatbot: {response}")

if __name__ == "__main__":
    main()
