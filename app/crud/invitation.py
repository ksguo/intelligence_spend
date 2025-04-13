import secrets
import string
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.invitation import Invitation
from app.schemas.invitation import InvitationCreate


def generate_invitation_code(length: int = 10) -> str:
    """Generate a random invitation code"""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_invitation(
    db: Session, obj_in: Optional[InvitationCreate] = None
) -> Invitation:
    """Create a new invitation"""
    if not obj_in:
        # Generate a random code if not provided
        code = generate_invitation_code()
        db_obj = Invitation(code=code)
    else:
        db_obj = Invitation(code=obj_in.code, email=obj_in.email)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_invitation_by_code(db: Session, code: str) -> Optional[Invitation]:
    """Get invitation by code"""
    return db.query(Invitation).filter(Invitation.code == code).first()


def mark_invitation_as_used(
    db: Session, invitation: Invitation, user_id: UUID
) -> Invitation:
    """Mark invitation as used"""
    invitation.is_used = True
    invitation.used_at = datetime.timezone()
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_all_invitations(
    db: Session, skip: int = 0, limit: int = 100
) -> List[Invitation]:
    """Get all invitations"""
    return db.query(Invitation).offset(skip).limit(limit).all()
