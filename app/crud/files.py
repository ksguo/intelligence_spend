from typing import List, Optional
import uuid
from sqlalchemy.orm import Session

from app.models.files import File
from app.schemas.files import FileCreate, FileUpdate


def get_file(db: Session, file_id: uuid.UUID) -> Optional[File]:
    return db.query(File).filter(File.id == file_id).first()


def get_user_files(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> List[File]:
    return (
        db.query(File).filter(File.user_id == user_id).offset(skip).limit(limit).all()
    )


def create_file(db: Session, file_in: FileCreate) -> File:
    db_file = File(
        filename=file_in.filename,
        original_filename=file_in.original_filename,
        file_path=file_in.file_path,
        file_size=file_in.file_size,
        file_type=file_in.file_type,
        user_id=file_in.user_id,
        is_active=file_in.is_active,
        is_processed=file_in.is_processed,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def update_file(db: Session, file_id: uuid.UUID, file_in: FileUpdate) -> Optional[File]:

    db_file = get_file(db, file_id)
    if not db_file:
        return None

    update_data = file_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(db_file, field) and value is not None:
            setattr(db_file, field, value)

    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file


def delete_file(db: Session, file_id: uuid.UUID) -> Optional[File]:
    db_file = get_file(db, file_id)
    if not db_file:
        return None

    db.delete(db_file)
    db.commit()
    return db_file
