"""
Entry point for Google App Engine deployment.
This file imports the FastAPI app from the app module.
"""

from app.main import app

# This is required for App Engine to find the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 