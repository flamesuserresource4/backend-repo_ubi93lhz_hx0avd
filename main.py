import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import User, Cafe, Slot, Booking

app = FastAPI(title="Gaming Cafe SaaS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def to_str_id(doc):
    if not doc:
        return doc
    d = dict(doc)
    if "_id" in d:
        d["id"] = str(d.pop("_id"))
    return d

class CafeCreate(Cafe):
    pass

class SlotCreate(Slot):
    pass

class BookingCreate(Booking):
    pass

@app.get("/")
def read_root():
    return {"message": "Gaming Cafe SaaS API is running"}

@app.get("/test")
def test_database():
    response = {"backend": "✅ Running", "database": "❌ Not Available"}
    try:
        if db is not None:
            response["database"] = "✅ Connected"
            response["collections"] = db.list_collection_names()
        else:
            response["database"] = "❌ Not Configured"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Public: list cafes
@app.get("/api/cafes")
def list_cafes(city: Optional[str] = None):
    query = {"city": city} if city else {}
    cafes = get_documents("cafe", query, limit=50)
    return [to_str_id(c) for c in cafes]

# Public: list slots for a cafe and date
@app.get("/api/cafes/{cafe_id}/slots")
def list_slots(cafe_id: str, date: Optional[str] = None):
    q = {"cafe_id": cafe_id}
    if date:
        q["date"] = date
    slots = get_documents("slot", q, limit=200)
    return [to_str_id(s) for s in slots]

# Public: create booking
@app.post("/api/bookings")
def create_booking(payload: BookingCreate):
    # Basic validation: ensure slot is available
    slot = db["slot"].find_one({"_id": ObjectId(payload.slot_id)}) if ObjectId.is_valid(payload.slot_id) else None
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    if slot.get("status") != "available":
        raise HTTPException(status_code=400, detail="Slot is not available")

    booking_id = create_document("booking", payload)
    # Mark slot as booked
    db["slot"].update_one({"_id": slot["_id"]}, {"$set": {"status": "booked"}})

    return {"id": booking_id, "message": "Booking confirmed"}

# Owner/Admin: create cafe
@app.post("/api/cafes")
def create_cafe(payload: CafeCreate):
    cafe_id = create_document("cafe", payload)
    return {"id": cafe_id}

# Owner/Admin: create slots in bulk for a cafe
class BulkSlots(BaseModel):
    cafe_id: str
    slots: List[Slot]

@app.post("/api/slots/bulk")
def create_slots_bulk(payload: BulkSlots):
    if not ObjectId.is_valid(payload.cafe_id):
        raise HTTPException(status_code=400, detail="Invalid cafe id")
    docs = []
    for s in payload.slots:
        doc = s.model_dump()
        doc["cafe_id"] = payload.cafe_id
        docs.append(doc)
    for d in docs:
        create_document("slot", d)
    return {"created": len(docs)}

# Admin/Owner dashboards - simple stats
@app.get("/api/admin/stats")
def admin_stats():
    return {
        "cafes": db["cafe"].count_documents({}) if db else 0,
        "slots": db["slot"].count_documents({}) if db else 0,
        "bookings": db["booking"].count_documents({}) if db else 0,
    }

@app.get("/api/owner/{owner_id}/bookings")
def owner_bookings(owner_id: str):
    cafes = list(db["cafe"].find({"owner_id": owner_id})) if db else []
    cafe_ids = [str(c["_id"]) for c in cafes]
    bookings = list(db["booking"].find({"cafe_id": {"$in": cafe_ids}})) if db else []
    return [to_str_id(b) for b in bookings]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
