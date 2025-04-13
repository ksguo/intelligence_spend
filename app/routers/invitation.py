from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_active_superuser
from app.core.db import get_db
from app.crud.invitation import (
    create_invitation,
    get_all_invitations,
    get_invitation_by_code,
)
from app.schemas.invitation import Invitation, InvitationCreate

router = APIRouter(tags=["invitations"])


@router.post(
    "/invitations", response_model=Invitation, status_code=status.HTTP_201_CREATED
)
def create_new_invitation(
    invitation_in: InvitationCreate = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """Create a new invitation code (admin only)"""
    return create_invitation(db, invitation_in)


@router.get("/invitations", response_model=List[Invitation])
def read_invitations(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_superuser),
):
    """Get all invitation codes (admin only)"""
    return get_all_invitations(db, skip=skip, limit=limit)


@router.post(
    "/invitations/generate",
    response_model=Invitation,
    status_code=status.HTTP_201_CREATED,
)
def generate_invitation(
    db: Session = Depends(get_db), current_user=Depends(get_current_active_superuser)
):
    """Generate a random invitation code (admin only)"""
    return create_invitation(db)


@router.get("/invitations/{code}/validate", response_model=dict)
def validate_invitation_code(
    code: str,
    db: Session = Depends(get_db),
):
    """Validate an invitation code"""
    invitation = get_invitation_by_code(db, code)
    if invitation and not invitation.is_used:  # 修改 used 为 is_used
        return {"valid": True}
    return {"valid": False}
