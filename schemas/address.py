from pydantic import BaseModel
from typing import Optional

class AddressBase(BaseModel):
    full_name: str
    phone: str
    address_line: str
    city: str
    state: str
    pincode: str
    country: str


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address_line: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: Optional[str] = None


class AddressResponse(AddressBase):
    id: int

    class Config:
        from_attributes = True