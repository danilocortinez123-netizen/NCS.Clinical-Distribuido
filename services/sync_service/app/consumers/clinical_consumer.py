from .base_consumer import BaseConsumer
from ..handlers.clinical_handler import clinical_handler

CLINICAL_ROUTING = {
    "encounter.created": clinical_handler.handle_encounter_created,
    "observation.created": clinical_handler.handle_observation_created,
    "condition.created": clinical_handler.handle_condition_created,
}


def create_clinical_consumer(queue_name: str) -> BaseConsumer:
    routing_key = queue_name.replace(".queue", "")
    handler = CLINICAL_ROUTING.get(routing_key)

    if handler is None:
        handler = clinical_handler.handle_sync

    return BaseConsumer(
        queue_name=queue_name,
        handler=handler,
        max_retries=3,
        prefetch_count=10,
    )


encounter_consumer = create_clinical_consumer("encounter.created.queue")
observation_consumer = create_clinical_consumer("observation.created.queue")
condition_consumer = create_clinical_consumer("condition.created.queue")
clinical_all_consumer = create_clinical_consumer("clinical.all.queue")
