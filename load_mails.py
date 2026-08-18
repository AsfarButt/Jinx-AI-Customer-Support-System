import base64
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def extract_body(payload):
    if "parts" not in payload:
        body = payload.get("body", {}).get("data")
        if body:
            return base64.urlsafe_b64decode(body).decode("utf-8", errors="ignore")
        return ""

    for part in payload["parts"]:
        if part.get("mimeType") == "text/plain":
            body = part.get("body", {}).get("data")
            if body:
                return base64.urlsafe_b64decode(body).decode(
                    "utf-8",
                    errors = "ignore"
                )

    for part in payload["parts"]:
        if "parts" in part:
            text = extract_body(part)
            if text:
                return text

    return ""
    


def fetch_unread_emails(service):
    unread_messages = []
    page_token = None

    print("Searching for unread mails...")  

    while True:
        response = (
            service.users()
            .messages()
            .list(
                userId = "me",
                q = "is:unread newer_than:1d",
                maxResults = 100,
                pageToken = page_token
            )
            .execute()
        )

        unread_messages .extend(response.get("messages", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    if not unread_messages:
        print("No unread mails found :(")
        return []

    print(f"Found {len(unread_messages)} unread mails :)")

    emails = []

    for index, msg in enumerate(unread_messages, start=1):
        message = (
            service.users()
            .messages()
            .get(
                userId = "me",
                id = msg["id"],
                format = "full"
            )
            .execute()
        )

        headers = message["payload"].get("headers", [])

        sender = ""
        subject = ""
        date = ""

        for header in headers:
            if header["name"] == "From":
                sender = header["value"]

            elif header["name"] == "Subject":
                subject = header["value"]

            elif header["name"] == "Date":
                date = header["value"]

        body = extract_body(message["payload"])

        email_data = {
            "id" : msg["id"],
            "thread_id" : message["threadId"],
            "sender" : sender,
            "subject" : subject,
            "date" : date,
            "body" : body
        }

        emails.append(email_data)

        print(f"Email #{index}")
        print(f"From    : {sender}")
        print(f"Subject : {subject}")
        print(f"Date    : {date}")
        print("\nBody Preview:")
        print(body[:500])     
        print("\n")

    return emails

def get_gmail_service():
    creds = None
    # token.json stores your access/refresh token after first login
    if os.path.exists('../token.json'):
        creds = Credentials.from_authorized_user_file('../token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('../credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # opens browser for login
        with open('../token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)


# if __name__ == '__main__':
#     service = get_gmail_service()
#     emails = fetch_unread_emails(service)
