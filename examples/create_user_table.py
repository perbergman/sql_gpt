#!/usr/bin/env python3
"""
Example: Create a users table
This example demonstrates how to use SQL-GPT to create a users table
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.nlp_processor import NLPProcessor
from src.sql_generator import SQLGenerator
from src.deployment_manager import DeploymentManager
from src.db_connector import DBConnector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function"""
    # Initialize components
    nlp_processor = NLPProcessor()
    sql_generator = SQLGenerator()
    deployment_manager = DeploymentManager()
    db_connector = DBConnector()
    
    # Natural language prompt
    prompt = "Create a users table with id, name, email, and registration date"
    
    # Process the prompt
    print(f"Processing prompt: {prompt}")
    intent = nlp_processor.process(prompt)
    
    # Print the structured intent
    print("\nStructured Intent:")
    print(intent)
    
    # Generate SQL
    sql_query = sql_generator.generate(intent)
    
    # Print the SQL query
    print("\nGenerated SQL:")
    print(sql_query)
    
    # Create a deployment script
    script = deployment_manager.create_script(sql_query, intent)
    
    # Print the deployment script
    print("\nDeployment Script:")
    print(script)
    
    # Test database connection
    success, message = db_connector.test_connection()
    if success:
        print(f"\nDatabase Connection: {message}")
        
        # Execute the query
        print("\nExecuting SQL query...")
        success, result = db_connector.execute_query(sql_query)
        
        if success:
            print(f"Result: {result}")
            
            # Get schema info to verify the table was created
            success, schema_info = db_connector.get_schema_info()
            if success:
                print("\nUpdated Schema Information:")
                for table in schema_info['tables']:
                    print(f"Table: {table['name']}")
                    for column in table['columns']:
                        print(f"  - {column['column_name']} ({column['data_type']})")
        else:
            print(f"Error: {result}")
    else:
        print(f"Database Connection Error: {message}")

if __name__ == "__main__":
    main()
