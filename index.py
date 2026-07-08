import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import get_app

app = get_app()

# Vercel expects a handler function
async def handler(event, context):
    return await app(event, context)

# Also export app for compatibility
handler = app