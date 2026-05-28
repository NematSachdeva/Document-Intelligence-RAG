"""
Initialize Chroma Cloud collection
"""
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()

# Get Chroma Cloud credentials
host = os.getenv("CHROMA_HOST", "api.trychroma.com")
api_key = os.getenv("CHROMA_API_KEY")
tenant = os.getenv("CHROMA_TENANT")
database = os.getenv("CHROMA_DATABASE", "DocumentIntelligence")

if not api_key or not tenant:
    print("❌ Missing Chroma Cloud credentials in .env")
    exit(1)

try:
    # Connect to Chroma Cloud
    client = chromadb.HttpClient(
        host=host,
        port=443,
        ssl=True,
        headers={"Authorization": f"Bearer {api_key}"},
        tenant_name=tenant,
        database_name=database
    )
    
    print(f"✓ Connected to Chroma Cloud")
    print(f"  Host: {host}")
    print(f"  Tenant: {tenant}")
    print(f"  Database: {database}")
    
    # Try to get or create collection
    try:
        collection = client.get_collection(name="DocumentIntelligence")
        print(f"✓ Collection 'DocumentIntelligence' already exists")
        print(f"  Documents: {collection.count()}")
    except Exception:
        collection = client.create_collection(
            name="DocumentIntelligence",
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✓ Created collection 'DocumentIntelligence'")
    
    print("\n✅ Chroma Cloud initialized successfully!")
    
except Exception as e:
    print(f"❌ Error connecting to Chroma Cloud: {e}")
    exit(1)
