"""
LabMind AI — Asset Service
Handles file uploads via the storage provider and audit logging.
"""

import hashlib
import uuid

from sqlalchemy.orm import Session

from app.core.constants import AssetType, AuditAction
from app.core.exceptions import NotFoundException
from app.db.models.case_asset import CaseAsset
from app.providers.storage_provider import StorageProvider
from app.repositories.asset_repository import AssetRepository
from app.services.audit_service import AuditService


class AssetService:
    def __init__(self, db: Session, storage: StorageProvider):
        self.repo = AssetRepository(db)
        self.storage = storage
        self.audit = AuditService(db)

    def upload(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        filename: str,
        file_data: bytes,
        content_type: str | None,
        asset_type: AssetType = AssetType.BLOOD_SMEAR,
        ip: str | None = None,
    ) -> CaseAsset:
        # Generate unique storage key
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        storage_key = f"cases/{case_id}/{uuid.uuid4().hex}.{ext}"

        # Compute checksum
        checksum = hashlib.sha256(file_data).hexdigest()

        # Store file
        self.storage.upload(storage_key, file_data, content_type)

        # Create DB record
        asset = CaseAsset(
            case_id=case_id,
            uploaded_by=user_id,
            asset_type=asset_type,
            original_filename=filename,
            storage_key=storage_key,
            file_size_bytes=len(file_data),
            mime_type=content_type,
            checksum_sha256=checksum,
        )
        created = self.repo.create(asset)

        self.audit.log(
            action=AuditAction.ASSET_UPLOADED,
            user_id=user_id,
            entity_type="case_asset",
            entity_id=created.id,
            details={
                "case_id": str(case_id),
                "filename": filename,
                "size_bytes": len(file_data),
            },
            ip_address=ip,
        )
        return created

    def list_by_case(self, case_id: uuid.UUID) -> list[CaseAsset]:
        return self.repo.list_by_case(case_id)

    def get(self, asset_id: uuid.UUID) -> CaseAsset:
        asset = self.repo.get_by_id(asset_id)
        if not asset:
            raise NotFoundException(detail="Asset not found.")
        return asset

    def download(self, asset_id: uuid.UUID) -> tuple[bytes, CaseAsset]:
        asset = self.get(asset_id)
        data = self.storage.download(asset.storage_key)
        return data, asset

    def delete(self, asset_id: uuid.UUID, user_id: uuid.UUID, ip: str | None = None) -> None:
        asset = self.get(asset_id)
        self.storage.delete(asset.storage_key)
        self.repo.delete(asset)

        self.audit.log(
            action=AuditAction.ASSET_DELETED,
            user_id=user_id,
            entity_type="case_asset",
            entity_id=asset_id,
            details={"filename": asset.original_filename, "case_id": str(asset.case_id)},
            ip_address=ip,
        )
