from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
