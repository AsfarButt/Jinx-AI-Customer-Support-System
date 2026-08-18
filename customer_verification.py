from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def user_verification(email):
    from langchain_groq import ChatGroq
    from dotenv import load_dotenv

    import os

    load_dotenv(dotenv_path="E:/Asfar/Learning/Project01/codefiles/.env")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY01")
    )
    import importlib
    import email_reply
    importlib.reload(email_reply)

    id_extraction_prompt = ChatPromptTemplate.from_template("""
    You are extracting identifying information from a customer complaint email for TechSphere.

    Email Details:

    Sender:
    {sender}

    Subject:
    {subject}

    Body:
    {body}

    Read the email text above and extract, if present:

    - An order ID (format: ORD00123)
    - A customer ID (format: CUST000123)
    - Email of the customer (format: abc@xyz.com)

    Do not guess or infer any IDs.

    If none is present, return all as null.

    Also summarize the customer's complaint in first-person singular.

    Return ONLY this JSON object:

    {{
        "order_id": string or null,
        "customer_id": string or null,
        "email": string or null
        "user_name": string or '' (leave it empty if you are not sure or if the name doesn't make any sense)
        "email_summary": string
    }}
    """)

    chain = id_extraction_prompt | llm | JsonOutputParser()
    email["body"] = " ".join(email["body"].split()[:2000])
    response = chain.invoke({
    "sender": email["sender"],
    "subject": email["subject"],
    "body": email["body"]
    })

    print("Complaint Summary:")
    print(response["email_summary"])

    verify_id_mail = {
        "subject": "Quick info needed to verify your order",
        "body": """
Hi,
\nThanks for reaching out!
\nBefore we can move forward, could you please share your Order ID or Customer ID (or any other detail that helps us confirm your purchase)?
Once we have that, we'll take it from there.
\nThanks,
TechSphere Support Team
        """
    }

    if response["order_id"] is None and response["customer_id"] is None and response['email'] is None:

        email_reply.mail_sender(
            email["sender"],
            verify_id_mail["subject"], 
            verify_id_mail["body"],
            email['id'],
            email["thread_id"], 
            "missing_ID"
        )

        print("Verification email sent.")
        response['verification'] = False

    else:

        print("Customer already provided verification information.")
        response['verification'] = True

    return response

