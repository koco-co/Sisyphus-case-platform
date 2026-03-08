from app.worker.celery_app import celery_app


@celery_app.task(name="diff_tasks.placeholder")
def placeholder() -> dict:
    """TODO: implement diff_tasks"""
    return {"status": "not implemented"}
