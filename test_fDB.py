from firebase_config import db, bucket

# Firestore test
doc_ref = db.collection("test").document("my_test_doc")
doc_ref.set({"hello": "Firebase!"})

# Storage test
if bucket:
    blob = bucket.blob("test.txt")
    blob.upload_from_string("Hello Firebase Storage!")

print("Data written successfully!")
