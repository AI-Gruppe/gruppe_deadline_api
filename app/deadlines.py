from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, UUID4, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from arango import ArangoClient
from arango.exceptions import DocumentUpdateError
import os

class Category(str, Enum):
    HARDWARE = 'Hardware'
    SOFTWARE = 'Software'
    FIRMWARE = 'Firmware'
    ACCOUNTING = 'Accounting'
    PRODUCTION = 'Production'
    CERTIFICATION = 'Certification'
    DELIVERY = 'Delivery'
    OTHER = 'Other'

class Status(str, Enum):
    OPEN = 'Open'
    DONE = 'Done'
    POSTPONED = 'Postponed'

class Deadline(BaseModel):
    uuid: UUID4 = Field(default_factory=UUID4, description="UUID of the Deadline. UUID is created automagically")
    title: str = Field(description="Title of the Deadline")
    description: Optional[str] = Field(description="Description of the Deadline. This is optional")
    creation_date: datetime = Field(default=datetime.now(), description="Creation date of the Deadline")
    due_date: datetime = Field(description="Due date of the Deadline. If it was postponed, this is the postponed due date")
    original_due_date: datetime = Field(description="Original due date of the Deadline on the date of creation")
    status: Status = Field(description="Status of the Deadline", default=Status.OPEN)
    category: Category = Field(description="Category of the Deadline", default=Category.OTHER)
    responsible: str = Field(description="Person responsible for the package delivery")
    customer: str = Field(description="Customer for whom the deadline is set")
    tag: Optional[str] = Field(description="Optional tags related to the deadline")

app = FastAPI()

ARANGO_URL = os.getenv('ARANGO_URL', 'http://localhost:8529')
ARANGO_USERNAME = os.getenv('ARANGO_USERNAME', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', 'rootpassword')

def get_db_client():
    client = ArangoClient(hosts=ARANGO_URL)
    db = client.db('deadline_db', username=ARANGO_USERNAME, password=ARANGO_PASSWORD)
    return db

def setup_database():
    db = get_db_client()
    if not db.has_collection('deadlines'):
        db.create_collection('deadlines')

setup_database()

@app.post("/deadlines/", response_model=Deadline)
def create_deadline(deadline: Deadline):
    db = get_db_client()
    collection = db.collection('deadlines')
    collection.insert(deadline.dict())
    return deadline

@app.get("/deadlines/", response_model=list[Deadline])
def get_deadlines(status: Optional[Status] = None):
    db = get_db_client()
    collection = db.collection('deadlines')
    query = {'status': status.value} if status else {}
    return [Deadline(**doc) for doc in collection.find(query)]

@app.put("/deadlines/{uuid}/due-date", response_model=Deadline)
def update_deadline_due_date(uuid: UUID4, new_due_date: datetime):
    db = get_db_client()
    collection = db.collection('deadlines')
    try:
        doc = collection.get(uuid)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Deadline with UUID {uuid} not found")
        doc['due_date'] = new_due_date
        collection.update(doc)
        return Deadline(**doc)
    except DocumentUpdateError:
        raise HTTPException(status_code=500, detail="Error updating the deadline")
    
@app.put("/deadlines/{uuid}/update-status", response_model=BaseModel)
def update_deadline_status(uuid: UUID4, new_status: Status):
    db = get_db_client()
    collection = db.collection('deadlines')
    deadline = collection.get(str(uuid))
    if not deadline:
        raise HTTPException(status_code=404, detail=f"Deadline with UUID {uuid} not found")
    
    # Update the status
    deadline['status'] = new_status.value
    try:
        collection.update(deadline)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating the deadline: {e}")
    
    return {"message": "Deadline status updated successfully"}