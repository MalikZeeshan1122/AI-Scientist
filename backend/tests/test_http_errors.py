from ai_scientist.api.http_errors import runtime_error_status_and_headers


def test_maps_openai_rpm_message_without_digit_429_to_503():
    """Vendor bodies sometimes omit the literal substring ``429`` in the outer message."""
    msg = (
        'Rate limit: Limit 3 requests per min — '
        '{"code":"rate_limit_exceeded"}'
    )
    status, headers = runtime_error_status_and_headers(msg)
    assert status == 503
    assert headers.get("Retry-After") == "60"


def test_unrelated_runtime_error_stays_500():
    status, headers = runtime_error_status_and_headers("Something broke in the pipeline")
    assert status == 500
    assert headers == {}
