import pytest
from datetime import datetime
from log_processor import parse_log_line, process_logs
import tempfile
from pathlib import Path
import os

# ====================== TESTS FOR parse_log_line ======================

def test_parse_log_line_valid():
    line = "2026-03-18 10:15:23 | ERROR | service_b | Timeout occurred"
    result = parse_log_line(line)
    assert result is not None
    assert result["level"] == "ERROR"
    assert result["service"] == "service_b"
    assert result["message"] == "Timeout occurred"
    assert isinstance(result["timestamp"], datetime)

def test_parse_log_line_malformed_wrong_parts():
    line = "2026-03-18 10:15:23 | ERROR | service_b"   # only 3 parts
    assert parse_log_line(line) is None

def test_parse_log_line_empty():
    assert parse_log_line("") is None
    assert parse_log_line("   ") is None

def test_parse_log_line_bad_timestamp():
    line = "2026-99-99 10:15:23 | INFO | service_a | hello"
    assert parse_log_line(line) is None

def test_parse_log_line_extra_spaces():
    line = "  2026-03-18 10:15:23  |  INFO  |  service_a  |  Request done  "
    result = parse_log_line(line)
    assert result is not None
    assert result["level"] == "INFO"

# ====================== TESTS FOR process_logs ======================

def test_process_logs_with_sample_data():
    # Create temporary log file with known data
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = Path(tmp_dir) / "test.log"
        log_file.write_text(
            "2026-03-18 10:00:01 | INFO | service_a | ok\n"
            "2026-03-18 10:02:30 | ERROR | service_b | Timeout occurred\n"
            "2026-03-18 10:02:45 | ERROR | service_b | Timeout occurred\n"
            "2026-03-18 10:03:00 | ERROR | service_a | Database failed\n"
            "2026-03-18 10:06:00 | WARN | service_a | retry\n"
        )

        result = process_logs(str(tmp_dir), threshold=2)

        assert result["summary"]["total_logs"] == 5
        assert result["summary"]["levels"]["ERROR"] == 3
        assert result["summary"]["services"]["service_b"] == 2

        # Top errors
        assert result["top_errors"][0]["message"] == "Timeout occurred"
        assert result["top_errors"][0]["count"] == 2

        # Anomaly (3 errors between 10:00-10:05)
        assert len(result["anomalies"]) == 1
        assert result["anomalies"][0]["error_count"] == 3
        assert result["anomalies"][0]["window_start"] == "2026-03-18 10:00:00"

def test_process_logs_no_errors():
    with tempfile.TemporaryDirectory() as tmp_dir:
        log_file = Path(tmp_dir) / "noerror.log"
        log_file.write_text("2026-03-18 10:00:01 | INFO | service_a | ok\n")

        result = process_logs(str(tmp_dir), threshold=10)
        assert result["summary"]["levels"].get("ERROR", 0) == 0
        assert len(result["anomalies"]) == 0
        assert len(result["top_errors"]) == 0

def test_process_logs_empty_directory():
    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(ValueError):
            process_logs(str(tmp_dir))   # no .log files

# ====================== Run tests command ======================
# Run with: pytest test_log_processor.py -v