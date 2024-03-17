import datetime
from enum import IntEnum, Enum

from pydantic import BaseModel
import decimal


class InteractionType(IntEnum):
    """
    0: Missing Type
    1->99: Normal
        1: Elle ma is lelijk
        ...
    100->199: Monetary
        100: Bought
        101: User_derived Refund
        102: Staff_driven Refund
        ...
    200->299: Staff
        200: Created Item
        ...

    300->399: RecommenderSystem specific
        300: Clicked on
        301: Viewed
        302: Shared
        ...
    """

    """ Missing 0 """
    missing_type = 0

    """ Normal 1->99 """

    """ Monetary 100->199 """
    bought = 100

    """ Staff 200->299 """

    """ Recommender System Specific 300->399 """


class TransactionStatusEnum(Enum):
    SUCCESSFUL = "SUCCESSFUL"  # Payment has succeeded
    CANCELLED = "CANCELLED"  # Payment was cancelled
    FAILED = "FAILED"  # Payment Failed
    PENDING = "PENDING"  # Awaiting confirmation
    PROCESSING = "PROCESSING"  # Not quite succeeded, but we won't cancel the checkout anymore
    REFUNDED = "REFUNDED"
    REFUND_PENDING = "REFUND_PENDING"


class ValidityEnum(Enum):
    valid = 'valid'  # everything is as should be
    invalid = 'invalid'  # item was likely not fully paid for
    manually_verified = 'manually_verified'  # item was manually verified
    consumed = 'consumed'  # item was already used before


class PyStaffInteraction(BaseModel):
    id: int
    user_id: str
    user_email: str | None = None  # useful for displaying in columns

    interaction_type: InteractionType
    item_id: str
    item_name: str | None = None  # useful for displaying in columns
    date_created: datetime.datetime


class PyStaffTransaction(BaseModel):
    interaction: PyStaffInteraction
    product_blueprint_id: int

    product: dict
    count: int
    amount: decimal.Decimal
    currency: str

    status: TransactionStatusEnum
    checkout_id: str

    validity: ValidityEnum

    date_created: datetime.datetime
    date_completed: datetime.datetime | None

    note: str | None = None
