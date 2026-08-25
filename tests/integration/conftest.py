import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import httpx
import jwt
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app import create_app
from app.api.models.api_models import CreateTenderDTO, UpdateTenderStatusDTO
from app.cofigurations.config import Configuration
from app.dal.db.database import DataBase
from app.dal.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from app.dependencies.app_dependecies import get_session
from app.enums.tender_status import TenderStatus
from app.services.tender_service import TenderServiceImpl


@pytest_asyncio.fixture
async def database() -> AsyncIterator[DataBase]:
    db = DataBase(Configuration().db_settings)
    yield db
    await db.close()


@pytest_asyncio.fixture
async def session(database: DataBase) -> AsyncIterator[AsyncSession]:
    async with database.engine.connect() as connection:
        outer_transaction = await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        async with session_factory() as isolated_session:
            yield isolated_session
        await outer_transaction.rollback()


@pytest_asyncio.fixture
async def uow(session: AsyncSession) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session)


@pytest_asyncio.fixture
async def service(uow: SqlAlchemyUnitOfWork) -> TenderServiceImpl:
    return TenderServiceImpl(uow)


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture
async def client(session: AsyncSession) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client


@pytest.fixture
def auth_token(user_id: uuid.UUID) -> str:
    config = Configuration()
    return jwt.encode(
        {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        config.auth_settings.JWT_SECRET,
        algorithm=config.auth_settings.JWT_ALGORITHM,
    )


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth_token}"}


def make_create_dto(**overrides: Any) -> CreateTenderDTO:
    defaults: dict[str, Any] = dict(
        title="Test tender",
        issuer_name="ACME",
        budget=Decimal("100.00"),
        currency="RUB",
    )
    defaults.update(overrides)
    return CreateTenderDTO(**defaults)


def make_update_dto(new_status: TenderStatus, update_reason: str = "reason") -> UpdateTenderStatusDTO:
    return UpdateTenderStatusDTO(new_status=new_status, update_reason=update_reason)
