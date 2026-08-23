from enum import StrEnum


class TenderStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"