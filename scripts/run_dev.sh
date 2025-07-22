# Quick launcher for FiduciaMVP development server

# Get the directory where this script is located
SCRIPT_DIR=\"$( cd \"$( dirname \"${BASH_SOURCE[0]}\" )\" && pwd )\"
PROJECT_ROOT=\"$(dirname \"$SCRIPT_DIR\")\"

# Change to project root
cd \"$PROJECT_ROOT\"

# Activate virtual environment
if [ -f \"venv/bin/activate\" ]; then
    source venv/bin/activate
else
    echo \"❌ Virtual environment not found. Please run ./scripts/setup.sh first\"
    exit 1
fi

# Run the development server
python scripts/run_dev.py