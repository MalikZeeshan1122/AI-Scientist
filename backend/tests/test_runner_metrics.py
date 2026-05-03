from ai_scientist.experiments.runner import _parse_metrics


def test_parse_metrics_extracts_block():
    stdout = (
        "some logs\n"
        "===METRICS_START===\n"
        '{"accuracy": 0.91, "loss": 0.12, "ignored": "abc"}\n'
        "===METRICS_END===\n"
        "more logs\n"
    )
    m = _parse_metrics(stdout)
    assert m == {"accuracy": 0.91, "loss": 0.12}


def test_parse_metrics_missing_block_returns_empty():
    assert _parse_metrics("nothing here") == {}


def test_parse_metrics_invalid_json():
    stdout = "===METRICS_START===\nnot-json\n===METRICS_END==="
    assert _parse_metrics(stdout) == {}
