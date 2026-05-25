from .base_consumer import BaseConsumer
from ..handlers.sync_handler import sync_handler

SYNC_ROUTING = {
    "sync.patient.created": sync_handler.handle_patient_sync,
    "sync.patient.updated": sync_handler.handle_patient_sync,
    "sync.clinical.encounter": sync_handler.handle_clinical_sync,
    "sync.clinical.observation": sync_handler.handle_clinical_sync,
    "sync.clinical.condition": sync_handler.handle_clinical_sync,
}


def create_sync_consumer(queue_name: str) -> BaseConsumer:
    handler = sync_handler.handle_health_check

    return BaseConsumer(
        queue_name=queue_name,
        handler=handler,
        max_retries=3,
        prefetch_count=5,
    )


sync_patient_consumer = create_sync_consumer("sync.patient.queue")
sync_clinical_consumer = create_sync_consumer("sync.clinical.queue")
sync_all_consumer = create_sync_consumer("sync.all.queue")
