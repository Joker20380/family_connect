from scripts import correlate_restricted as diagnostic


def test_boundary_privacy_bounds_and_unknown_attempt():
    source = {"dropped": 3, "events": [
        {"index": index, "at_ms": 1, "stage": "rtp_received", "result": "ok",
         "direction": "rx", "frame_known": True, "timestamp": 42,
         "payload": "PRIVATE KEY secret", "url": "https://secret"}
        for index in range(1, 101)
    ]}
    safe = diagnostic.boundaries(source)
    assert len(safe["events"]) == 64
    assert safe["projection_dropped"] == 36
    assert safe["dropped"] == 3
    assert "secret" not in str(safe)
    assert all("attempt" not in item and "attempt_known" not in item for item in safe["events"])
    assert diagnostic.delivery({"boundaries": source})["boundaries"] == safe


def test_boundary_rejects_untrusted_enums_and_numbers():
    for field, value in [("stage", "https://secret"), ("result", "PRIVATE KEY"),
                         ("attempt", 33), ("first_rtp", 65536), ("at_ms", True),
                         ("timestamp", 2**32), ("data_known", "true")]:
        point = {"index": 1, "at_ms": 1, "stage": "reliable_send", "result": "ok", "direction": "tx"}
        point[field] = value
        assert diagnostic.boundaries({"dropped": 0, "events": [point]})["events"] == []
