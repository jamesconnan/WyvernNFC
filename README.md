# WyvernNFC Google Drive Integration

This project provides functionality to download credentials files from Google Drive.

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Drive API:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the Google Drive API
   - Create OAuth 2.0 credentials (Desktop application)
   - Download the credentials file and upload it to your Google Drive

3. Run the script:
```bash
python google_drive_utils.py
```

The script will:
- Authenticate with Google Drive
- Search for a file named `credentials.json`
- Download the file to your local directory
- Save the authentication token for future use

## Security Notes

- The `token.pickle` file contains sensitive authentication information
- Keep your credentials file secure and never commit it to version control
- The downloaded credentials file will be saved in the same directory as the script

## Error Handling

The script includes error handling for:
- Missing or invalid credentials
- Network issues
- File not found on Google Drive
- Permission issues 