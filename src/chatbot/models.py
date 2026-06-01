from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WorkRecord:
    author: str
    title: str
    year_label: str
    genre: str
    region: str
    year_start: Optional[int]
    year_end: Optional[int]

    @property
    def display_year(self) -> str:
        return self.year_label or "không rõ năm"


@dataclass(frozen=True)
class SearchHit:
    record: WorkRecord
    score: float

