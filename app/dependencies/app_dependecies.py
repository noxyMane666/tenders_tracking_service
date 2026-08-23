from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.dal.db.database import DataBase
from app.dal.uow.abstractions.interfaces import AbstractUnitOfWork
from app.dal.uow.sqlalchemy_uow import SqlAlchemyUnitOfWork
from app.exceptions.domain_exceptions import InvalidAuthTokenException
from app.services.abstractions.interfaces import AbstractAuthService, AbstractTenderService
from app.services.tender_service import TenderServiceImpl

_bearer_scheme = HTTPBearer(auto_error=False)


def get_database(request: Request) -> DataBase:
    return request.app.state.database


async def get_session(
        database: DataBase = Depends(get_database)
) -> AsyncIterator[AsyncSession]:
    async with database.session_factory() as session:
        yield session


def get_unit_of_work(
        session: AsyncSession = Depends(get_session)
) -> AbstractUnitOfWork:
    return SqlAlchemyUnitOfWork(session)


def get_tender_service(
        uow: AbstractUnitOfWork = Depends(get_unit_of_work)
) -> AbstractTenderService:
    return TenderServiceImpl(uow)


def get_auth_service(request: Request) -> AbstractAuthService:
    return request.app.state.auth_service


def get_current_user_id(
        credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
        auth_service: AbstractAuthService = Depends(get_auth_service)
) -> UUID:
    if credentials is None:
        raise InvalidAuthTokenException("Missing bearer token")

    return auth_service.get_current_user_id(credentials.credentials)
