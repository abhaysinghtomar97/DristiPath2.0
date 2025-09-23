import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'C:/Users/Abhay Singh/SIH/dristipath2.0/secrets/dristipath-23021-firebase-adminsdk-fbsvc-ee61acb2b6.json'

# Test Firebase
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
    firebase_admin.initialize_app(cred)

db = firestore.client()
print("Firebase initialized successfully")