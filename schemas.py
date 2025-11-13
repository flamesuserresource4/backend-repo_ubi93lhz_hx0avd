"""
Database Schemas for Gaming Cafe SaaS

Collections:
- user: customers, admins, cafe owners (simple role field for now)
- cafe: gaming cafes listed on the platform
- slot: time slots per cafe that customers can book
- booking: reservations made by customers for specific slots
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    role: Literal["customer", "owner", "admin"] = Field("customer", description="Access role")
    phone: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(True, description="Active status")

class Cafe(BaseModel):
    name: str = Field(..., description="Cafe name")
    city: str = Field(..., description="City or locality")
    address: str = Field(..., description="Street address")
    cover_image: Optional[str] = Field(None, description="Cover image URL")
    description: Optional[str] = Field(None, description="Short description")
    owner_id: Optional[str] = Field(None, description="Owner user id")

class Slot(BaseModel):
    cafe_id: str = Field(..., description="Cafe id")
    date: str = Field(..., description="YYYY-MM-DD")
    start_time: str = Field(..., description="HH:MM 24h")
    end_time: str = Field(..., description="HH:MM 24h")
    price: float = Field(..., ge=0, description="Price for the slot")
    status: Literal["available", "booked"] = Field("available", description="Slot status")

class Booking(BaseModel):
    cafe_id: str = Field(..., description="Cafe id")
    slot_id: str = Field(..., description="Slot id")
    customer_name: str = Field(..., description="Customer name")
    customer_email: str = Field(..., description="Customer email")
    customer_phone: Optional[str] = Field(None, description="Customer phone")
    status: Literal["pending", "confirmed", "cancelled"] = Field("confirmed", description="Booking status")
