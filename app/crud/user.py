from typing import List, Optional, Union, Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.password import get_password_hash
from app.crud.invitation import get_invitation_by_code, mark_invitation_as_used


def get_user(db: Session, user_id: uuid.UUID) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:

    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:

    return db.query(User).filter(User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:

    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate) -> User:
    invitation = get_invitation_by_code(db, user_in.invitation_code)
    if not invitation:
        raise ValueError("Invalid invitation code")

    if invitation.is_used:
        raise ValueError("Invitation code has already been used")

    # 如果邀请码指定了email，验证是否匹配
    if invitation.email and invitation.email != user_in.email:
        raise ValueError("Invitation code was issued for a different email address")

    # Check if username already exists
    if get_user_by_username(db, username=user_in.username):
        raise ValueError("Username already registered")

    # Check if email already exists
    if get_user_by_email(db, email=user_in.email):
        raise ValueError("Email already registered")

    hashed_password = get_password_hash(user_in.password)

    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        bio=user_in.bio,
        avatar_url=user_in.avatar_url,
        is_active=user_in.is_active,
        is_superuser=user_in.is_superuser,
        is_verified=user_in.is_verified,
        invitation_id=invitation.id,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    invitation.is_used = True
    invitation.used_at = datetime.now(datetime.timezone.utc)
    db.add(invitation)
    db.commit()
    return db_user


def update_user(
    db: Session, user_id: uuid.UUID, user_in: Union[UserUpdate, Dict[str, Any]]
) -> User:

    user = get_user(db, user_id)
    if not user:
        raise ValueError("User not found")

    if isinstance(user_in, dict):
        update_data = user_in
    else:
        update_data = user_in.dict(exclude_unset=True)

    if "password" in update_data and update_data["password"]:
        hashed_password = get_password_hash(update_data["password"])
        del update_data["password"]
        update_data["hashed_password"] = hashed_password

    for field, value in update_data.items():
        if hasattr(user, field) and value is not None:
            setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: uuid.UUID) -> User:

    user = get_user(db, user_id)
    if not user:
        raise ValueError("User not found")

    db.delete(user)
    db.commit()
    return user


def create_superuser(db: Session, user_in: UserCreate):
    """创建超级用户，跳过邀请码检查"""
    # 检查用户名和邮箱是否已存在
    if get_user_by_username(db, username=user_in.username):
        raise ValueError("Username already registered")
    if get_user_by_email(db, email=user_in.email):
        raise ValueError("Email already registered")

    # 创建超级用户
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_password,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_active=True,
        is_superuser=True,  # 设置为超级用户
        is_verified=True,  # 自动验证
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_superuser(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """获取超级用户"""
    return db.query(User).filter(User.id == user_id, User.is_superuser == True).first()
