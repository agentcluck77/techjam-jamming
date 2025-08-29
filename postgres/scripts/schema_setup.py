import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = int(os.getenv("DB_PORT", 5432))


def setup_schema():
    print("Starting schema setup...")
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    SCHEMA_PATH = os.path.join(SCRIPT_DIR, "data","schemaCreation.sql")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_creation_sql = f.read()
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = False
        cursor = conn.cursor()

        print("Creating schema...")
        cursor.execute(schema_creation_sql)    

        conn.commit()
        print("Schema setup completed successfully!")

    except Exception as e:
        if conn:
            conn.rollback()
        print("Schema setup failed:", repr(e))
        exit(1)
    finally:
        if conn:
            cursor.close()
            conn.close()
        

if __name__ == "__main__":
    setup_schema()

# python postgres\scripts\schemaSetup.py