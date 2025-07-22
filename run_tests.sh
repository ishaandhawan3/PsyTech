#!/bin/bash
# Script to run the JSON storage tests and the application

echo "PsyTech Child Wellness Companion - JSON Storage Test Runner"
echo "=========================================================="
echo

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python; then
    echo "Error: Python is not installed or not in PATH"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "Error: This script must be run from the psyTech directory"
    echo "Please navigate to the psyTech directory and try again"
    exit 1
fi

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data/sessions
fi

# Run the JSON storage tests
echo "Running JSON storage tests..."
echo "----------------------------"
python test_json_storage.py
test_result=$?

echo
if [ $test_result -eq 0 ]; then
    echo "✅ Tests completed successfully!"
else
    echo "❌ Tests failed with exit code $test_result"
    echo "Please check the error messages above"
    exit $test_result
fi

echo
echo "Would you like to run the application now? (y/n)"
read -r run_app

if [[ $run_app =~ ^[Yy]$ ]]; then
    echo
    echo "Starting the application..."
    echo "-------------------------"
    
    # Check if Streamlit is installed
    if ! command_exists streamlit; then
        echo "Error: Streamlit is not installed"
        echo "Please install it with: pip install streamlit"
        exit 1
    fi
    
    # Run the application
    streamlit run frontend/main_app.py
else
    echo
    echo "You can run the application later with:"
    echo "  streamlit run frontend/main_app.py"
fi

echo
echo "Thank you for using PsyTech Child Wellness Companion!"
