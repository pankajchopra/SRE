"""
Response Refiner Tool
Adjusts tone and format of responses to match specified communication style.
"""

import logging
from typing import Dict, Any, List, Optional, Literal

from langchain.tools import BaseTool
from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

# Configure logging
logger = logging.getLogger(__name__)

class ResponseRefinerTool(BaseTool):
    """Tool for refining and adjusting response content and tone."""
    
    name = "response_refiner"
    description = """
    Refines and adjusts responses to match specified communication styles and formats.
    Use this tool to adjust the tone, summarize lengthy content, or format responses
    in a specific way (professional, casual, technical, simple, etc.).
    """
    
    def __init__(self, llm: BaseChatModel):
        """
        Initialize the response refiner tool.
        
        Args:
            llm: Language model for response refinement
        """
        super().__init__()
        self.llm = llm
    
    def _adjust_tone(self, content: str, tone: str) -> str:
        """
        Adjust the tone of the content.
        
        Args:
            content: Original content
            tone: Target tone (professional, casual, technical, simple, etc.)
            
        Returns:
            Content with adjusted tone
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
                You are a communication specialist who adjusts the tone and style of text.
                Your task is to rewrite the given content to match a {tone} tone.
                
                Guidelines for {tone} tone:
                {self._get_tone_guidelines(tone)}
                
                Keep the same information and meaning, but adjust the style and language.
                Do not add new information or remove important details.
                """),
                ("human", f"Content to adjust:\n\n{content}")
            ])
            
            response = self.llm.invoke(prompt.format_messages())
            adjusted_content = response.content.strip()
            
            return adjusted_content
            
        except Exception as e:
            logger.error(f"Error adjusting tone: {e}")
            return content  # Return original content if processing fails
    
    def _get_tone_guidelines(self, tone: str) -> str:
        """
        Get guidelines for the specified tone.
        
        Args:
            tone: Target tone
            
        Returns:
            Tone guidelines
        """
        tone_guidelines = {
            "professional": """
            - Use formal language and avoid contractions
            - Maintain a respectful and objective tone
            - Use industry-appropriate terminology
            - Be concise and clear
            - Avoid casual expressions and slang
            - Structure information logically with clear transitions
            """,
            
            "casual": """
            - Use conversational language with contractions
            - Include some personality and warmth
            - Use accessible vocabulary and examples
            - Feel free to use casual expressions (but avoid excessive slang)
            - Be friendly and relatable
            """,
            
            "technical": """
            - Use precise technical terminology
            - Be detailed and specific
            - Structure information in a logical sequence
            - Include relevant technical details
            - Maintain accuracy and precision
            - Use industry-standard formatting where appropriate
            """,
            
            "simple": """
            - Use plain language and short sentences
            - Avoid jargon and complex terms
            - Explain concepts in straightforward ways
            - Use concrete examples
            - Break down complex ideas into simpler parts
            - Prioritize clarity over comprehensiveness
            """,
            
            "educational": """
            - Explain concepts clearly with definitions
            - Use examples and analogies
            - Build from basic to more complex ideas
            - Include some repetition of key points
            - Use a supportive and encouraging tone
            - Ask rhetorical questions to prompt thinking
            """,
            
            "empathetic": """
            - Show understanding of concerns and feelings
            - Use warm and compassionate language
            - Acknowledge difficulties or challenges
            - Offer supportive and reassuring statements
            - Use inclusive language
            - Balance emotional support with practical help
            """
        }
        
        return tone_guidelines.get(tone.lower(), "- Use clear and concise language\n- Be helpful and informative")
    
    def _summarize_content(self, content: str, length: Literal['brief', 'medium', 'detailed'] = 'medium') -> str:
        """
        Summarize content to the specified length.
        
        Args:
            content: Original content
            length: Target summary length (brief, medium, detailed)
            
        Returns:
            Summarized content
        """
        try:
            # Define length parameters
            length_guidelines = {
                'brief': "2-3 sentences, capturing only the most essential points",
                'medium': "a paragraph or two, including key details and main points",
                'detailed': "a comprehensive summary that preserves most details while condensing redundant content"
            }
            
            guideline = length_guidelines.get(length, length_guidelines['medium'])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
                You are a skilled content summarizer. Your task is to create a {length} summary of the given content.
                
                For a {length} summary, aim for {guideline}.
                
                Retain the most important information, key points, and essential context.
                Use clear and concise language.
                Preserve the original meaning and intent.
                """),
                ("human", f"Content to summarize:\n\n{content}")
            ])
            
            response = self.llm.invoke(prompt.format_messages())
            summary = response.content.strip()
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing content: {e}")
            return content  # Return original content if processing fails
    
    def _format_content(self, content: str, format_type: str) -> str:
        """
        Format content according to the specified format type.
        
        Args:
            content: Original content
            format_type: Target format (bullet points, numbered list, Q&A, etc.)
            
        Returns:
            Formatted content
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
                You are a content formatting specialist. Your task is to reformat the given content 
                into a {format_type} format while preserving all important information.
                
                Guidelines for formatting:
                {self._get_format_guidelines(format_type)}
                
                Keep all important information intact while reformatting.
                """),
                ("human", f"Content to format:\n\n{content}")
            ])
            
            response = self.llm.invoke(prompt.format_messages())
            formatted_content = response.content.strip()
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error formatting content: {e}")
            return content  # Return original content if processing fails
    
    def _get_format_guidelines(self, format_type: str) -> str:
        """
        Get guidelines for the specified format type.
        
        Args:
            format_type: Target format
            
        Returns:
            Format guidelines
        """
        format_guidelines = {
            "bullet points": """
            - Convert the content into a series of concise bullet points
            - Start each point with a dash or bullet symbol
            - Group related points under clear headings if appropriate
            - Keep each point focused on a single idea
            - Use parallel structure for all points
            """,
            
            "numbered list": """
            - Convert the content into a numbered sequence of points
            - Use a logical ordering (chronological, priority, etc.)
            - Start each point with a number
            - Keep each point focused and concise
            - Use parallel structure for all points
            """,
            
            "q&a": """
            - Reformat the content as a series of questions and answers
            - Create clear, direct questions that address key points
            - Provide comprehensive answers to each question
            - Ensure questions flow logically from one to the next
            - Cover all important information from the original content
            """,
            
            "table": """
            - Identify information that can be organized into rows and columns
            - Create a clear table structure with headers
            - Organize information logically within the table
            - Use concise language for table entries
            - Include a brief introduction before the table if needed
            """,
            
            "step-by-step": """
            - Break the content into sequential steps
            - Number each step clearly
            - Begin with an introduction explaining the goal
            - Keep each step focused on a specific action
            - Add brief explanations where needed
            - End with a conclusion or expected outcome
            """
        }
        
        return format_guidelines.get(format_type.lower(), "- Organize information clearly and logically\n- Use appropriate formatting elements")
    
    def _parse_refinement_parameters(self, query: str) -> Dict[str, Any]:
        """
        Parse refinement parameters from the query.
        
        Args:
            query: Raw query with refinement parameters
            
        Returns:
            Dictionary of refin