"""
Entry point for Google Cloud Run deployment.
This file imports the FastAPI app from the app module.
"""

import os
from app.main import app

# This is required for Cloud Run to find the application
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port) 