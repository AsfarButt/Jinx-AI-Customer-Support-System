# Jinx — AI Customer Support System

Jinx is an AI-powered customer support system designed to automate the repetitive, time-consuming work involved in handling customer emails.

Instead of simply asking an LLM to read an email and generate a reply, Jinx treats customer support as a **structured decision-making problem**. It identifies what the customer needs, retrieves the relevant customer/order/policy information, verifies whether it has enough information to act, and then chooses the appropriate action — such as resolving the issue, requesting verification, retrying retrieval, or escalating the case to a human.

The goal is simple: **automate first-line customer support while keeping responses accurate, traceable, and grounded in real business data.**

> **Note:** This repository contains a representative portion of the full system. Some modules involving proprietary data processing, client-specific integrations, production credentials, and internal infrastructure have been omitted for confidentiality. The architecture and workflow described below represent the overall system design. A live walkthrough or demo can be provided if required.

## What Problem Does Jinx Solve?

Traditional customer support often involves a support agent manually performing the same sequence of tasks:

1. Open the customer's email.
2. Understand what the customer is asking.
3. Identify the customer.
4. Find their order or account information.
5. Search through company policies or documentation.
6. Determine what can actually be done.
7. Write a response.
8. Escalate the issue if the information is insufficient.

For a large number of emails, this becomes repetitive and expensive.

Jinx automates this workflow while deliberately avoiding the idea of letting an LLM "make things up."

The LLM is given a **controlled set of actions** and has to work with retrieved information before it can resolve a case.

In other words:

**Email → Understand → Retrieve → Verify → Decide → Act → Respond**

---

## High-Level Architecture

```text
                    ┌─────────────────────┐
                    │    Customer Email   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Gmail API         │
                    │      Ingestion      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Email Processing &  │
                    │ Intent Classification│
                    └──────────┬──────────┘
                               │
                               ▼
                 ┌───────────────────────────┐
                 │       Retrieval Layer     │
                 │                           │
                 │ Customer / Order Data     │
                 │ PostgreSQL + pgvector     │
                 │ Policies / Documents      │
                 └─────────────┬─────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Decision / Action  │
                    │       Loop          │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
            Verify          Check          Retry
            Customer        Policy       Retrieval
                 │             │             │
                 └─────────────┼─────────────┘
                               │
                        ┌──────┴──────┐
                        ▼             ▼
                    Resolve       Escalate
                        │             │
                        ▼             ▼
                  ┌────────────────────────┐
                  │   Response Generation  │
                  │   + Sufficiency Check  │
                  └───────────┬────────────┘
                              │
                              ▼
                       Customer Reply
```

---

# How Jinx Works

## 1. Email Ingestion

Jinx begins by monitoring incoming customer-support emails through the Gmail API.

Instead of requiring an agent to manually copy an email into an AI system, incoming messages are automatically collected and passed into the processing pipeline.

The system extracts important information such as:

* Sender information
* Email subject
* Message body
* Thread information
* Previous conversation context
* Message metadata

This allows Jinx to understand not only the latest email but also the context of the ongoing conversation when required.

---

## 2. Understanding the Customer's Intent

Once an email is ingested, Jinx determines what the customer is actually trying to accomplish.

For example, an email such as:

> "Hi, I placed an order three days ago but it still hasn't arrived. Can you tell me where it is?"

could be classified as an **order-status / delivery inquiry**.

Other possible intents include:

* Order status
* Missing order
* Product information
* Return request
* Refund request
* Shipping question
* Policy question
* Customer complaint
* Identity/customer verification
* General support question
* Unknown or unsupported request

Intent classification helps the system determine what information it needs to retrieve and which actions are relevant.

---

# 3. Customer and Order Retrieval

After understanding the request, Jinx searches the company's structured data.

The system uses **PostgreSQL with pgvector** as part of its retrieval infrastructure.

The representative dataset contains:

* **8,000+ customers**
* **42,000+ orders**
* Product information
* Shipping/carrier information
* Warehouse information
* Return information
* Other structured business data

For example, if a customer asks:

> "Where is my order?"

Jinx needs to determine:

```text
Who is the customer?
        ↓
Which order belongs to them?
        ↓
What is the current order status?
        ↓
Which carrier is handling it?
        ↓
What does the relevant policy say?
        ↓
Can the issue be resolved automatically?
```

This is fundamentally different from simply asking an LLM to answer the question.

The model must first obtain the underlying data.

---

# 4. Document and Policy Retrieval

Not every support question can be answered using database records.

Some questions require company policies or documentation.

For example:

> "Can I return an item after 35 days?"

The customer's order data alone is not enough.

Jinx can retrieve relevant documents such as:

* Return policies
* Refund policies
* Shipping policies
* Warranty information
* FAQs
* Internal support documentation
* Product documentation
* Other relevant knowledge sources

This creates a hybrid retrieval system:

