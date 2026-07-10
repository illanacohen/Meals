from datetime import date

from pydantic import BaseModel, Field


class ShoppingListItem(BaseModel):
    name: str
    quantity: float
    unit: str = Field(description='g, kg, unit, or ml')
    grams: float
    display: str = Field(description='Human-readable line, e.g. "1.4 kg pollo"')


class ShoppingListResponse(BaseModel):
    start_date: date
    end_date: date
    plan_ids: list[int]
    plan_count: int
    item_count: int
    items: list[ShoppingListItem]
    lines: list[str] = Field(
        description='Ready-to-show shopping lines',
    )
    message: str
