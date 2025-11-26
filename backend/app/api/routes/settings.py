"""
Settings API Routes
Handles HTTP endpoints for user settings
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.models.database import UserSettings
from app.models.schemas import UserSettingsResponse, UserSettingsUpdate
from app.config import settings as app_settings
from app.core.security import validate_download_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


def get_or_create_settings(db: Session) -> UserSettings:
    """Get or create user settings"""
    settings = db.query(UserSettings).first()
    if not settings:
        settings = UserSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("/", response_model=UserSettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """
    Get user settings
    """
    settings = get_or_create_settings(db)

    # If download_location is not set, use the default from config
    if not settings.download_location:
        settings.download_location = str(app_settings.DOWNLOAD_DIR)

    return settings


@router.patch("/", response_model=UserSettingsResponse)
async def update_settings(
    update: UserSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update user settings

    SECURITY: Validates download_location to prevent path traversal attacks
    """
    settings = get_or_create_settings(db)

    # Update only provided fields
    update_data = update.model_dump(exclude_unset=True)

    # SECURITY: Validate download_location if being updated
    if "download_location" in update_data and update_data["download_location"]:
        try:
            # Validate path to prevent path traversal
            validated_path = validate_download_path(update_data["download_location"])
            update_data["download_location"] = str(validated_path)
            logger.info(f"Download location updated to: {validated_path}")
        except ValueError as e:
            logger.warning(f"Invalid download location rejected: {update_data['download_location']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return settings
