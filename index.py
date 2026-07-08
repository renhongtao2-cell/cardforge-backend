import sys
import os

# Ensure the current directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and expose the FastAPI app
from app import get_app

app = get_app()

# Vercel serverless handler
handler = app