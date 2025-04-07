import os
import shutil
import uuid
from typing import List
from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
    status,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from app.auth import get_current_active_user

from app.core.db import get_db
from app.models.user import User as UserModel
from app.crud.files import (
    create_file,
    get_user_files,
    get_file,
    update_file,
    delete_file,
)
from app.schemas.files import File as FileSchema, FileCreate, FileUpdate

router = APIRouter(prefix="/files", tags=["files"])

# 确保上传目录存在
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def process_file_background(file_id: uuid.UUID, db: Session):
    """后台处理文件的示例函数"""
    file = get_file(db, file_id)
    if file:

        update_file(db, file_id, FileUpdate(is_processed=True))


@router.post("/upload", response_model=FileSchema, status_code=status.HTTP_201_CREATED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """上传新文件"""
    # 验证文件类型
    if file.content_type not in ["application/pdf", "image/jpeg", "image/png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="只支持PDF和图片文件"
        )

    # 创建唯一文件名
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_location = os.path.join(UPLOAD_DIR, unique_filename)

    # 保存文件
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"无法保存文件: {str(e)}",
        )
    finally:
        file.file.close()

    # 获取文件大小
    file_size = os.path.getsize(file_location)

    # 创建文件记录
    file_data = FileCreate(
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_location,
        file_size=file_size,
        file_type=file.content_type,
        user_id=current_user.id,
    )

    db_file = create_file(db, file_data)

    # 添加后台任务处理文件
    background_tasks.add_task(process_file_background, db_file.id, db)

    return db_file


@router.get("/me", response_model=List[FileSchema])
async def read_user_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """获取当前用户的所有文件"""
    files = get_user_files(db, current_user.id, skip=skip, limit=limit)
    return files


@router.get("/{file_id}", response_model=FileSchema)
async def read_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """获取特定文件详情"""
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="文件未找到")

    # 检查文件所有权
    if file.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="没有权限访问此文件")

    return file


@router.delete("/{file_id}", response_model=FileSchema)
async def remove_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """删除文件"""
    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="文件未找到")

    # 检查文件所有权
    if file.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="没有权限删除此文件")

    # 删除物理文件
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        # 记录错误但继续删除数据库记录
        print(f"删除文件时出错: {str(e)}")

    # 删除数据库记录
    deleted_file = delete_file(db, file_id)
    return deleted_file
