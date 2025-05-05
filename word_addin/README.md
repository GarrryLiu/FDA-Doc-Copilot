# FDA Oncology Copilot Word Add-in

This add-in allows you to use FDA Oncology Copilot functionality directly within Microsoft Word, generating FDA-style executive summaries for oncology documents.

## Quick Start

### Using the Setup Scripts

For the easiest setup experience, use one of the provided setup scripts:

#### On macOS/Linux:
```bash
# Make the script executable
chmod +x word_addin/run_word_addin.sh

# Run the setup script
./word_addin/run_word_addin.sh
```

#### On Windows:
```
word_addin\run_word_addin.bat
```

These scripts will:
1. Check for required dependencies
2. Install necessary packages
3. Create a `.env` file if needed
4. Build vector indices if they don't exist
5. Start the backend service
6. Provide instructions for installing the add-in in Word

### Manual Installation Steps

If you prefer to install manually, follow these steps:

#### 1. Install Dependencies

Ensure you have Python 3.7 or higher installed, then run:

```bash
pip install -r requirements.txt
```

#### 2. Start the Backend Service

```bash
python word_addin/run_server.py
```

This will start the backend service and automatically open a browser window with the API documentation.

#### 3. Install the Add-in in Word

1. Open Microsoft Word
2. Go to "Insert" > "Get Add-ins" > "Manage My Add-ins" > "Upload My Add-in"
3. Select the `word_addin/manifest.xml` file
4. Click "Install"

## Usage Instructions

1. In Word, go to the "Insert" tab and click on "FDA Oncology Copilot"
2. Select text in your document that you want to summarize
3. In the add-in panel:
   - Select a data source
   - Apply filters if needed (disease type, trial phase, document section)
   - Click "Summarize Selected Text"
4. Review the generated summary and reference documents
5. Click "Insert Summary into Document" to add the summary to your document

## Troubleshooting

- **Add-in not appearing**: Make sure the backend service is running (`python word_addin/run_server.py`)
- **Connection errors**: Ensure the service is running on port 8000 and not blocked by a firewall
- **No data sources**: Make sure you've built the vector indices by running `python scripts/build_indices.py`
- **Add-in not loading**: Try restarting Word and reinstalling the add-in

## Development Notes

### Architecture

The Word add-in consists of:

1. **Frontend**: HTML/CSS/JavaScript using Office.js API
2. **Backend**: Python FastAPI server exposing the existing FDA Oncology Copilot functionality
3. **Manifest**: XML file describing the add-in to Microsoft Word

### Files

- `manifest.xml`: Word add-in manifest
- `run_server.py`: Script to start the backend service
- `server.py`: FastAPI backend implementation
- `web/`: Frontend files (HTML, CSS, JavaScript)

### Security Considerations

- The backend server allows CORS from all origins for development purposes
- In a production environment, you should restrict CORS to specific domains
- Consider adding authentication for the API endpoints

## License

This project is licensed under the MIT License - see the LICENSE file for details.
