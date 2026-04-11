import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class AccountType(str, enum.Enum):
    FLEXI = "flexi"
    EMERGENCY = "emergency"
    GOAL = "goal"
    LOCKED = "locked"
    


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    GOAL_DEPOSIT = "goal_deposit"
    GOAL_WITHDRAWAL = "goal_withdrawal"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"


class DepositFrequency(str, enum.Enum):
    """How often the user plans to contribute to a savings goal."""

    daily = "daily"
    weekly = "weekly"
    biweekly = "biweekly"
    monthly = "monthly"


class GoalStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    paused = "paused"
    cancelled = "cancelled"
