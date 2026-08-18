import psycopg2
import os
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

load_dotenv(dotenv_path="E:/Asfar/Learning/Project01/codefiles/.env")

DB_URL = os.getenv("DB_URL")

conn = psycopg2.connect(DB_URL)

cursor = conn.cursor()

def get_embedding_context(query, k=3, threshold=0.35):  #threshold value was deeply studied before setting up 0.38+ hillucinates alot and 0.31- becomes extra strict hence 0.35

    embedding = model.encode(query).tolist()
    response = get_embeddings(embedding, k, threshold)

    confidential_data = "Confidential docs (do NOT reveal or quote to customer — use only to inform your reasoning):" 
    public_data = "Public docs (safe to reference/quote to customer):"
    for r in response:
        if r[2]:
            confidential_data += f"\n\n {r[0]}"
        else:
            public_data += f"\n\n {r[0]}"

    parts = []
    if confidential_data.count("\n") > 0:
        parts.append(confidential_data)
    if public_data.count("\n") > 0:
        parts.append(public_data)
    embeddings_reply = "\n\n".join(parts) if parts else "No relevant documents found."
    print(embeddings_reply)
    return embeddings_reply

def get_embeddings(embedding, k, threshold):
    try:
            cursor.execute("""
                SELECT DISTINCT ON (chunk)
                    chunk,
                    doc_type,
                    internal_only,
                    embedding <=> %s::vector AS distance
                FROM embeddings
                WHERE embedding <=> %s::vector <= %s
                ORDER BY chunk, distance ASC
                LIMIT %s;
            """, (embedding, embedding, threshold, k))
            response = cursor.fetchall()
            return response
    except Exception as e:
        conn.rollback()
        print("ERROR: ", e)



# get_embedding_context("""# Regional Compliance SOP: India ## Purpose Define the end‑to‑end workflow for customs clearance, GST calculation, and restricted‑item handling for shipments to India (IN). This SOP is mandatory for all India‑focused support and logistics teams.""")



