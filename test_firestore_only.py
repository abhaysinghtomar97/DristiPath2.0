import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("Testing Firebase Firestore connection...")
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")

# Import Firebase config
from firebase_config import db, bucket

# Test Firestore only
try:
    doc_ref = db.collection("test").document("connection_test")
    doc_ref.set({
        "message": "Firebase connection successful!",
        "timestamp": "2024-01-01",
        "test_type": "credentials_fix"
    })
    print("SUCCESS: Firestore connection successful!")
    
    # Read back the data to confirm
    doc = doc_ref.get()
    if doc.exists:
        print(f"SUCCESS: Data written and read successfully: {doc.to_dict()}")
    else:
        print("ERROR: Document was not found after writing")
        
except Exception as e:
    print(f"ERROR: Firestore connection failed: {e}")

print("Test completed!")