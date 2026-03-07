from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_asset import KnowledgeAsset


async def list_assets(db: AsyncSession) -> list[KnowledgeAsset]:
    result = await db.execute(select(KnowledgeAsset).order_by(KnowledgeAsset.id.asc()))
    return list(result.scalars().all())


async def promote_asset(db: AsyncSession, asset_id: int) -> KnowledgeAsset | None:
    asset = await db.scalar(select(KnowledgeAsset).where(KnowledgeAsset.id == asset_id))
    if asset is None:
        return None

    asset.status = 'curated'
    asset.quality_level = 'curated'
    await db.commit()
    await db.refresh(asset)
    return asset
