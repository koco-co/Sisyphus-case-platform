from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.domain.knowledge.service import list_assets, promote_asset

router = APIRouter(prefix='/api/knowledge-assets', tags=['knowledge'])


@router.get('')
async def get_knowledge_assets(db: AsyncSession = Depends(get_db)):
    assets = await list_assets(db)
    return [
        {
            'id': asset.id,
            'title': asset.title,
            'status': asset.status,
            'quality_level': asset.quality_level,
        }
        for asset in assets
    ]


@router.post('/{asset_id}:promote')
async def promote_knowledge_asset(asset_id: int, db: AsyncSession = Depends(get_db)):
    asset = await promote_asset(db, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail='知识资产不存在')
    return {
        'id': asset.id,
        'status': asset.status,
        'quality_level': asset.quality_level,
    }
