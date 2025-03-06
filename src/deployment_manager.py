"""
Deployment Manager Module
Handles the generation of deployment scripts for database migrations
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import openai
from datetime import datetime
import jinja2

logger = logging.getLogger(__name__)

class DeploymentManager:
    """
    Manages the generation of deployment scripts for database migrations
    """
    
    def __init__(self):
        """Initialize the deployment manager with OpenAI client"""
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            ),
            autoescape=jinja2.select_autoescape(['sql'])
        )
        logger.debug("Deployment Manager initialized")
    
    def create_script(self, sql_query: str, intent: Dict[str, Any]) -> str:
        """
        Create a deployment script for a SQL query
        
        Args:
            sql_query: The SQL query to deploy
            intent: The structured intent that generated the query
            
        Returns:
            A string containing the deployment script
        """
        logger.info(f"Creating deployment script for operation: {intent.get('operation_type', 'unknown')}")
        
        # Generate a timestamp for the migration
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create a migration name based on the operation type and entities
        operation = intent.get('operation_type', 'unknown').lower()
        entities = [e['name'] for e in intent.get('entities', [])]
        migration_name = f"{operation}_{'-'.join(entities)}"
        
        # Determine if this is a reversible migration
        is_reversible = self._is_reversible(operation)
        
        # Generate the rollback SQL if the migration is reversible
        rollback_sql = ""
        if is_reversible:
            rollback_sql = self._generate_rollback(sql_query, intent)
        
        # Create the deployment script
        if self._should_use_alembic(intent):
            return self._create_alembic_script(sql_query, rollback_sql, timestamp, migration_name, intent)
        else:
            return self._create_plain_script(sql_query, rollback_sql, timestamp, migration_name, intent)
    
    def _is_reversible(self, operation: str) -> bool:
        """
        Determine if an operation is reversible
        
        Args:
            operation: The operation type
            
        Returns:
            True if the operation is reversible, False otherwise
        """
        # These operations are generally reversible
        reversible_operations = [
            'create_table', 'alter_table', 'create_index', 
            'insert', 'update', 'delete'
        ]
        
        # These operations are generally not reversible
        non_reversible_operations = [
            'drop_table', 'drop_index', 'truncate'
        ]
        
        return operation.lower() in reversible_operations
    
    def _generate_rollback(self, sql_query: str, intent: Dict[str, Any]) -> str:
        """
        Generate rollback SQL for a given query
        
        Args:
            sql_query: The SQL query to roll back
            intent: The structured intent that generated the query
            
        Returns:
            A string containing the rollback SQL
        """
        logger.info("Generating rollback SQL")
        
        system_message = """
        You are an expert PostgreSQL database engineer. Your task is to generate rollback SQL 
        for the provided forward migration SQL.
        
        The rollback SQL should undo the changes made by the forward migration, returning the 
        database to its previous state. Only return the SQL query without any additional text 
        or markdown formatting.
        """
        
        try:
            # Call the OpenAI API to generate the rollback SQL
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",  # Use an appropriate model
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Generate rollback SQL for this migration:\n{sql_query}\n\nIntent: {json.dumps(intent, indent=2)}"}
                ]
            )
            
            # Extract the rollback SQL from the response
            rollback_sql = response.choices[0].message.content.strip()
            
            logger.debug(f"Generated rollback SQL: {rollback_sql}")
            return rollback_sql
            
        except Exception as e:
            logger.error(f"Error generating rollback SQL: {e}")
            return f"-- Error generating rollback SQL: {e}\n-- Manual rollback required"
    
    def _should_use_alembic(self, intent: Dict[str, Any]) -> bool:
        """
        Determine if Alembic should be used for this migration
        
        Args:
            intent: The structured intent
            
        Returns:
            True if Alembic should be used, False otherwise
        """
        # This is a simplified decision - in a real application, this would be more complex
        # For now, we'll assume Alembic should be used for schema changes
        schema_operations = [
            'create_table', 'alter_table', 'drop_table', 
            'create_index', 'drop_index'
        ]
        
        operation = intent.get('operation_type', '').lower()
        return operation in schema_operations
    
    def _create_alembic_script(self, sql_query: str, rollback_sql: str, timestamp: str, 
                              migration_name: str, intent: Dict[str, Any]) -> str:
        """
        Create an Alembic migration script
        
        Args:
            sql_query: The SQL query to deploy
            rollback_sql: The rollback SQL
            timestamp: The migration timestamp
            migration_name: The migration name
            intent: The structured intent
            
        Returns:
            A string containing the Alembic migration script
        """
        # In a real application, we would use a template file
        # For now, we'll create the script directly
        script = f"""\"\"\"
{migration_name}

Revision ID: {timestamp}
Revises: 
Create Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

\"\"\"

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '{timestamp}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Execute the forward migration
    op.execute(\"\"\"
{sql_query}
    \"\"\")


def downgrade():
    # Execute the rollback migration
    op.execute(\"\"\"
{rollback_sql}
    \"\"\")
"""
        return script
    
    def _create_plain_script(self, sql_query: str, rollback_sql: str, timestamp: str, 
                            migration_name: str, intent: Dict[str, Any]) -> str:
        """
        Create a plain SQL migration script
        
        Args:
            sql_query: The SQL query to deploy
            rollback_sql: The rollback SQL
            timestamp: The migration timestamp
            migration_name: The migration name
            intent: The structured intent
            
        Returns:
            A string containing the plain SQL migration script
        """
        # In a real application, we would use a template file
        # For now, we'll create the script directly
        script = f"""-- Migration: {migration_name}
-- Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Migration ID: {timestamp}

-- Transaction to ensure the migration is atomic
BEGIN;

-- Forward migration
{sql_query}

-- To roll back this migration, run the following SQL:
/*
-- Rollback migration
{rollback_sql}
*/

COMMIT;
"""
        return script
