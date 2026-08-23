from uuid import UUID

from app.enums.tender_status import TenderStatus


class DomainException(Exception):
    pass


class TenderNotFoundException(DomainException):
    def __init__(self, tender_id: UUID):
        self.tender_id = tender_id
        super().__init__(f"Tender with id {tender_id} not found")


class InvalidTenderStatusTransitionException(DomainException):
    def __init__(self, current_status: TenderStatus, new_status: TenderStatus):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Cannot change tender status from '{current_status}' to '{new_status}'"
        )


class InvalidAuthTokenException(DomainException):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid or expired authentication token: {reason}")
