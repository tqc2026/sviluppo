from dataclasses import dataclass, field
from typing import List
from datetime import date


@dataclass
class QuoteItem:
    name: str
    description: str
    amount: float
    item_type: str  # "one_time", "monthly", "optional"
    notes: str = ""


@dataclass
class Quote:
    project_name: str = ""
    client_name: str = ""
    date: str = field(default_factory=lambda: date.today().strftime("%d/%m/%Y"))
    items: List[QuoteItem] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)

    @property
    def total_one_time(self) -> float:
        return sum(i.amount for i in self.items if i.item_type == "one_time")

    @property
    def total_monthly(self) -> float:
        return sum(i.amount for i in self.items if i.item_type == "monthly")

    @property
    def total_optional(self) -> float:
        return sum(i.amount for i in self.items if i.item_type == "optional")
