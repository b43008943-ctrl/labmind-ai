"""
LabMind AI — Case Asset API Routes (File Upload)
With MIME type validation and content-type enforcement.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_client_ip, get_current_user, require_role
from app.core.constants import AssetType, UserRole
from app.core.exceptions import PayloadTooLargeException, ValidationException
from app.db.database import get_db
from app.db.models.user import User
from app.providers.storage_provider_local import LocalStorageProvider
from app.schemas.asset import AssetListItem, AssetUploadResponse
from app.schemas.common import MessageResponse
from app.services.asset_service import AssetService

router = APIRouter(tags=["Case Assets"])

# ── Upload safety constants ──
MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/bmp",
    "image/webp",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}


def _get_storage() -> LocalStorageProvider:
    return LocalStorageProvider(root_dir="uploads")


def _validate_upload(filename: str, content_type: str | None, file_data: bytes) -> None:
    """Validate file size, MIME type, and extension before accepting the upload."""
    # Size check
    if len(file_data) > MAX_UPLOAD_BYTES:
        raise PayloadTooLargeException(
            detail=f"File too large ({len(file_data) / 1024 / 1024:.1f} MB). Maximum size is 20 MB."
        )

    # MIME type check
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationException(
            detail=f"Unsupported file type '{content_type}'. "
                   f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}"
        )

    # Extension check
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(
            detail=f"Unsupported file extension '{ext}'. "
                   f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )


@router.post(
    "/api/cases/{case_id}/assets",
    response_model=AssetUploadResponse,
    status_code=201,
)
async def upload_asset(
    case_id: UUID,
    request: Request,
    file: UploadFile = File(...),
    asset_type: AssetType = Form(AssetType.BLOOD_SMEAR),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ip = get_client_ip(request)

    # Validate case exists before accepting upload
    from app.services.case_service import CaseService
    CaseService(db).get(case_id)  # raises 404 if missing

    file_data = await file.read()
    filename = file.filename or "upload.bin"

    # Validate upload safety (size, MIME, extension)
    _validate_upload(filename, file.content_type, file_data)

    storage = _get_storage()
    service = AssetService(db, storage)

    return service.upload(
        case_id=case_id,
        user_id=current_user.id,
        filename=filename,
        file_data=file_data,
        content_type=file.content_type,
        asset_type=asset_type,
        ip=ip,
    )


@router.get("/api/cases/{case_id}/assets", response_model=list[AssetListItem])
def list_assets(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    storage = _get_storage()
    service = AssetService(db, storage)
    return service.list_by_case(case_id)


@router.get("/api/assets/{asset_id}/download")
def download_asset(
    asset_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    storage = _get_storage()
    service = AssetService(db, storage)
    data, asset = service.download(asset_id)
    return Response(
        content=data,
        media_type=asset.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{asset.original_filename}"'},
    )


@router.delete("/api/assets/{asset_id}", response_model=MessageResponse)
def delete_asset(
    asset_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    ip = get_client_ip(request)
    storage = _get_storage()
    service = AssetService(db, storage)
    service.delete(asset_id, user_id=current_user.id, ip=ip)
    return MessageResponse(message="Asset deleted successfully.")
