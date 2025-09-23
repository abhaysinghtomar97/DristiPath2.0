# tracking_app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import BusLocation
try:
    from firebase_config import db as firestore_db
except ImportError:
    firestore_db = None
import traceback

@receiver(post_save, sender=BusLocation)
def push_bus_location_to_firestore(sender, instance: BusLocation, created, **kwargs):
    """
    Push the latest location to Firestore.
    - Document path: buses/{bus_id}
    - Field 'last_location' contains current snapshot
    - Optionally append to subcollection 'history'
    """
    try:
        if not firestore_db:
            return
        bus_doc_id = str(instance.bus.bus_id)
        # Prepare data
        data = {
            "latitude": float(instance.latitude),
            "longitude": float(instance.longitude),
            "speed": float(instance.speed or 0.0),
            "heading": float(instance.heading or 0.0),
            "last_updated": instance.last_updated.isoformat(),
            # optional: server timestamp too
            "server_ts": firestore_db._client._firestore_api._rpc.metadata if False else None
        }
        # Set last_location (merge so we keep other bus fields)
        firestore_db.collection("buses").document(bus_doc_id).set({
            "last_location": data,
            "bus_id": bus_doc_id
        }, merge=True)

        # Append to history with minimal write cost (optional)
        # You might want to throttle writes to 'history' to avoid reads/writes cost
        firestore_db.collection("buses").document(bus_doc_id).collection("history").add(data)
    except Exception:
        # Don't break Django on Firestore errors — log for debug
        import logging
        logging.getLogger("tracking_app").exception("Failed pushing BusLocation to Firestore: %s", traceback.format_exc())
