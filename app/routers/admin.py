from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_superuser
from app.core.db import get_db
from app.crud.user import create_superuser
from app.schemas.user import UserCreate, User

router = APIRouter(tags=["admin"])


@router.post("/admin/users", response_model=User, status_code=status.HTTP_201_CREATED)
def create_new_superuser(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """创建新的超级用户（仅限超级用户）"""
    try:
        return create_superuser(db, user_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
