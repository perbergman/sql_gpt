# SQL-GPT: Natural Language to PostgreSQL Generator

A tool that converts natural language prompts into advanced PostgreSQL queries and deployment scripts.

## Features

- Convert natural language to PostgreSQL queries
- Generate database schema from descriptions
- Create deployment scripts for database migrations
- Support for advanced PostgreSQL features (indexes, partitioning, etc.)
- Interactive mode for query refinement

## Installation

```bash
# Create and activate virtual environment
python -m venv venv

# On macOS/Linux
source venv/bin/activate

# On Windows
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py "Create a table for storing user information with name, email, and registration date"
```

Or use the interactive mode:

```bash
python src/main.py --interactive
```

## Documentation

See the `docs` directory for detailed documentation.
