import psycopg2
import os
from dotenv import load_dotenv




def fetch_data(tableName, ID_type, ID):
    load_dotenv(dotenv_path="E:/Asfar/Learning/Project01/codefiles/.env")
    # print(os.getenv("DB_URL"))
    DB_URL = os.getenv("DB_URL")
    conn = psycopg2.connect(DB_URL)

    cursor = conn.cursor()

    cursor.execute("SELECT version();")

    print(cursor.fetchone())

    if tableName == '':
        TABLE_MAP = {
            "carrier_id": "carriers",
            "customer_id": "customers",
            "order_id": "orders",
            "product_id": "products",
            "return_id": "returns",
            "partner_id": "shipping_partners",
            "tracking_id": "tracking",
            "warehouse_id": "warehouses",
            "email_id": "tickets",
        }

        tableName = TABLE_MAP.get(ID_type)

    if tableName is None:
        return "Unknown ID type"

    try:
        cursor.execute(f"""
            SELECT *
            FROM {tableName}
            WHERE {ID_type} = %s;
        """,(ID,))
            
        return cursor.fetchone()    
    
    except Exception as e:
        print("Error:", e)
        conn.rollback()
        return "No Data Found :("


print(fetch_data("","order_id","ORD000000262"))
# ORD000000262
 