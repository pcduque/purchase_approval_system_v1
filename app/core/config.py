import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    requests_table_name: str = field(
        default_factory=lambda: os.getenv("REQUESTS_TABLE_NAME", "purchase_requests")
    )
    approvals_table_name: str = field(
        default_factory=lambda: os.getenv("APPROVALS_TABLE_NAME", "purchase_approvals")
    )
