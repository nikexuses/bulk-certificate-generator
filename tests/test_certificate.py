from pathlib import Path

from app.certificate import generate_certificate


def test_certificate_generation():

    file_path = generate_certificate(
        recipient_name="Test User",
        event_name="Test Event",
        certificate_title="Certificate of Completion",
        certificate_id=9999
    )

    path = Path(file_path)

    assert path.exists()
    assert path.suffix == ".pdf"

    path.unlink()