from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_superuser
from app.core.db import get_db
from app.crud.user import create_superuser, get_users
from app.schemas.user import UserCreate, User
from app.models.users import Users as UserModel

router = APIRouter(tags=["admin"])


@router.post("/admin/users", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_superuser(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """创建新的超级用户（仅限超级用户）"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="操作被拒绝：只有超级用户可以创建新的超级用户。",
        )

    try:
        return create_superuser(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/admin/initialize", response_model=User, status_code=status.HTTP_201_CREATED
)
def initialize_first_superuser(
    user_in: UserCreate,
    db: Session = Depends(get_db),
):
    """创建系统中的第一个超级用户（仅当系统中没有用户时可用）"""
    # 检查系统中是否已存在用户
    existing_users = get_users(db, skip=0, limit=1)
    if existing_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="初始化失败：系统中已存在用户，请使用正常的超级用户创建流程。",
        )

    try:
        return create_superuser(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
