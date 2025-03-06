"""
Interactive Mode Module
Provides an interactive session for generating SQL queries
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from nlp_processor import NLPProcessor
from sql_generator import SQLGenerator
from deployment_manager import DeploymentManager

logger = logging.getLogger(__name__)

class InteractiveSession:
    """
    Provides an interactive session for generating SQL queries
    """
    
    def __init__(self, nlp_processor: NLPProcessor, sql_generator: SQLGenerator, 
                deployment_manager: DeploymentManager):
        """
        Initialize the interactive session
        
        Args:
            nlp_processor: NLP processor instance
            sql_generator: SQL generator instance
            deployment_manager: Deployment manager instance
        """
        self.nlp_processor = nlp_processor
        self.sql_generator = sql_generator
        self.deployment_manager = deployment_manager
        self.console = Console()
        self.history = []
        logger.debug("Interactive session initialized")
    
    def start(self):
        """Start the interactive session"""
        self._print_welcome()
        
        while True:
            try:
                # Get user prompt
                prompt = self._get_prompt()
                
                if prompt.lower() in ['exit', 'quit', 'q']:
                    self._print_goodbye()
                    break
                
                if prompt.lower() in ['help', 'h', '?']:
                    self._print_help()
                    continue
                
                if prompt.lower() in ['history', 'hist']:
                    self._show_history()
                    continue
                
                # Process the prompt
                self._process_prompt(prompt)
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Session interrupted.[/yellow]")
                if Confirm.ask("Do you want to exit?"):
                    self._print_goodbye()
                    break
            except Exception as e:
                logger.error(f"Error in interactive session: {e}")
                self.console.print(f"[red]Error:[/red] {e}")
    
    def _print_welcome(self):
        """Print welcome message"""
        self.console.print(Panel.fit(
            "[bold blue]SQL-GPT: Natural Language to PostgreSQL Generator[/bold blue]\n\n"
            "Convert natural language prompts to advanced PostgreSQL queries.\n"
            "Type [bold]help[/bold] for a list of commands or [bold]exit[/bold] to quit.",
            title="Welcome",
            border_style="blue"
        ))
    
    def _print_help(self):
        """Print help information"""
        self.console.print(Panel.fit(
            "Available commands:\n\n"
            "[bold]help[/bold] or [bold]h[/bold] or [bold]?[/bold] - Show this help message\n"
            "[bold]exit[/bold] or [bold]quit[/bold] or [bold]q[/bold] - Exit the application\n"
            "[bold]history[/bold] or [bold]hist[/bold] - Show command history\n\n"
            "For any other input, I'll try to convert it to SQL!",
            title="Help",
            border_style="green"
        ))
    
    def _print_goodbye(self):
        """Print goodbye message"""
        self.console.print(Panel.fit(
            "Thank you for using SQL-GPT!\n\n"
            "Have a great day!",
            title="Goodbye",
            border_style="blue"
        ))
    
    def _get_prompt(self) -> str:
        """Get a prompt from the user"""
        return Prompt.ask("\n[bold green]Enter your prompt[/bold green]")
    
    def _show_history(self):
        """Show command history"""
        if not self.history:
            self.console.print("[yellow]No history yet.[/yellow]")
            return
        
        self.console.print(Panel.fit(
            "\n".join([f"[bold]{i+1}.[/bold] {item['prompt']}" for i, item in enumerate(self.history)]),
            title="History",
            border_style="yellow"
        ))
    
    def _process_prompt(self, prompt: str):
        """
        Process a user prompt
        
        Args:
            prompt: User prompt
        """
        self.console.print("[bold]Processing...[/bold]")
        
        try:
            # Process natural language to structured intent
            intent = self.nlp_processor.process(prompt)
            
            # Show the intent
            self._show_intent(intent)
            
            # Ask if the intent is correct
            if not Confirm.ask("Is this intent correct?"):
                feedback = Prompt.ask("[bold]Please provide feedback to improve the intent[/bold]")
                intent = self.nlp_processor.refine_intent(intent, feedback)
                self._show_intent(intent)
            
            # Generate SQL from intent
            sql_query = self.sql_generator.generate(intent)
            
            # Show the SQL
            self._show_sql(sql_query)
            
            # Validate the SQL
            validation = self.sql_generator.validate(sql_query)
            if not validation['valid']:
                self._show_validation(validation)
                if Confirm.ask("Do you want to regenerate the SQL?"):
                    feedback = Prompt.ask("[bold]Please provide feedback for regeneration[/bold]")
                    intent = self.nlp_processor.refine_intent(intent, feedback)
                    sql_query = self.sql_generator.generate(intent)
                    self._show_sql(sql_query)
            
            # Ask if deployment script is needed
            if Confirm.ask("Do you want to generate a deployment script?"):
                script = self.deployment_manager.create_script(sql_query, intent)
                self._show_deployment_script(script)
                
                # Ask if the script should be saved
                if Confirm.ask("Do you want to save this script to a file?"):
                    filename = Prompt.ask(
                        "[bold]Enter filename[/bold]", 
                        default=f"migration_{intent.get('operation_type', 'unknown').lower()}.sql"
                    )
                    with open(filename, 'w') as f:
                        f.write(script)
                    self.console.print(f"[green]Script saved to {filename}[/green]")
            
            # Add to history
            self.history.append({
                'prompt': prompt,
                'intent': intent,
                'sql': sql_query
            })
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            self.console.print(f"[red]Error:[/red] {e}")
    
    def _show_intent(self, intent: Dict[str, Any]):
        """
        Show the structured intent
        
        Args:
            intent: The structured intent
        """
        intent_str = json.dumps(intent, indent=2)
        self.console.print(Panel(
            Syntax(intent_str, "json", theme="monokai", line_numbers=True),
            title="Structured Intent",
            border_style="cyan"
        ))
    
    def _show_sql(self, sql: str):
        """
        Show the generated SQL
        
        Args:
            sql: The SQL query
        """
        self.console.print(Panel(
            Syntax(sql, "sql", theme="monokai", line_numbers=True),
            title="Generated SQL",
            border_style="green"
        ))
    
    def _show_validation(self, validation: Dict[str, Any]):
        """
        Show the validation results
        
        Args:
            validation: The validation results
        """
        content = []
        
        if validation.get('errors'):
            content.append("[bold red]Errors:[/bold red]")
            for error in validation['errors']:
                content.append(f"- {error}")
            content.append("")
        
        if validation.get('warnings'):
            content.append("[bold yellow]Warnings:[/bold yellow]")
            for warning in validation['warnings']:
                content.append(f"- {warning}")
            content.append("")
        
        if validation.get('suggestions'):
            content.append("[bold blue]Suggestions:[/bold blue]")
            for suggestion in validation['suggestions']:
                content.append(f"- {suggestion}")
        
        self.console.print(Panel(
            "\n".join(content),
            title="Validation Results",
            border_style="red"
        ))
    
    def _show_deployment_script(self, script: str):
        """
        Show the deployment script
        
        Args:
            script: The deployment script
        """
        self.console.print(Panel(
            Syntax(script, "python" if script.startswith('"""') else "sql", theme="monokai", line_numbers=True),
            title="Deployment Script",
            border_style="magenta"
        ))
