"""
Database Connector Module
Handles connections to PostgreSQL databases and query execution
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DBConnector:
    """
    Handles connections to PostgreSQL databases and query execution
    """
    
    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the database connector
        
        Args:
            connection_params: Optional connection parameters. If not provided,
                              environment variables will be used.
        """
        self.connection_params = connection_params or {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'database': os.getenv('POSTGRES_DB', 'sql_gpt')
        }
        self.conn = None
        logger.debug("Database connector initialized")
    
    def connect(self) -> bool:
        """
        Connect to the PostgreSQL database
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info(f"Connected to PostgreSQL database at {self.connection_params['host']}:{self.connection_params['port']}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the PostgreSQL database"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("Disconnected from PostgreSQL database")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Tuple[bool, Union[List[Dict[str, Any]], str]]:
        """
        Execute a SQL query
        
        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            A tuple containing (success, result)
            - success: True if query executed successfully, False otherwise
            - result: List of dictionaries for SELECT queries, or message for other queries
        """
        if not self.conn:
            if not self.connect():
                return False, "Not connected to database"
        
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or {})
                
                # Check if the query returns results
                if cursor.description:
                    results = cursor.fetchall()
                    self.conn.commit()
                    return True, [dict(row) for row in results]
                else:
                    rowcount = cursor.rowcount
                    self.conn.commit()
                    return True, f"Query executed successfully. Rows affected: {rowcount}"
                    
        except psycopg2.errors.DuplicateTable as e:
            self.conn.rollback()
            logger.warning(f"Table already exists: {e}")
            # Extract table name from the error message
            table_name = str(e).split('"')[1] if '"' in str(e) else "table"
            return True, f"Table '{table_name}' already exists. No changes were made."
            
        except psycopg2.errors.DuplicateColumn as e:
            self.conn.rollback()
            logger.warning(f"Column already exists: {e}")
            return True, f"Column already exists. No changes were made."
            
        except psycopg2.errors.UndefinedTable as e:
            self.conn.rollback()
            logger.error(f"Table does not exist: {e}")
            # Extract table name from the error message
            table_name = str(e).split('"')[1] if '"' in str(e) else "table"
            return False, f"Error: Table '{table_name}' does not exist."
            
        except psycopg2.errors.UndefinedColumn as e:
            self.conn.rollback()
            logger.error(f"Column does not exist: {e}")
            error_message = str(e).split('\n')[0] if '\n' in str(e) else str(e)
            return False, f"Error: {error_message}"
            
        except psycopg2.errors.SyntaxError as e:
            self.conn.rollback()
            logger.error(f"SQL syntax error: {e}")
            # Get just the first line of the error message which is usually the most helpful
            error_message = str(e).split('\n')[0] if '\n' in str(e) else str(e)
            return False, f"SQL syntax error: {error_message}"
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error executing query: {e}")
            return False, f"Error: {e}"
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the database connection
        
        Returns:
            A tuple containing (success, message)
        """
        if not self.conn:
            if not self.connect():
                return False, "Failed to connect to database"
        
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                return True, f"Connected to PostgreSQL: {version}"
        except Exception as e:
            logger.error(f"Error testing connection: {e}")
            return False, f"Error: {e}"
    
    def get_schema_info(self) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """
        Get information about the database schema
        
        Returns:
            A tuple containing (success, schema_info)
        """
        if not self.conn:
            if not self.connect():
                return False, "Not connected to database"
        
        try:
            schema_info = {
                'tables': [],
                'views': [],
                'functions': []
            }
            
            # Get tables
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        table_name, 
                        table_schema
                    FROM 
                        information_schema.tables
                    WHERE 
                        table_schema NOT IN ('pg_catalog', 'information_schema')
                        AND table_type = 'BASE TABLE'
                    ORDER BY 
                        table_schema, table_name;
                """)
                tables = cursor.fetchall()
                
                # Get columns for each table
                for table in tables:
                    table_name = table['table_name']
                    schema_name = table['table_schema']
                    
                    cursor.execute("""
                        SELECT 
                            column_name, 
                            data_type, 
                            is_nullable,
                            column_default
                        FROM 
                            information_schema.columns
                        WHERE 
                            table_schema = %s AND table_name = %s
                        ORDER BY 
                            ordinal_position;
                    """, (schema_name, table_name))
                    
                    columns = cursor.fetchall()
                    
                    schema_info['tables'].append({
                        'name': table_name,
                        'schema': schema_name,
                        'columns': [dict(col) for col in columns]
                    })
            
            # Get views
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        table_name as view_name, 
                        table_schema as view_schema
                    FROM 
                        information_schema.views
                    WHERE 
                        table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY 
                        table_schema, table_name;
                """)
                views = cursor.fetchall()
                schema_info['views'] = [dict(view) for view in views]
            
            # Get functions
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        routine_name as function_name, 
                        routine_schema as function_schema
                    FROM 
                        information_schema.routines
                    WHERE 
                        routine_schema NOT IN ('pg_catalog', 'information_schema')
                        AND routine_type = 'FUNCTION'
                    ORDER BY 
                        routine_schema, routine_name;
                """)
                functions = cursor.fetchall()
                schema_info['functions'] = [dict(func) for func in functions]
            
            return True, schema_info
            
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return False, f"Error: {e}"
