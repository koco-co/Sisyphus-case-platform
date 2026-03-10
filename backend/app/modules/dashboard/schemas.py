from __future__ import annotations

from datetime import datetime
from typing import Literal

from app.shared.base_schema import BaseSchema


class DashboardStatsResponse(BaseSchema):
    product_count: int
    iteration_count: int
    requirement_count: int
    testcase_count: int
    coverage_rate: int
    weekly_cases: int
    pending_diagnosis: int


class DashboardActivityItem(BaseSchema):
    id: str
    time: datetime
    action: str
    resource: str
    resource_id: str
    title: str
    user: str


class DashboardPendingItem(BaseSchema):
    id: str
    type: Literal["unconfirmed_testpoint", "pending_review", "failed_diagnosis", "low_coverage"]
    title: str
    description: str
    product_name: str
    priority: Literal["high", "medium", "low"]
    link: str
    created_at: datetime
