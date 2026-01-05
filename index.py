"""
Vercel Entry Point for Smart Irrigation System
==============================================
This file serves as the WSGI entry point for Vercel deployment
"""

from app import app

# Vercel expects a handler function
def handler(event, context):
    return app

# For Vercel serverless functions
application = app

if __name__ == "__main__":
    app.run()