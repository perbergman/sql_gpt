#!/usr/bin/env python3
"""
Run SQL-GPT Web Interface
This script starts the SQL-GPT web interface
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

from src.nlp_processor import NLPProcessor
from src.sql_generator import SQLGenerator
from src.deployment_manager import DeploymentManager
from src.db_connector import DBConnector
from src.web_interface import WebInterface

def main():
    """Main function to run the web interface"""
    print("Starting SQL-GPT Web Interface...")
    
    # Initialize components
    nlp_processor = NLPProcessor()
    sql_generator = SQLGenerator()
    deployment_manager = DeploymentManager()
    db_connector = DBConnector()
    
    # Create web interface
    web = WebInterface(nlp_processor, sql_generator, deployment_manager, db_connector)
    
    # Run the web interface
    web.run(host='0.0.0.0', port=9876, debug=False)

if __name__ == "__main__":
    main()
