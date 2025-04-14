import os
import shutil
import uuid
import logging
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
from app.models.users import Users as UserModel
from app.crud.files import (
    create_file,
    get_user_files,
    get_file,
    update_file,
    delete_file,
)
from app.schemas.files import File as FileSchema, FileCreate, FileUpdate

from app.utils.inovice_processor import InvoiceProcessor
from app.crud.invoice import create_invoice, get_invoice_by_file, get_user_invoices
from app.schemas.invoice import InvoiceCreate, Invoice as InvoiceSchema

from app.crud.invoice_item import create_invoice_item
from app.schemas.invoice_item import InvoiceItemCreate

router = APIRouter(prefix="/files", tags=["files"])

# 确保上传目录存在
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
# Configure logger
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=FileSchema, status_code=status.HTTP_201_CREATED)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

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

    files = get_user_files(db, current_user.id, skip=skip, limit=limit)
    return files


@router.get("/{file_id}", response_model=FileSchema)
async def read_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="can not find file")

    if file.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="have no permission to access this file"
        )

    return file


@router.delete("/{file_id}", response_model=FileSchema)
async def remove_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="can not find file")

    # check file ownership
    if file.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="no permission to access this file")

    # delete file from disk
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        logger.error(f"delete file  {file.file_path} get error: {str(e)}")

    # delete file record from database
    deleted_file = delete_file(db, file_id)
    return deleted_file


# inovce processor routes


# TODO: let invoice process separate from file upload
async def process_file_background(file_id: uuid.UUID, db: Session):

    file = get_file(db, file_id)
    if not file:
        return

    try:

        existing_invoice = get_invoice_by_file(db, file_id)
        if existing_invoice:
            logger.info(f"文件 {file_id} 的发票记录已存在，跳过处理")
            return

        processor = InvoiceProcessor(file.file_path)

        invoice_data = processor.process()

        items = invoice_data.pop("items", [])
        logger.info(f"从OCR中提取到 {len(items)} 个商品项目")

        invoice_create = InvoiceCreate(
            file_id=file_id,
            user_id=file.user_id,
            ocr_text=processor.extracted_text,
            is_processed=True,
            **{
                k: v
                for k, v in invoice_data.items()
                if k
                in [
                    "markt_name",
                    "store_address",
                    "brand",
                    "telephone",
                    "uid_number",
                    "markt_id",
                    "receipt_nr",
                    "document_nr",
                    "date",
                    "time",
                    "payment_method",
                    "total",
                ]
            },
        )

        invoice = create_invoice(db, invoice_create)
        logger.info(f"成功创建发票记录 ID: {invoice.id}")

        try:
            if not items:
                logger.warning("没有提取到任何商品项目")

            for idx, item_data in enumerate(items):
                try:
                    if "name" in item_data and "total_price" in item_data:
                        item_create = InvoiceItemCreate(
                            invoice_id=invoice.id,
                            name=item_data["name"],
                            quantity=item_data.get("quantity"),
                            unit_price=item_data.get("unit_price"),
                            total_price=item_data["total_price"],
                        )
                        create_invoice_item(db, item_create)
                        logger.info(f"成功创建商品项目 {idx+1}: {item_data['name']}")
                    else:
                        logger.warning(f"商品项目 {idx+1} 缺少必要字段: {item_data}")
                except Exception as e:
                    logger.error(f"创建商品项目 {idx+1} 时出错: {str(e)}")
        except Exception as e:
            logger.error(f"处理商品项目时出错: {str(e)}")

        # 更新文件状态为已处理
        update_file(db, file_id, FileUpdate(is_processed=True))

    except Exception as e:
        logger.error(f"处理文件 {file_id} 时出错: {str(e)}")
        # 如果发生错误，仍然将文件标记为已处理，但记录错误信息
        update_file(db, file_id, FileUpdate(is_processed=True))


# 添加新的API路由获取发票数据
@router.get("/{file_id}/invoice", response_model=InvoiceSchema)
async def get_file_invoice(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="file not found")

    if file.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="no permission to access this file")

    invoice = get_invoice_by_file(db, file_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="invoice not found")

    return invoice


@router.post("/{file_id}/process", response_model=FileSchema)
async def process_file(
    file_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    file = get_file(db, file_id)
    if not file:
        raise HTTPException(status_code=404, detail="file not found")

    if file.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="no permission to access this file")

    update_file(db, file_id, FileUpdate(is_processed=False))

    background_tasks.add_task(process_file_background, file_id, db)

    return file


@router.get("/invoices/me", response_model=List[InvoiceSchema])
async def read_user_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):

    invoices = get_user_invoices(db, current_user.id, skip=skip, limit=limit)
    return invoices
