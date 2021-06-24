import logging

from mock import patch

from pushsource._impl.backend.errata_source import errata_client


def test_errata_client_info_logs(caplog):
    """Errata client logs one INFO message per advisory queried."""

    caplog.set_level(logging.INFO)

    client = errata_client.ErrataClient(threads=1, url="https://errata.example.com/")

    with patch(
        "pushsource._impl.backend.errata_source.errata_client.xmlrpc_client.ServerProxy"
    ) as mock_proxy:
        client.get_raw_f("advisory-1").result()
        client.get_raw_f("advisory-2").result()

    assert caplog.messages == [
        "Queried Errata Tool for advisory-1",
        "Queried Errata Tool for advisory-2",
    ]


def test_errata_client_debug_logs(caplog):
    """Errata client logs detailed DEBUG messages around each method call."""

    caplog.set_level(logging.DEBUG)

    client = errata_client.ErrataClient(
        threads=1,
        url="https://errata.example.com/",
        # disable retry just for this test
        max_attempts=1,
    )

    with patch(
        "pushsource._impl.backend.errata_source.errata_client.xmlrpc_client.ServerProxy"
    ) as mock_proxy:
        # make this one fail on the second try
        mock_proxy.return_value.get_advisory_cdn_file_list.side_effect = [
            {},
            ValueError("oops, something went wrong"),
        ]

        client.get_raw_f("advisory-1").result()
        client.get_raw_f("advisory-2").exception()

    # Locate structed log records with ET events
    logs = [
        log
        for log in caplog.records
        if getattr(log, "event", {}).get("type", "").startswith("errata-tool-")
    ]

    # We are not going to check every single one of them, but sample a few
    # events we expect to exist.

    expected_events = [
        # A successful call
        {
            "type": "errata-tool-call-start",
            "method": "get_advisory_cdn_metadata",
            "advisory": "advisory-1",
        },
        {
            "type": "errata-tool-call-end",
            "method": "get_advisory_cdn_metadata",
            "advisory": "advisory-1",
        },
        # Unsuccessful
        {
            "type": "errata-tool-call-start",
            "method": "get_advisory_cdn_file_list",
            "advisory": "advisory-2",
        },
        {
            "type": "errata-tool-call-fail",
            "method": "get_advisory_cdn_file_list",
            "advisory": "advisory-2",
        },
    ]

    for event in expected_events:
        assert [log for log in logs if log.event == event]
