from app.worker.celery_app import celery_app


@celery_app.task(name="parse_tasks.placeholder")
def placeholder() -> dict:
    """TODO: implement parse_tasks"""
    return {"status": "not implemented"}
