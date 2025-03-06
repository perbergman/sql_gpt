#!/bin/bash
# Run SQL-GPT locally without Docker

# Verify OPENAI_API_KEY is available
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable not found"
    echo "Please make sure to run this script from a shell where OPENAI_API_KEY is set"
    echo "For example: OPENAI_API_KEY=your_key_here ./scripts/run_local.sh"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Run the application
echo "Starting SQL-GPT..."
python src/main.py --web --host 0.0.0.0 --port 5000
