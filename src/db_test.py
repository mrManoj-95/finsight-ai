import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load environment variables
load_dotenv()

# Database connection URL (matches your docker-compose credentials)
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+psycopg://finsight:finsight@localhost:5432/finsight"
)

def test_connection():
    print(f"Connecting to database at: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as connection:
        # Check PostgreSQL Version
        pg_version = connection.execute(text("SELECT version();")).fetchone()
        print(f"✅ PostgreSQL Connected: {pg_version[0]}")
        
        # Check pgvector Extension
        vector_ext = connection.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';")).fetchone()
        if vector_ext:
            print(f"✅ Vector Extension Ready: {vector_ext[0]} (v{vector_ext[1]})")
        else:
            print("❌ Vector extension not detected. Please run the docker exec CREATE EXTENSION command.")

if __name__ == "__main__":
    test_connection()