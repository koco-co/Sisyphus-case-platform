from app.worker.celery_app import celery_app


@celery_app.task(name="diagnosis_tasks.placeholder")
def placeholder() -> dict:
    """TODO: implement diagnosis_tasks"""
    return {"status": "not implemented"}
