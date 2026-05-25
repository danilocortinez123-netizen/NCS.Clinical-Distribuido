from .base_consumer import BaseConsumer
from ..handlers.patient_handler import patient_handler

# Mapping de routing_key → handler method
PATIENT_ROUTING = {
    "patient.created": patient_handler.handle_created,
    "patient.updated": patient_handler.handle_updated,
}


def create_patient_consumer(queue_name: str) -> BaseConsumer:
    routing_key = queue_name.replace(".queue", "")
    handler = PATIENT_ROUTING.get(routing_key)

    if handler is None:
        handler = patient_handler.handle_sync

    return BaseConsumer(
        queue_name=queue_name,
        handler=handler,
        max_retries=3,
        prefetch_count=10,
    )


patient_created_consumer = create_patient_consumer("patient.created.queue")
patient_updated_consumer = create_patient_consumer("patient.updated.queue")
patient_all_consumer = create_patient_consumer("patient.all.queue")
