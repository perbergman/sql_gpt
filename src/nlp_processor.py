"""
NLP Processor Module
Handles the processing of natural language prompts into structured intents
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import openai

logger = logging.getLogger(__name__)

class NLPProcessor:
    """
    Processes natural language prompts into structured intents for SQL generation
    """
    
    def __init__(self):
        """Initialize the NLP processor with OpenAI client"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.debug("NLP Processor initialized")
        
    def process(self, prompt: str) -> Dict[str, Any]:
        """
        Process a natural language prompt into a structured intent
        
        Args:
            prompt: Natural language prompt from the user
            
        Returns:
            A dictionary containing the structured intent
        """
        logger.info(f"Processing prompt: {prompt}")
        
        # Define the system message to guide the model
        system_message = """
        You are an expert PostgreSQL database engineer. Your task is to analyze natural language 
        requests and extract structured information needed to generate SQL queries.
        
        For each request, provide a JSON response with the following structure:
        {
            "operation_type": "CREATE_TABLE|ALTER_TABLE|SELECT|INSERT|UPDATE|DELETE|CREATE_INDEX|etc.",
            "entities": [{"name": "entity_name", "type": "table|view|index|etc."}],
            "fields": [{"name": "field_name", "data_type": "text|integer|etc.", "constraints": ["NOT NULL", "UNIQUE", etc.]}],
            "conditions": ["condition1", "condition2"],
            "relationships": [{"from": "table1.field1", "to": "table2.field2", "type": "one_to_many|many_to_one|etc."}],
            "advanced_features": {
                "partitioning": {"type": "range|list|hash", "by": "field_name"},
                "indexes": [{"name": "index_name", "fields": ["field1", "field2"], "type": "btree|hash|etc."}]
            },
            "explanation": "Brief explanation of what this SQL will accomplish"
        }
        
        Only include relevant fields based on the operation type. Ensure the response is valid JSON.
        """
        
        try:
            logger.info(f"Using OpenAI API key: {os.getenv('OPENAI_API_KEY')[:10]}...")
            
            # Call the OpenAI API to process the prompt
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo",  # Use an appropriate model
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                
                # Extract and parse the JSON response
                content = response.choices[0].message.content
                logger.debug(f"Raw response content: {content}")
                
                intent = json.loads(content)
                
                logger.debug(f"Generated intent: {json.dumps(intent, indent=2)}")
                return intent
            except openai.OpenAIError as api_error:
                logger.error(f"OpenAI API error: {api_error}")
                raise Exception(f"OpenAI API error: {api_error}")
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON parsing error: {json_error}, Content: {content if 'content' in locals() else 'No content'}")
                raise Exception(f"Failed to parse JSON response: {json_error}")
            
        except Exception as e:
            logger.error(f"Error processing prompt: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to process natural language prompt: {str(e)}")
    
    def refine_intent(self, intent: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Refine an intent based on user feedback
        
        Args:
            intent: The original intent dictionary
            feedback: User feedback for refinement
            
        Returns:
            An updated intent dictionary
        """
        logger.info(f"Refining intent with feedback: {feedback}")
        
        system_message = """
        You are an expert PostgreSQL database engineer. Your task is to refine a structured intent
        based on user feedback. The original intent is provided along with the user's feedback.
        
        Modify the intent to incorporate the feedback while maintaining the same JSON structure.
        """
        
        try:
            # Call the OpenAI API to refine the intent
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use an appropriate model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Original intent: {json.dumps(intent)}\n\nFeedback: {feedback}"}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the JSON response
            content = response.choices[0].message.content
            refined_intent = json.loads(content)
            
            logger.debug(f"Refined intent: {json.dumps(refined_intent, indent=2)}")
            return refined_intent
            
        except Exception as e:
            logger.error(f"Error refining intent: {e}")
            raise Exception(f"Failed to refine intent based on feedback: {e}")
