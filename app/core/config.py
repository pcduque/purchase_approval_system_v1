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
    approval_base_url: str = field(
        default_factory=lambda: os.getenv(
            "APPROVAL_BASE_URL",
            "http://localhost:5173/approve",
        )
    )
    evidence_bucket_name: str = field(
        default_factory=lambda: os.getenv(
            "EVIDENCE_BUCKET_NAME",
            "purchase-approval-evidence-pcduque",
        )
    )
