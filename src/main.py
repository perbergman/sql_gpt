#!/usr/bin/env python3
"""
SQL-GPT: Natural Language to PostgreSQL Generator
Main entry point for the application
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

from .nlp_processor import NLPProcessor
from .sql_generator import SQLGenerator
from .deployment_manager import DeploymentManager
from .interactive_mode import InteractiveSession
from .web_interface import WebInterface
from .db_connector import DBConnector

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Convert natural language to PostgreSQL queries and deployment scripts'
    )
    parser.add_argument(
        'prompt', 
        nargs='?', 
        help='Natural language prompt to convert to SQL'
    )
    parser.add_argument(
        '--interactive', 
        action='store_true', 
        help='Start in interactive mode'
    )
    parser.add_argument(
        '--web', 
        action='store_true', 
        help='Start the web interface'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to run the web interface on'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the web interface on'
    )
    parser.add_argument(
        '--deploy', 
        action='store_true', 
        help='Generate deployment scripts'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        help='Output file for SQL or deployment script'
    )
    parser.add_argument(
        '--db-connection', 
        type=str, 
        help='Database connection string'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true', 
        help='Enable verbose output'
    )
    
    return parser.parse_args()

def main():
    """Main entry point for the application"""
    args = parse_arguments()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize components
    nlp_processor = NLPProcessor()
    sql_generator = SQLGenerator()
    deployment_manager = DeploymentManager()
    db_connector = DBConnector()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables or .env file")
        print("Error: OPENAI_API_KEY not found. Please set it in your environment or .env file.")
        sys.exit(1)
    
    # Interactive mode
    if args.interactive:
        session = InteractiveSession(nlp_processor, sql_generator, deployment_manager)
        session.start()
        return
        
    # Web interface mode
    if args.web:
        logger.info(f"Starting web interface on {args.host}:{args.port}")
        web = WebInterface(nlp_processor, sql_generator, deployment_manager, db_connector)
        web.run(host=args.host, port=args.port, debug=args.verbose)
        return
    
    # Process single prompt
    if args.prompt:
        try:
            # Process natural language to structured intent
            intent = nlp_processor.process(args.prompt)
            
            # Generate SQL from intent
            sql_query = sql_generator.generate(intent)
            
            # Handle deployment if requested
            if args.deploy:
                script = deployment_manager.create_script(sql_query, intent)
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(script)
                    print(f"Deployment script written to {args.output}")
                else:
                    print("\n=== Deployment Script ===")
                    print(script)
            else:
                # Output SQL
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(sql_query)
                    print(f"SQL query written to {args.output}")
                else:
                    print("\n=== Generated SQL ===")
                    print(sql_query)
                    
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
