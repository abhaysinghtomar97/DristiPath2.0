import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify the environment variable is loaded
print(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')}")
print(f"FIREBASE_STORAGE_BUCKET: {os.environ.get('FIREBASE_STORAGE_BUCKET')}")

# Now import Firebase config
from firebase_config import db, bucket

# Test Firestore
doc_ref = db.collection("test").document("my_test_doc")
doc_ref.set({"hello": "Firebase!", "test": "success"})

# Test Storage
if bucket:
    blob = bucket.blob("test.txt")
    blob.upload_from_string("Hello Firebase Storage!")
    print("Storage test successful!")

print("Firebase connection successful!")