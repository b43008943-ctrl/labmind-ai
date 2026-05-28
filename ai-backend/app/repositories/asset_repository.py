"""
LabMind AI — Case Asset Repository
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.case_asset import CaseAsset


class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, asset_id: UUID) -> CaseAsset | None:
        return self.db.get(CaseAsset, asset_id)

    def create(self, asset: CaseAsset) -> CaseAsset:
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        return asset

    def list_by_case(self, case_id: UUID) -> list[CaseAsset]:
        stmt = (
            select(CaseAsset)
            .where(CaseAsset.case_id == case_id)
            .order_by(CaseAsset.uploaded_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def delete(self, asset: CaseAsset) -> None:
        self.db.delete(asset)
        self.db.commit()
