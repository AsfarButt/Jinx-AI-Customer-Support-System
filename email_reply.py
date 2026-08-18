import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

_service = None   # cache the authenticated service


def authenticate():
    creds = None

    if os.path.exists("../token.json"):
        creds = Credentials.from_authorized_user_file("../token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "../credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open("../token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_service():
    global _service

    if _service is None:
        _service = authenticate()

    return _service

# {'id': '19fd24c32565ac17',
#  'thread_id': '19fd24c32565ac17',
#  'sender': 'Pinterest <recommendations@explore.pinterest.com>',
#  'subject': 'Podcast Studio Design',
#  'date': 'Wed, 05 Aug 2026 14:20:36 +0000',
#  'body': 'To view this content open ticy%2Fterms-of-service%2F\n\n UnsubscriTqt5kD6d%26utm_campaign%3Djourney_aware_pins%26e_t%3D960395f42d464e9aadfa9243dff2c3a9%26e_t_s%3Dfooter%26utm_source%3D31%26utm_medium%3D2012'}

def send_email(service, to_email, subject, body, thread_id=None, in_reply_to=None, references=None):

    if not body:
        print("Email sending terminated.. msg is null")
        return 

    message = MIMEText(body)
    message["to"] = to_email
    message["subject"] = subject

    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
    if references:
        message["References"] = references

    raw = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    send_body = {"raw": raw}
    if thread_id:
        send_body["threadId"] = thread_id

    return (
        service.users()
        .messages()
        .send(
            userId="me",
            body=send_body
        )
        .execute()
    )

def add_label(service, msg_id, reason):

    # service = get_service()

    # labels = service.users().labels().list(userId="me").execute()

    # for label in labels["labels"]:
    #     print(label["name"], "=>", label["id"])

    match reason:
        
        case "missing_ID":
            label_id = 'Label_5856622068776614595'
        case "customer_not_found":
            label_id = 'Label_1408808667576335281'
        case "case_closed":
            label_id = 'Label_6468663163554220537'
        case 'more_info_needed':
            label_id = 'Label_5781506853081385281'
        case 'user_complaint':
            label_id = 'Label_9118689366844345354'
        case _:
            print("No matching label found :(")
            label_id = ''

    if label_id == '':
        print("Label setting terminated.. no reason")
        return 
    else:
        service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={
            "addLabelIds": [label_id]
        }
        ).execute()
        print("Label added successfully :)")
            

def get_message_id_header(service, msg_id):
    msg = service.users().messages().get(
        userId="me", id=msg_id, format="metadata",
        metadataHeaders=["Message-ID"]
    ).execute()
    headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
    return headers.get("Message-ID")


def mail_sender(to_email, subject, body, msg_id, thread_id, reason):
    service = get_service()
    add_label(service, msg_id, reason)

    original_message_id = get_message_id_header(service, msg_id)

    return send_email(
        service, to_email, subject, body,
        thread_id=thread_id,
        in_reply_to=original_message_id,
        references=original_message_id
    )

# mail_sender("2503599@students.au.edu.pk", "A", "B", "alu", "siehg")

# from googleapiclient.discovery import build
# from google.oauth2.credentials import Credentials

# SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# creds = Credentials.from_authorized_user_file(
#     "../token.json",
#     SCOPES
# )

# service = build("gmail", "v1", credentials=creds)

# results = service.users().labels().list(userId="me").execute()

# labels = results.get("labels", [])

# for label in labels:
#     print(f"Name: {label['name']}")
#     print(f"ID:   {label['id']}")
#     print("-" * 30)

