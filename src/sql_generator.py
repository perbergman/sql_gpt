"""
SQL Generator Module
Converts structured intents into PostgreSQL queries
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import openai
import sqlparse

logger = logging.getLogger(__name__)

class SQLGenerator:
    """
    Generates PostgreSQL queries from structured intents
    """
    
    def __init__(self):
        """Initialize the SQL generator with OpenAI client"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.debug("SQL Generator initialized")
    
    def generate(self, intent: Dict[str, Any]) -> str:
        """
        Generate a PostgreSQL query from a structured intent
        
        Args:
            intent: A dictionary containing the structured intent
            
        Returns:
            A string containing the generated SQL query
        """
        logger.info(f"Generating SQL for operation: {intent.get('operation_type', 'unknown')}")
        
        # Define the system message to guide the model
        system_message = """
        You are an expert PostgreSQL database engineer. Your task is to generate optimized PostgreSQL 
        queries based on the structured intent provided.
        
        Follow these guidelines:
        1. Use PostgreSQL-specific syntax and features when appropriate
        2. Include comments explaining complex parts of the query
        3. Format the SQL for readability
        4. Consider performance implications and add appropriate indexes
        5. Use best practices for the specific operation type
        6. Support advanced PostgreSQL features like partitioning, JSON operations, CTEs, etc.
        
        Only return the SQL query without any additional text or markdown formatting.
        """
        
        try:
            # Convert intent to a string representation for the prompt
            intent_str = json.dumps(intent, indent=2)
            
            # Call the OpenAI API to generate the SQL
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use an appropriate model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Generate PostgreSQL query for this intent:\n{intent_str}"}
                ]
            )
            
            # Extract the SQL from the response
            sql = response.choices[0].message.content.strip()
            
            # Format the SQL for readability
            formatted_sql = self._format_sql(sql)
            
            logger.debug(f"Generated SQL: {formatted_sql}")
            return formatted_sql
            
        except Exception as e:
            logger.error(f"Error generating SQL: {e}")
            raise Exception(f"Failed to generate SQL from intent: {e}")
    
    def _format_sql(self, sql: str) -> str:
        """
        Format SQL query for readability
        
        Args:
            sql: Raw SQL query
            
        Returns:
            Formatted SQL query
        """
        try:
            # Use sqlparse to format the SQL
            formatted = sqlparse.format(
                sql,
                reindent=True,
                keyword_case='upper',
                indent_width=4
            )
            return formatted
        except Exception as e:
            logger.warning(f"Error formatting SQL: {e}")
            return sql  # Return original if formatting fails
    
    def validate(self, sql: str) -> Dict[str, Any]:
        """
        Validate a SQL query for syntax and potential issues
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Dictionary with validation results
        """
        logger.info("Validating SQL query")
        
        system_message = """
        You are an expert PostgreSQL database engineer. Your task is to validate the provided SQL query
        for syntax errors and potential issues.
        
        Provide a JSON response with the following structure:
        {
            "valid": true|false,
            "errors": ["error1", "error2"],
            "warnings": ["warning1", "warning2"],
            "suggestions": ["suggestion1", "suggestion2"]
        }
        """
        
        try:
            # Call the OpenAI API to validate the SQL
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use an appropriate model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Validate this PostgreSQL query:\n{sql}"}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract and parse the JSON response
            content = response.choices[0].message.content
            validation_result = json.loads(content)
            
            logger.debug(f"Validation result: {json.dumps(validation_result, indent=2)}")
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating SQL: {e}")
            return {
                "valid": False,
                "errors": [f"Validation process failed: {e}"],
                "warnings": [],
                "suggestions": []
            }
