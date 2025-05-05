import os
import sys
import webbrowser
import uvicorn
from threading import Timer

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def open_browser():
    """Open browser with API documentation after a short delay"""
    webbrowser.open('http://localhost:8000/docs')

if __name__ == "__main__":
    # Open browser after 5 seconds
    Timer(5, open_browser).start()
    
    print("Starting FDA Oncology Copilot Word Add-in backend service...")
    print("Service running at http://localhost:8000")
    print("Word Add-in is ready to use. Please follow these steps to install it in Word:")
    print("1. Open Microsoft Word")
    print("2. Go to 'Insert' > 'Get Add-ins' > 'Manage My Add-ins' > 'Upload My Add-in'")
    print("3. Select the 'word_addin/manifest.xml' file")
    print("4. Click 'Install'")
    
    # Start FastAPI server
    from word_addin.server import app
    uvicorn.run(app, host="0.0.0.0", port=8000)
