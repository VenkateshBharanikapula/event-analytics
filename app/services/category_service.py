import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CategoryNotFoundException
from app.repositories.event_repository import CategoryRepository
from app.schemas.event import CategoryCreate

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def create_category(self, data: CategoryCreate):
        cat = await self.repo.create(data.name, data.description)
        logger.info("Category created: %s", cat.name)
        return cat

    async def list_categories(self):
        return await self.repo.get_all()

    async def get_category(self, id_: int):
        cat = await self.repo.get_by_id(id_)
        if not cat:
            raise CategoryNotFoundException(id_)
        return cat
