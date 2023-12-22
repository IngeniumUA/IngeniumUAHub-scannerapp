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
    100->199: Monetair
        100: Bought
        101: User_drived Refund
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

    """ Monetair 100->199 """
    bought = 100

    """ Staff 200->299 """

    """ Recommender System Specific 300->399 """


class CheckoutStatusEnum(Enum):
    SUCCESSFUL = "SUCCESSFUL"  # Payment has succeeded
    CANCELLED = "CANCELLED"  # Payment was cancelled
    FAILED = "FAILED"  # Payment Failed
    PENDING = "PENDING"  # Awaiting confirmation
    PROCESSING = "PROCESSING"  # Not quite succeeded but we won't cancel the checkout anymore


class ValidityEnum(Enum):
    valid = 'valid'
    invalid = 'invalid'
    manually_verified = 'manually_verified'
    consumed = 'consumed'


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

    status: CheckoutStatusEnum
    checkout_id: str

    validity: ValidityEnum

    date_created: datetime.datetime
    date_completed: datetime.datetime | None