```text
                    Customer Question
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
       Structured Data             Documents
       PostgreSQL                  Policies / FAQ
       Orders                     Knowledge Base
       Customers
       Products
              │                         │
              └────────────┬────────────┘
                           ▼
                    Relevant Context
```

The LLM then reasons over the retrieved information rather than relying solely on its pretrained knowledge.

---

# 5. The Action-Based Resolution Loop

One of the core design decisions in Jinx is that the LLM does **not** have unlimited freedom to decide what to do.

Instead, it operates using a predefined action set.

The available actions include:

```text
verify customer
check policy
retry retrieval
resolve
escalate
```

The LLM effectively acts as a decision-maker inside a controlled state machine.

For example:

```text
Customer email
      │
      ▼
Need customer identity?
      │
     YES
      │
      ▼
verify customer
      │
      ▼
Customer verified
      │
      ▼
Need policy information?
      │
     YES
      │
      ▼
check policy
      │
      ▼
Enough information?
   ┌──┴──┐
  YES    NO
   │      │
   ▼      ▼
resolve  retry retrieval
          │
          ▼
      Still missing?
       ┌──┴──┐
      YES    NO
       │      │
       ▼      ▼
   escalate  resolve
```

This makes the system much more predictable than a simple "ask the AI to solve the problem" architecture.

---

# 6. Persistent Case State

Jinx maintains state for each support case/thread.

This is important because customer support is often a multi-step process.

For example, the system might initially determine:

```text
Intent: Return request

Customer: Not yet verified
Policy: Retrieved
Order: Found
Required information: Customer verification
Next action: verify customer
```

After verification, the system can continue from the existing state instead of starting from scratch.

The case can therefore move through states such as:

```text
NEW
 ↓
CLASSIFIED
 ↓
RETRIEVING
 ↓
VERIFYING
 ↓
POLICY_CHECK
 ↓
READY_TO_RESOLVE
 ↓
RESOLVED
```

or:

```text
NEW
 ↓
CLASSIFIED
 ↓
RETRIEVAL_FAILED
 ↓
RETRY
 ↓
STILL_INSUFFICIENT
 ↓
ESCALATED
```

This stateful design makes the pipeline easier to debug, monitor, and extend.

---

# 7. Sufficiency Checks

A major concern with AI customer support is hallucination.

Jinx therefore does not simply generate a response immediately after retrieval.

Before sending a response, the system checks whether there is enough reliable information to answer the customer.

For example:

```text
Customer asks:
"Where is my order?"

Retrieved:
✓ Customer identified
✓ Order identified
✓ Tracking information found
✓ Carrier identified
✓ Current status available

Result:
Sufficient information → Resolve
```

But if the system finds:

```text
✓ Customer identified
✗ Order cannot be confidently identified
✗ Tracking information unavailable

Result:
Insufficient information → Retry or Escalate
```

This is an important safety mechanism because **not knowing the answer is better than confidently giving the customer an incorrect answer.**

---

# 8. Response Generation

Once the case has been successfully resolved, Jinx generates the customer-facing response.

The response is based on the information retrieved during the previous stages.

For example:

```text
Customer:
"Where is my order?"

Retrieved information:
Order: #12345
Carrier: XYZ
Status: In transit
Expected delivery: August 19

Generated response:
"Hi, your order is currently in transit with XYZ and is
expected to arrive on August 19. We'll keep you updated
if there are any changes."
```

The model is not expected to invent the order status or delivery date.

Those details come from the underlying retrieval system.

---

# 9. Tone Matching

Jinx also considers the tone of the incoming customer message.

A short and straightforward request may receive a concise response.

A frustrated customer may receive a more empathetic response.

For example:

```text
Customer:
"This is the third time I've contacted you about this.
Where is my refund?"

```

The system can generate a response that acknowledges the frustration while still grounding the actual information in retrieved records.

The goal is to combine:

**Accurate information + appropriate tone + controlled generation**

---

# 10. Escalation to a Human

Automation does not mean every case should be handled automatically.

Some cases are inherently ambiguous, sensitive, or outside the system's capabilities.

Jinx therefore has an explicit `escalate` action.

Examples include:

* Customer cannot be confidently identified
* Multiple orders match the available information
* Required data is missing
* Retrieval repeatedly fails
* Policy does not clearly cover the situation
* The request requires manual intervention
* The system cannot safely determine the correct resolution

Instead of hallucinating an answer, Jinx can stop and hand the case to a human support agent.

This creates a practical **human-in-the-loop architecture**.

---

# Technology Stack

The system is built around several components working together:

### Email Layer

**Gmail API**

Used for:

* Reading incoming emails
* Detecting relevant messages
* Accessing conversation threads
* Sending customer responses

### Backend / Processing

**Python**

Used to implement:

* Email processing
* Business logic
* Data retrieval
* AI orchestration
* Validation
* Case-state management

### AI / LLM Layer

An LLM is used for:

* Intent classification
* Context interpretation
* Action selection
* Decision-making
* Response generation

