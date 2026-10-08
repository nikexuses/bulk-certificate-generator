from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
from datetime import datetime

from .database import Base, engine, get_db
from .models import GenerationJob, Certificate
from .schemas import GenerationJobCreate, JobResponse
from .certificate import generate_certificate


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator",
    description="API for generating certificates in bulk",
    version="1.0.0"
)


def process_job(job_id: int):
    db = next(get_db())

    try:
        job = db.query(GenerationJob).filter(
            GenerationJob.id == job_id
        ).first()

        if not job:
            return

        job.status = "processing"
        db.commit()

        certificates = db.query(Certificate).filter(
            Certificate.job_id == job_id
        ).all()

        for certificate in certificates:

            try:
                file_path = generate_certificate(
                    recipient_name=certificate.recipient_name,
                    event_name=job.event_name,
                    certificate_title=job.certificate_title,
                    certificate_id=certificate.id
                )

                certificate.status = "completed"
                certificate.file_path = file_path

                job.successful += 1

            except Exception as error:

                certificate.status = "failed"
                certificate.error_message = str(error)

                job.failed += 1

            db.commit()

        job.status = "completed"
        job.completed_at = datetime.utcnow()

        db.commit()

    finally:
        db.close()


@app.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API",
        "status": "running"
    }


@app.post(
    "/jobs",
    response_model=JobResponse,
    status_code=202
)
def create_generation_job(
    request: GenerationJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):

    job = GenerationJob(
        event_name=request.event_name,
        certificate_title=request.certificate_title,
        total=len(request.recipients),
        status="pending"
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    for recipient in request.recipients:

        certificate = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=recipient.email,
            status="pending"
        )

        db.add(certificate)

    db.commit()

    background_tasks.add_task(
        process_job,
        job.id
    )

    return job


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db)
):

    job = db.query(GenerationJob).filter(
        GenerationJob.id == job_id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    return job


@app.get("/certificates/{certificate_id}")
def get_certificate(
    certificate_id: int,
    db: Session = Depends(get_db)
):

    certificate = db.query(Certificate).filter(
        Certificate.id == certificate_id
    ).first()

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found"
        )

    if certificate.status != "completed":
        raise HTTPException(
            status_code=404,
            detail="Certificate is not available"
        )

    file_path = Path(certificate.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Certificate file not found"
        )

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=file_path.name
    )