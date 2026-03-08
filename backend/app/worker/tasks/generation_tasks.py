from app.worker.celery_app import celery_app


@celery_app.task(name="generation_tasks.placeholder")
def placeholder() -> dict:
    """TODO: implement generation_tasks"""
    return {"status": "not implemented"}