The model is constrained by the application's action space rather than being given unrestricted control.

### Database

**PostgreSQL**

Used for structured business information including:

* Customers
* Orders
* Products
* Returns
* Carriers
* Warehouses
* Other operational records

### Vector Search

**pgvector**

Used to support semantic retrieval over relevant textual information and documents.

This allows the system to retrieve information based on meaning rather than relying exclusively on exact keyword matches.

### Retrieval / RAG

The system combines structured database queries with document retrieval to provide the LLM with the context required to make a decision.

---

# Why This Architecture?

A basic AI customer-support system might look like:

```text
Email → LLM → Response
```

Jinx takes a more controlled approach:

```text
Email
  ↓
Intent
  ↓
Retrieve Data
  ↓
Verify Information
  ↓
Select Action
  ↓
Check Sufficiency
  ↓
Resolve / Retry / Escalate
  ↓
Generate Response
```

This additional structure provides several advantages.

### Reduced Hallucination

The model is encouraged to answer using retrieved information instead of inventing facts.

### Better Reliability

The system can retry retrieval when information is incomplete instead of immediately producing an answer.

### Controlled AI Behavior

The LLM chooses from predefined actions instead of having unrestricted access to business operations.

### Explainability

Each case has a sequence of actions and states that can be inspected later.

### Human Escalation

Cases that cannot be safely automated can be passed to a human.

### Scalability

The same architecture can process many support cases without requiring an agent to manually perform every repetitive step.

---

# Example End-to-End Case

Consider a customer sending:

> "Hi, I ordered a laptop last week and it still hasn't arrived. Can you check what's going on?"

Jinx processes the case roughly like this:

```text
1. INGEST
   ↓
   Gmail API receives the email.

2. CLASSIFY
   ↓
   Intent = Order / Delivery Status

3. IDENTIFY CUSTOMER
   ↓
   Match sender information with customer records.

4. RETRIEVE ORDER
   ↓
   Search customer's orders.

5. RETRIEVE SHIPPING INFORMATION
   ↓
   Find carrier and current delivery status.

6. CHECK POLICY
   ↓
   Determine whether the shipment is still within
   the expected delivery window.

7. DECIDE
   ↓
   Enough information available → resolve.

8. GENERATE RESPONSE
   ↓
   Create a customer-friendly response using
   the retrieved order information.

9. SEND
   ↓
   Reply through Gmail.

10. STORE STATE
   ↓
   Persist the outcome for the conversation.
```

The important part is that the LLM is not independently guessing what happened to the order.

It is coordinating a process that connects the customer's question to actual business data.

---

# Core Design Philosophy

Jinx is built around a simple principle:

> **The LLM should reason about the information, not invent the information.**

The database provides facts.

The document retrieval system provides policies and knowledge.

The application controls what actions are possible.

The LLM determines what needs to happen next.

The validation layer determines whether there is enough information to safely respond.

And the escalation mechanism provides a safe fallback when automation is not appropriate.

---

# Project Structure

A simplified representation of the system can be thought of as:

```text
Jinx/
│
├── ingestion/
│   └── gmail.py
│
├── classification/
│   └── intent.py
│
├── retrieval/
│   ├── customers.py
│   ├── orders.py
│   ├── documents.py
│   └── vector_search.py
│
├── decision/
│   ├── actions.py
│   ├── state.py
│   └── resolution_loop.py
│
├── response/
│   ├── generation.py
│   └── validation.py
│
├── database/
│   └── postgres.py
│
└── main.py
```

The actual repository contains additional components and integrations that are not included in this representative version.

---

# What Makes Jinx Different?

Jinx is not simply an email chatbot.

It is an **AI-driven support orchestration system**.

The LLM is one component inside a larger pipeline involving:

* Email ingestion
* Intent classification
* Structured database queries
* Semantic document retrieval
* Customer verification
* Policy checking
* Stateful decision-making
* Action selection
* Sufficiency validation
* Response generation
* Human escalation

The result is a system designed to make AI useful in a real customer-support environment while maintaining control over what the AI can actually do.

## Summary

At a high level, Jinx turns this:

```text
Customer Email
      ↓
Human Agent
      ↓
Search Database
      ↓
Search Policies
      ↓
Make Decision
      ↓
Write Reply
```

into:

```text
Customer Email
      ↓
       Jinx
      ↓
Understand the Request
      ↓
Retrieve Relevant Data
      ↓
Verify Customer / Order
      ↓
Check Policies
      ↓
Choose an Action
      ↓
Validate Information
      ↓
 ┌────┴────────┐
 ↓             ↓
Resolve     Escalate
 ↓             ↓
Reply       Human Agent
```

The overall objective is to automate the **first line of customer support** without turning the LLM into an uncontrolled black box.

Jinx combines **LLM reasoning, RAG, structured database retrieval, stateful workflows, and deterministic business logic** to create a customer-support pipeline that is both intelligent and operationally controlled.
