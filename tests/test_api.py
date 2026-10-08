import time

from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app


client = TestClient(app)


def wait_for_job(job_id: int, timeout: float = 5):
    """
    Wait until a background job finishes.
    """

    start = time.time()

    while time.time() - start < timeout:

        response = client.get(
            f"/jobs/{job_id}"
        )

        assert response.status_code == 200

        data = response.json()

        if data["status"] == "completed":
            return data

        time.sleep(0.1)

    raise AssertionError(
        "Job did not complete within timeout"
    )


def test_root():

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"


def test_create_generation_job():

    response = client.post(
        "/jobs",
        json={
            "event_name": "Test Workshop",
            "certificate_title": "Certificate of Completion",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "test@example.com"
                }
            ]
        }
    )

    assert response.status_code == 202

    data = response.json()

    assert data["total"] == 1


def test_invalid_email():

    response = client.post(
        "/jobs",
        json={
            "event_name": "Test Workshop",
            "certificate_title": "Certificate of Completion",
            "recipients": [
                {
                    "name": "Test User",
                    "email": "not-an-email"
                }
            ]
        }
    )

    assert response.status_code == 422


def test_empty_recipients():

    response = client.post(
        "/jobs",
        json={
            "event_name": "Test Workshop",
            "certificate_title": "Certificate of Completion",
            "recipients": []
        }
    )

    assert response.status_code == 422


def test_job_status_after_processing():

    response = client.post(
        "/jobs",
        json={
            "event_name": "Status Test",
            "certificate_title": "Certificate of Completion",
            "recipients": [
                {
                    "name": "Status User",
                    "email": "status@example.com"
                }
            ]
        }
    )

    assert response.status_code == 202

    job_id = response.json()["id"]

    data = wait_for_job(job_id)

    assert data["status"] == "completed"
    assert data["total"] == 1
    assert data["successful"] == 1
    assert data["failed"] == 0


def test_certificate_retrieval():

    response = client.post(
        "/jobs",
        json={
            "event_name": "Retrieval Test",
            "certificate_title": "Certificate of Completion",
            "recipients": [
                {
                    "name": "Download User",
                    "email": "download@example.com"
                }
            ]
        }
    )

    assert response.status_code == 202

    job_id = response.json()["id"]

    data = wait_for_job(job_id)

    certificate_id = data["certificates"][0]["id"]

    response = client.get(
        f"/certificates/{certificate_id}"
    )

    assert response.status_code == 200

    assert response.headers["content-type"] == "application/pdf"


def test_individual_certificate_failure(
    monkeypatch
):

    original_generator = main_module.generate_certificate

    def mock_generator(
        recipient_name,
        event_name,
        certificate_title,
        certificate_id
    ):

        if recipient_name == "Fail User":
            raise RuntimeError(
                "Simulated certificate generation failure"
            )

        return original_generator(
            recipient_name,
            event_name,
            certificate_title,
            certificate_id
        )

    monkeypatch.setattr(
        main_module,
        "generate_certificate",
        mock_generator
    )

    response = client.post(
        "/jobs",
        json={
            "event_name": "Failure Test",
            "certificate_title": "Certificate of Completion",
            "recipients": [
                {
                    "name": "Success User",
                    "email": "success@example.com"
                },
                {
                    "name": "Fail User",
                    "email": "fail@example.com"
                },
                {
                    "name": "Another Success",
                    "email": "another@example.com"
                }
            ]
        }
    )

    assert response.status_code == 202

    job_id = response.json()["id"]

    data = wait_for_job(job_id)

    assert data["status"] == "completed"
    assert data["total"] == 3
    assert data["successful"] == 2
    assert data["failed"] == 1

    failed_certificates = [
        certificate
        for certificate in data["certificates"]
        if certificate["status"] == "failed"
    ]

    assert len(failed_certificates) == 1

    assert (
        failed_certificates[0]["error_message"]
        == "Simulated certificate generation failure"
    )