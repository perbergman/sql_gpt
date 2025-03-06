"""
Database Browser Module
Provides functionality for browsing PostgreSQL database contents
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from .db_connector import DBConnector

logger = logging.getLogger(__name__)

class DBBrowser:
    """
    Provides functionality for browsing PostgreSQL database contents
    """
    
    def __init__(self, db_connector: DBConnector):
        """
        Initialize the database browser
        
        Args:
            db_connector: Database connector instance
        """
        self.db_connector = db_connector
        logger.debug("Database browser initialized")
    
    def get_schemas(self) -> List[str]:
        """
        Get all schemas in the database
        
        Returns:
            List of schema names
        """
        if not self.db_connector.conn:
            if not self.db_connector.connect():
                return []
        
        try:
            with self.db_connector.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schema_name
                    FROM 
                        information_schema.schemata
                    WHERE 
                        schema_name NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY 
                        schema_name;
                """)
                schemas = cursor.fetchall()
                return [schema[0] for schema in schemas]
        except Exception as e:
            logger.error(f"Error getting schemas: {e}")
            return []
    
    def get_tables(self) -> List[Dict[str, Any]]:
        """
        Get all tables in the database
        
        Returns:
            List of tables with schema and description
        """
        if not self.db_connector.conn:
            if not self.db_connector.connect():
                return []
        
        try:
            with self.db_connector.conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        t.table_name, 
                        t.table_schema,
                        pg_catalog.obj_description(pgc.oid, 'pg_class') as table_description,
                        (SELECT COUNT(*) FROM information_schema.columns c WHERE c.table_name = t.table_name AND c.table_schema = t.table_schema) as column_count,
                        (SELECT pg_total_relation_size(quote_ident(t.table_schema) || '.' || quote_ident(t.table_name))) as table_size
                    FROM 
                        information_schema.tables t
                    JOIN 
                        pg_catalog.pg_class pgc ON pgc.relname = t.table_name
                    JOIN 
                        pg_catalog.pg_namespace pgn ON pgn.oid = pgc.relnamespace AND pgn.nspname = t.table_schema
                    WHERE 
                        t.table_schema NOT IN ('pg_catalog', 'information_schema')
                        AND t.table_type = 'BASE TABLE'
                    ORDER BY 
                        t.table_schema, t.table_name;
                """)
                tables = cursor.fetchall()
                result = []
                for table in tables:
                    result.append({
                        'table_name': table[0],
                        'table_schema': table[1],
                        'table_description': table[2],
                        'column_count': table[3],
                        'table_size': table[4]
                    })
                return result
        except Exception as e:
            logger.error(f"Error getting tables: {e}")
            return []
    
    def get_table_structure(self, table_name: str, schema_name: str = 'public') -> List[Dict[str, Any]]:
        """
        Get structure of a specific table
        
        Args:
            table_name: Name of the table
            schema_name: Schema of the table (default: 'public')
            
        Returns:
            List of columns with their properties
        """
        if not self.db_connector.conn:
            if not self.db_connector.connect():
                return []
        
        try:
            with self.db_connector.conn.cursor(cursor_factory=self.db_connector.conn.cursor_factory) as cursor:
                cursor.execute("""
                    SELECT 
                        column_name, 
                        data_type, 
                        is_nullable,
                        column_default,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale,
                        pg_catalog.col_description(format('%s.%s', table_schema, table_name)::regclass::oid, ordinal_position) as column_description,
                        CASE 
                            WHEN pk.column_name IS NOT NULL THEN true 
                            ELSE false 
                        END as is_primary_key
                    FROM 
                        information_schema.columns c
                    LEFT JOIN (
                        SELECT 
                            kcu.column_name, 
                            kcu.table_name,
                            kcu.table_schema
                        FROM 
                            information_schema.table_constraints tc
                        JOIN 
                            information_schema.key_column_usage kcu ON kcu.constraint_name = tc.constraint_name
                        WHERE 
                            tc.constraint_type = 'PRIMARY KEY'
                    ) pk ON pk.column_name = c.column_name AND pk.table_name = c.table_name AND pk.table_schema = c.table_schema
                    WHERE 
                        c.table_name = %s AND c.table_schema = %s
                    ORDER BY 
                        ordinal_position;
                """, (table_name, schema_name))
                columns = cursor.fetchall()
                return [dict(column) for column in columns]
        except Exception as e:
            logger.error(f"Error getting table structure: {e}")
            return []
    
    def get_table_data(self, table_name: str, schema_name: str = 'public', limit: int = 100, offset: int = 0, order_by: str = None, order_dir: str = 'ASC') -> List[Dict[str, Any]]:
        """
        Get data from a specific table
        
        Args:
            table_name: Name of the table
            schema_name: Schema of the table (default: 'public')
            limit: Maximum number of rows to return
            offset: Number of rows to skip
            order_by: Column to order by
            order_dir: Direction to order (ASC or DESC)
            
        Returns:
            List of rows from the table
        """
        if not self.db_connector.conn:
            if not self.db_connector.connect():
                return []
        
        try:
            from psycopg2 import sql
            
            # Sanitize table_name and schema_name to prevent SQL injection
            schema_identifier = sql.Identifier(schema_name)
            table_identifier = sql.Identifier(table_name)
            
            query = sql.SQL("SELECT * FROM {}.{}").format(schema_identifier, table_identifier)
            
            # Add ORDER BY clause if specified
            if order_by:
                # Sanitize order_by to prevent SQL injection
                order_by_identifier = sql.Identifier(order_by)
                order_dir = "ASC" if order_dir.upper() != "DESC" else "DESC"
                query = sql.SQL("{} ORDER BY {} {}").format(
                    query,
                    order_by_identifier,
                    sql.SQL(order_dir)
                )
            
            # Add LIMIT and OFFSET
            query = sql.SQL("{} LIMIT %s OFFSET %s").format(query)
            
            with self.db_connector.conn.cursor(cursor_factory=self.db_connector.conn.cursor_factory) as cursor:
                cursor.execute(query, (limit, offset))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error getting table data: {e}")
            return []
    
    def get_table_count(self, table_name: str, schema_name: str = 'public') -> int:
        """
        Get the total number of rows in a table
        
        Args:
            table_name: Name of the table
            schema_name: Schema of the table (default: 'public')
            
        Returns:
            Total number of rows
        """
        if not self.db_connector.conn:
            if not self.db_connector.connect():
                return 0
        
        try:
            from psycopg2 import sql
            
            # Sanitize table_name and schema_name to prevent SQL injection
            schema_identifier = sql.Identifier(schema_name)
            table_identifier = sql.Identifier(table_name)
            
            query = sql.SQL("SELECT COUNT(*) as count FROM {}.{}").format(schema_identifier, table_identifier)
            
            with self.db_connector.conn.cursor(cursor_factory=self.db_connector.conn.cursor_factory) as cursor:
                cursor.execute(query)
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error getting table count: {e}")
            return 0
