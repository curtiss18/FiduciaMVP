"""Run FiduciaMVP development server with proper configuration."""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = f"{project_root}:{project_root}/src"

def check_services():
    """Check if Docker services are running."""
    print("🔍 Checking services...")
    
    # Check Docker services
    result = subprocess.run(
        ["docker-compose", "ps"],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    if "postgres" in result.stdout and "Up" in result.stdout:
        print("✅ PostgreSQL is running")
    else:
        print("⚠️  PostgreSQL is not running. Starting Docker services...")
        subprocess.run(["docker-compose", "up", "-d"], cwd=project_root)
        
    if "redis" in result.stdout and "Up" in result.stdout:
        print("✅ Redis is running")
    else:
        print("⚠️  Redis is not running. Starting Docker services...")
        subprocess.run(["docker-compose", "up", "-d"], cwd=project_root)


def main():
    """Run the development server."""
    print("🚀 Starting FiduciaMVP Development Server")
    print("=" * 40)
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python path: {os.environ.get('PYTHONPATH')}")
    print("=" * 40)
    
    # Check services
    check_services()
    
    print("🌐 Server starting...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("📊 Alternative Docs: http://localhost:8000/redoc")
    print("🔍 Health Check: http://localhost:8000/api/v1/health")
    print("✋ Press CTRL+C to stop the server")
    print("=" * 40)
    
    # Run uvicorn
    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "src.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--log-level", "info"
    ], cwd=project_root)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("👋 Server stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)