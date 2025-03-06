"""
Basic tests for SQL-GPT
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.nlp_processor import NLPProcessor
from src.sql_generator import SQLGenerator
from src.deployment_manager import DeploymentManager
from src.db_connector import DBConnector

class TestBasicFunctionality(unittest.TestCase):
    """Test basic functionality of SQL-GPT"""
    
    @patch('openai.OpenAI')
    def test_nlp_processor(self, mock_openai):
        """Test NLP processor"""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({
            "operation_type": "CREATE_TABLE",
            "entities": [{"name": "users", "type": "table"}],
            "fields": [
                {"name": "id", "data_type": "serial", "constraints": ["PRIMARY KEY"]},
                {"name": "name", "data_type": "text", "constraints": ["NOT NULL"]},
                {"name": "email", "data_type": "text", "constraints": ["UNIQUE", "NOT NULL"]},
                {"name": "created_at", "data_type": "timestamp", "constraints": ["NOT NULL", "DEFAULT CURRENT_TIMESTAMP"]}
            ],
            "explanation": "Create a users table with id, name, email, and creation timestamp"
        })
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the NLP processor
        processor = NLPProcessor()
        intent = processor.process("Create a users table with name, email, and registration date")
        
        # Verify the result
        self.assertEqual(intent["operation_type"], "CREATE_TABLE")
        self.assertEqual(intent["entities"][0]["name"], "users")
        self.assertEqual(len(intent["fields"]), 4)
    
    @patch('openai.OpenAI')
    def test_sql_generator(self, mock_openai):
        """Test SQL generator"""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the SQL generator
        generator = SQLGenerator()
        intent = {
            "operation_type": "CREATE_TABLE",
            "entities": [{"name": "users", "type": "table"}],
            "fields": [
                {"name": "id", "data_type": "serial", "constraints": ["PRIMARY KEY"]},
                {"name": "name", "data_type": "text", "constraints": ["NOT NULL"]},
                {"name": "email", "data_type": "text", "constraints": ["UNIQUE", "NOT NULL"]},
                {"name": "created_at", "data_type": "timestamp", "constraints": ["NOT NULL", "DEFAULT CURRENT_TIMESTAMP"]}
            ],
            "explanation": "Create a users table with id, name, email, and creation timestamp"
        }
        sql = generator.generate(intent)
        
        # Verify the result
        self.assertIn("CREATE TABLE users", sql)
        self.assertIn("id SERIAL PRIMARY KEY", sql)
        self.assertIn("email TEXT UNIQUE NOT NULL", sql)

    @patch('openai.OpenAI')
    def test_deployment_manager(self, mock_openai):
        """Test deployment manager"""
        # Mock the OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices[0].message.content = """
        DROP TABLE IF EXISTS users;
        """
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the deployment manager
        manager = DeploymentManager()
        sql_query = """
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        intent = {
            "operation_type": "CREATE_TABLE",
            "entities": [{"name": "users", "type": "table"}]
        }
        script = manager.create_script(sql_query, intent)
        
        # Verify the result
        self.assertIn("BEGIN;", script)
        self.assertIn("CREATE TABLE users", script)
        self.assertIn("COMMIT;", script)

if __name__ == "__main__":
    unittest.main()
