import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from dateutil import parser  # Install with: pip install python-dateutil
import pytz

# Path to your service account JSON file
SERVICE_ACCOUNT_FILE = "service_account.json"

# Define the scope
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Authenticate and connect to Google Sheets
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1uwGyzX4wk92dzf1e5Co7CwpzdxCEa6u_98jYyxxDH7Y/edit?usp=sharingL"  # Replace with your actual Google Sheet URL
sheet = client.open_by_url(SHEET_URL)
worksheet = sheet.sheet1


def get_record():
    """Fetch the latest response from the Google Sheet if it's within the last minute."""
    records = worksheet.get_all_records()
    if not records:
        return None

    latest_response = records[-1]
    timestamp_str = latest_response[list(latest_response.keys())[0]]

    try:
        latest_timestamp = parser.parse(timestamp_str)  # Auto-detect format
    except ValueError:
        print(f"❌ Error: Unable to parse timestamp '{timestamp_str}'")
        return None

    # Convert to system timezone
    sheet_tz = pytz.utc  # Adjust if needed
    system_tz = pytz.timezone("Asia/Kolkata")  # Set your timezone
    latest_timestamp = latest_timestamp.replace(tzinfo=sheet_tz).astimezone(system_tz)
    now = datetime.now(system_tz)

    # Check if the response is recent
    if (now - latest_timestamp) < timedelta(minutes=1):
        return latest_response
    else:
        return None

# Example Usage:
# latest = get_latest_response()
# if latest:
#     print("Latest response:", latest)
# else:
#     print("No recent response found.")