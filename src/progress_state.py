current_progress = {
    "status": "idle",
    "current_batch": 0,
    "total_batches": 0,
    "message": ""
}

def update_progress(status: str, current_batch: int, total_batches: int, message: str):
    global current_progress
    current_progress["status"] = status
    current_progress["current_batch"] = current_batch
    current_progress["total_batches"] = total_batches
    current_progress["message"] = message