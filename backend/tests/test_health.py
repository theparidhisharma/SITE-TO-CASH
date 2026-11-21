"""Smoke tests verifying the Phase 1 backend skeleton and local storage."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_reports_local_storage_and_never_leaks_secret(
    monkeypatch, tmp_path: Path
) -> None:
    secret_sentinel = "dummy-test-key-never-expose"
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("GEMINI_API_KEY", secret_sentinel)

    client = TestClient(create_app())
    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["app"] == "Site-to-Cash"
    assert payload["storage_backend"] == "local"
    assert payload["storage_ready"] is True
    assert payload["gemini_configured"] is True
    assert secret_sentinel not in response.text


def test_empty_documents_and_cases_repositories(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    client = TestClient(create_app())

    docs_resp = client.get("/api/documents")
    assert docs_resp.status_code == 200
    assert docs_resp.json() == []

    cases_resp = client.get("/api/cases")
    assert cases_resp.status_code == 200
    assert cases_resp.json() == []


def test_empty_dashboard_and_missing_case_report_return_expected_responses(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    client = TestClient(create_app())

    metrics_resp = client.get("/api/dashboard/metrics")
    assert metrics_resp.status_code == 200
    metrics = metrics_resp.json()
    assert metrics["total_cases"] == 0
    assert metrics["contains_demo_data"] is False
    assert metrics["amounts_by_currency"] == []
    assert metrics["status_counts"] == {
        "detected": 0,
        "under_review": 0,
        "drafted": 0,
        "submitted": 0,
        "approved": 0,
        "rejected": 0,
        "executed": 0,
        "billed": 0,
        "paid": 0,
    }

    missing_report = client.post(
        "/api/cases/nonexistent-case/report",
        json={"prepared_by": "QS Reviewer"},
    )
    assert missing_report.status_code == 404

def test_vercel_uses_writable_ephemeral_data_directory(monkeypatch) -> None:
    from app.config import get_settings

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("LOCAL_DATA_DIR", raising=False)

    assert get_settings().local_data_dir == Path("/tmp/site-to-cash")


def test_local_data_dir_environment_override_is_respected(monkeypatch, tmp_path: Path) -> None:
    from app.config import get_settings

    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("LOCAL_DATA_DIR", str(tmp_path))

    assert get_settings().local_data_dir == tmp_path

