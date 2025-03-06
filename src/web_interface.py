"""
Web Interface Module
Provides a web interface for the SQL-GPT application
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, render_template, send_from_directory

from .nlp_processor import NLPProcessor
from .sql_generator import SQLGenerator
from .deployment_manager import DeploymentManager
from .db_connector import DBConnector
from .db_browser import DBBrowser

logger = logging.getLogger(__name__)

class WebInterface:
    """
    Provides a web interface for the SQL-GPT application
    """
    
    def __init__(self, nlp_processor: NLPProcessor, sql_generator: SQLGenerator, 
                deployment_manager: DeploymentManager, db_connector: DBConnector):
        """
        Initialize the web interface
        
        Args:
            nlp_processor: NLP processor instance
            sql_generator: SQL generator instance
            deployment_manager: Deployment manager instance
            db_connector: Database connector instance
        """
        self.nlp_processor = nlp_processor
        self.sql_generator = sql_generator
        self.deployment_manager = deployment_manager
        self.db_connector = db_connector
        self.db_browser = DBBrowser(db_connector)
        self.app = Flask(__name__, 
                         static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
                         template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))
        
        self._setup_routes()
        logger.debug("Web interface initialized")
    
    def _setup_routes(self):
        """Set up the Flask routes"""
        
        @self.app.route('/')
        def index():
            """Render the index page"""
            return render_template('index.html')
        
        @self.app.route('/static/<path:path>')
        def serve_static(path):
            """Serve static files"""
            return send_from_directory(self.app.static_folder, path)
        
        @self.app.route('/api/process', methods=['POST'])
        def process_prompt():
            """Process a natural language prompt"""
            logger.info("Received API request to /api/process")
            print("\n[REQUEST /api/process] Received API request")
            
            # Log request headers for debugging
            logger.info(f"Request headers: {dict(request.headers)}")
            
            # Get and validate JSON data
            try:
                data = request.get_json(force=True)  # force=True to handle potential content-type issues
                logger.info(f"Received request data: {data}")
                print(f"[REQUEST DATA] {json.dumps(data, indent=2)}")
            except Exception as json_error:
                logger.error(f"Failed to parse JSON request: {json_error}")
                try:
                    raw_data = request.data.decode('utf-8', errors='replace')
                    logger.error(f"Raw request data: {raw_data}")
                except:
                    raw_data = "<Could not decode request data>"
                    
                return jsonify({
                    'success': False,
                    'error': f'Invalid JSON in request: {str(json_error)}',
                    'request_data': raw_data
                })
            
            if not data:
                logger.error("No JSON data received in request")
                return jsonify({
                    'success': False,
                    'error': 'No data received'
                })
                
            prompt = data.get('prompt', '')
            if not prompt:
                logger.error("No prompt provided in request")
                return jsonify({
                    'success': False,
                    'error': 'No prompt provided',
                    'received_data': data
                })
                
            logger.info(f"Processing prompt: '{prompt}'")
            
            try:
                # Check if OpenAI API key is available
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.error("OPENAI_API_KEY environment variable not set")
                    return jsonify({
                        'success': False,
                        'error': 'OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable.'
                    })
                
                # Process the prompt with detailed error handling
                try:
                    logger.info("Calling NLP processor")
                    intent = self.nlp_processor.process(prompt)
                    logger.info(f"NLP processing complete: {intent}")
                except Exception as nlp_error:
                    logger.error(f"Error in NLP processing: {nlp_error}")
                    import traceback
                    return jsonify({
                        'success': False,
                        'error': f'NLP processing error: {str(nlp_error)}',
                        'error_details': traceback.format_exc()
                    })
                
                # Generate SQL with detailed error handling
                try:
                    logger.info("Generating SQL query")
                    sql_query = self.sql_generator.generate(intent)
                    logger.info(f"SQL generation complete: {sql_query}")
                except Exception as sql_error:
                    logger.error(f"Error in SQL generation: {sql_error}")
                    import traceback
                    return jsonify({
                        'success': False,
                        'error': f'SQL generation error: {str(sql_error)}',
                        'error_details': traceback.format_exc(),
                        'intent': intent  # Return the intent even if SQL generation failed
                    })
                
                # Validate SQL with detailed error handling
                try:
                    logger.info("Validating SQL query")
                    validation = self.sql_generator.validate(sql_query)
                    logger.info(f"SQL validation complete: {validation}")
                except Exception as validation_error:
                    logger.error(f"Error in SQL validation: {validation_error}")
                    import traceback
                    # Continue with a default validation result
                    validation = {'valid': False, 'errors': [str(validation_error)]}
                
                # Create deployment script with detailed error handling
                try:
                    logger.info("Creating deployment script")
                    script = self.deployment_manager.create_script(sql_query, intent)
                    logger.info("Deployment script creation complete")
                except Exception as script_error:
                    logger.error(f"Error in deployment script creation: {script_error}")
                    import traceback
                    # Continue with an empty script
                    script = "-- Error generating deployment script: " + str(script_error)
                
                # Prepare successful response
                response_data = {
                    'success': True,
                    'intent': intent,
                    'sql': sql_query,
                    'validation': validation,
                    'deployment_script': script
                }
                
                logger.info(f"Returning successful response with data: {response_data}")
                print(f"\n[RESPONSE /api/process] {json.dumps(response_data, indent=2)}\n")
                return jsonify(response_data)
                
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Unhandled error processing prompt: {e}")
                logger.error(error_trace)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_details': error_trace
                })
        
        @self.app.route('/api/execute', methods=['POST'])
        def execute_query():
            """Execute a SQL query"""
            data = request.json
            print(f"\n[REQUEST /api/execute] Received data: {json.dumps(data, indent=2)}\n")
            
            query = data.get('query', '')
            
            if not query or not query.strip():
                logger.warning("Empty query received")
                print("[WARNING] Empty query received")
                return jsonify({
                    'success': False,
                    'error': 'Empty query. Please provide a valid SQL query.'
                })
                
            logger.info(f"Executing query: {query[:100]}{'...' if len(query) > 100 else ''}")
            print(f"[INFO] Executing query: {query}")
            
            try:
                # Execute the query
                success, result = self.db_connector.execute_query(query)
                
                # Log the result type and summary
                if success:
                    if isinstance(result, str):
                        logger.info(f"Query executed with message: {result[:100]}{'...' if len(str(result)) > 100 else ''}")
                    elif isinstance(result, list):
                        logger.info(f"Query returned {len(result)} rows")
                    else:
                        logger.info(f"Query executed successfully with result type: {type(result)}")
                else:
                    logger.warning(f"Query execution failed: {result}")
                
                # Check for warning conditions in successful queries
                if success and isinstance(result, str) and 'already exists' in result:
                    logger.info("Query resulted in a warning condition (already exists)")
                
                response_data = {
                    'success': success,
                    'result': result,
                    'query_type': self._determine_query_type(query)
                }
                print(f"\n[RESPONSE /api/execute] {json.dumps(response_data, indent=2)}\n")
                return jsonify(response_data)
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"Error executing query: {e}")
                logger.error(error_trace)
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'error_details': error_trace
                })
        
    def _determine_query_type(self, query):
        """Determine the type of SQL query"""
        query = query.strip().upper()
        
        if query.startswith('SELECT'):
            return 'SELECT'
        elif query.startswith('INSERT'):
            return 'INSERT'
        elif query.startswith('UPDATE'):
            return 'UPDATE'
        elif query.startswith('DELETE'):
            return 'DELETE'
        elif query.startswith('CREATE TABLE'):
            return 'CREATE_TABLE'
        elif query.startswith('ALTER TABLE'):
            return 'ALTER_TABLE'
        elif query.startswith('DROP'):
            return 'DROP'
        else:
            return 'OTHER'
        
        @self.app.route('/api/schema', methods=['GET'])
        def get_schema():
            """Get the database schema"""
            try:
                # Get the schema
                success, schema_info = self.db_connector.get_schema_info()
                
                return jsonify({
                    'success': success,
                    'schema': schema_info if success else None,
                    'error': schema_info if not success else None
                })
            except Exception as e:
                logger.error(f"Error getting schema: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/test-connection', methods=['GET'])
        def test_connection():
            """Test the database connection"""
            try:
                # Test the connection
                success, message = self.db_connector.test_connection()
                
                return jsonify({
                    'success': success,
                    'message': message
                })
            except Exception as e:
                logger.error(f"Error testing connection: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/browser/schemas', methods=['GET'])
        def get_schemas():
            """Get all schemas in the database"""
            try:
                schemas = self.db_browser.get_schemas()
                
                return jsonify({
                    'success': True,
                    'schemas': schemas
                })
            except Exception as e:
                logger.error(f"Error getting schemas: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/browser/tables', methods=['GET'])
        def get_tables():
            """Get all tables in the database"""
            try:
                tables = self.db_browser.get_tables()
                
                return jsonify({
                    'success': True,
                    'tables': tables
                })
            except Exception as e:
                logger.error(f"Error getting tables: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/browser/table/structure', methods=['GET'])
        def get_table_structure():
            """Get structure of a specific table"""
            table_name = request.args.get('table', '')
            schema_name = request.args.get('schema', 'public')
            
            if not table_name:
                return jsonify({
                    'success': False,
                    'error': 'Table name is required'
                })
            
            try:
                structure = self.db_browser.get_table_structure(table_name, schema_name)
                
                return jsonify({
                    'success': True,
                    'structure': structure,
                    'table': table_name,
                    'schema': schema_name
                })
            except Exception as e:
                logger.error(f"Error getting table structure: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
        
        @self.app.route('/api/browser/table/data', methods=['GET'])
        def get_table_data():
            """Get data from a specific table"""
            table_name = request.args.get('table', '')
            schema_name = request.args.get('schema', 'public')
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            order_by = request.args.get('order_by', None)
            order_dir = request.args.get('order_dir', 'ASC')
            
            if not table_name:
                return jsonify({
                    'success': False,
                    'error': 'Table name is required'
                })
            
            try:
                data = self.db_browser.get_table_data(
                    table_name, schema_name, limit, offset, order_by, order_dir
                )
                count = self.db_browser.get_table_count(table_name, schema_name)
                
                return jsonify({
                    'success': True,
                    'data': data,
                    'table': table_name,
                    'schema': schema_name,
                    'total_count': count,
                    'limit': limit,
                    'offset': offset
                })
            except Exception as e:
                logger.error(f"Error getting table data: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                })
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Run the web interface
        
        Args:
            host: Host to run on
            port: Port to run on
            debug: Whether to run in debug mode
        """
        self.app.run(host=host, port=port, debug=debug)
