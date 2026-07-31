from app.pipeline_store import PipelineStore


def test_pipeline_store_success_lifecycle():
    store = PipelineStore()
    store.begin()
    store.update_progress("market", "Market research", "start")

    running = store.snapshot()
    assert running["running"] is True
    assert running["progress"]["market"]["phase"] == "start"

    result = {"score": 8.1}
    store.finish_success(result)
    completed = store.snapshot()
    assert completed["running"] is False
    assert completed["show_results"] is True
    assert completed["result"] == result


def test_pipeline_store_cancel_and_error_lifecycle():
    store = PipelineStore()
    store.begin()
    store.request_cancel()
    assert store.is_cancel_requested() is True

    store.finish_cancelled("Stopped")
    cancelled = store.snapshot()
    assert cancelled["error"] == "Stopped"
    assert cancelled["cancel_requested"] is False

    store.begin()
    store.finish_error("Failed")
    failed = store.snapshot()
    assert failed["running"] is False
    assert failed["error"] == "Failed"

