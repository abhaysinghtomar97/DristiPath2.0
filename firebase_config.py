# firebase_config.py
import os
import json
import base64
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, rely on system environment variables
    pass

def _init_firebase():
    """
    Initialize Firebase app (idempotent) and return Firestore, Storage, and Auth.
    Supports multiple credential sources:
    1. FIREBASE_SA_JSON_B64 (base64-encoded JSON)
    2. FIREBASE_SA_JSON (raw JSON string or file path)
    3. GOOGLE_APPLICATION_CREDENTIALS (file path)
    4. Application Default Credentials (fallback)
    """
    if firebase_admin._apps:
        # Already initialized
        db = firestore.client()
        try:
            bucket = storage.bucket()
        except Exception:
            bucket = None
        return db, bucket, auth

    # Try base64 JSON first
    sa_b64 = os.environ.get("FIREBASE_SA_JSON_B64")
    sa_json_raw = os.environ.get("FIREBASE_SA_JSON")
    gcred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    cred = None
    if sa_b64:
        try:
            sa_json = base64.b64decode(sa_b64).decode()
            cred = credentials.Certificate(json.loads(sa_json))
        except Exception as e:
            raise RuntimeError("Invalid FIREBASE_SA_JSON_B64") from e
    elif sa_json_raw:
        try:
            cred = credentials.Certificate(json.loads(sa_json_raw))
        except Exception:
            # fallback to file path
            if os.path.exists(sa_json_raw):
                cred = credentials.Certificate(sa_json_raw)
            else:
                raise RuntimeError("FIREBASE_SA_JSON provided but invalid")
    elif gcred_path and os.path.exists(gcred_path):
        cred = credentials.Certificate(gcred_path)
    else:
        # Fallback: Application Default Credentials
        cred = credentials.ApplicationDefault()

    # Optional storage bucket
    storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")

    if storage_bucket:
        firebase_admin.initialize_app(cred, {"storageBucket": storage_bucket})
    else:
        firebase_admin.initialize_app(cred)

    # Firestore client
    db = firestore.client()

    # Storage bucket
    bucket = None
    try:
        bucket = storage.bucket()
    except Exception:
        bucket = None

    return db, bucket, auth

# Initialize Firebase and export
db, bucket, firebase_auth = _init_firebase()
