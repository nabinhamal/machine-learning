import time
from .celery_app import celery_app

@celery_app.task(name="app.tasks.process_data")
def process_data(data):
    """
    Sample background task that simulates heavy processing.
    """
    print(f"Starting heavy processing for: {data}")
    time.sleep(10)  # Simulate long-running task
    print(f"Finished processing for: {data}")
    return {"status": "completed", "result": f"Processed {data}"}
