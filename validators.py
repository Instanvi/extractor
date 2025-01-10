from typing import Dict, Any, Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator, Field, computed_field

class LineItemValidator(BaseModel):
    item_name: str
    item_code: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal

    @field_validator('total_price')
    @classmethod
    def validate_total_price(cls, v: Decimal, info) -> Decimal:
        values = info.data
        if 'quantity' in values and 'unit_price' in values:
            expected_total = values['quantity'] * values['unit_price']
            if abs(v - expected_total) > Decimal('0.01'):
                raise ValueError(f"Total price {v} doesn't match quantity * unit price {expected_total}")
        return v

class DocumentValidator(BaseModel):
    doc_type: str
    doc_number: str
    issue_date: Optional[str] = None
    due_date: Optional[str] = None
    supplier_name: str
    supplier_address: Optional[str] = None
    customer_name: str
    customer_address: Optional[str] = None
    total_amount: Decimal
    tax_amount: Optional[Decimal] = None
    line_items: List[LineItemValidator]
    raw_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        valid_types = {'invoice', 'purchase_order'}
        if v.lower() not in valid_types:
            raise ValueError(f'Document type must be one of {valid_types}')
        return v.lower()

    @field_validator('issue_date', 'due_date')
    @classmethod
    def validate_dates(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        try:
            # Support multiple date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y']:
                try:
                    datetime.strptime(v, fmt)
                    return v
                except ValueError:
                    continue
            raise ValueError
        except ValueError:
            raise ValueError('Invalid date format')

    @field_validator('total_amount')
    @classmethod
    def validate_total(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError('Total amount must be greater than 0')
        return v