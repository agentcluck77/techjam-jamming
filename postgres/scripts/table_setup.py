import os
import sys
import psycopg2
from dotenv import load_dotenv
# law 

load_dotenv()

DB_USER = os.getenv("DB_USER", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_PORT = int(os.getenv("DB_PORT", 5432))

# function to replace {{region}} 
def render_sql_template(sql_text: str, region: str) -> str:
    """Replace placeholder {{region}} in SQL template."""
    return sql_text.replace("{{region}}", region)

# function to check if table already exists
def table_exists(cursor, schema: str, table: str) -> bool:
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        )
    """, (schema, table))
    return cursor.fetchone()[0]


def setup_table(region: str):
    print("Starting table setup...")

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TABLE_PATH = os.path.join(SCRIPT_DIR, "data","tableCreation.sql")

    with open(TABLE_PATH, "r", encoding="utf-8") as f:
        table_creation_sql = f.read()

    # Render SQL with region replacement
    table_creation_sql = render_sql_template(table_creation_sql, region.lower())

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

        if table_exists(cursor, "techjam", f"t_law_{region}_regulations".lower()):
            print(f"Tables for {region} already exist. Skipping creation.")
        else:
            print("Creating tables...")
            cursor.execute(table_creation_sql)
            print("Executed SQL successfully!")
            conn.commit()
            print(f"{region} setup completed successfully!")

    except Exception as e:
        if conn:
            conn.rollback()
        print("Table setup failed:", repr(e))
        exit(1)
    finally:
        if conn:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    # Require table name as command-line argument
    if len(sys.argv) < 2:
        print("Error: You must provide a table name.")
        print("Usage: python tableSetup.py <table_name>")
        sys.exit(1)

    table_name = sys.argv[1]
    setup_table(table_name)

# python postgres\scripts\tableSetup.py utah