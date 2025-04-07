from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, Field


class FileBase(BaseModel):

    filename: str
    original_filename: str
    file_size: int
    file_type: str


class FileCreate(FileBase):

    file_path: str
    user_id: uuid.UUID
    is_active: bool = True
    is_processed: bool = False


class FileUpdate(BaseModel):

    is_active: Optional[bool] = None
    is_processed: Optional[bool] = None


class FileInDBBase(FileBase):

    id: uuid.UUID
    file_path: str
    user_id: uuid.UUID
    is_active: bool
    is_processed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class File(FileInDBBase):
    pass


class FileInDB(FileInDBBase):

    pass
