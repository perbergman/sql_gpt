#!/usr/bin/env python3
"""
SQL-GPT: Natural Language to PostgreSQL Generator
Run script for the application
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.nlp_processor import NLPProcessor
from src.sql_generator import SQLGenerator
from src.deployment_manager import DeploymentManager
from src.db_connector import DBConnector
from src.web_interface import WebInterface

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Main entry point"""
    # Initialize components
    db_connector = DBConnector()
    nlp_processor = NLPProcessor()
    sql_generator = SQLGenerator()
    deployment_manager = DeploymentManager()
    
    # Initialize web interface
    web_interface = WebInterface(
        nlp_processor=nlp_processor,
        sql_generator=sql_generator,
        deployment_manager=deployment_manager,
        db_connector=db_connector
    )
    
    # Run web interface
    web_interface.run(host='0.0.0.0', port=9876, debug=False)

if __name__ == "__main__":
    main()
