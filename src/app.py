"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pymongo import MongoClient
from typing import Dict, Any

# Initialize MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['school_activities']
activities_collection = db['activities']

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Sports related activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in local leagues",
        "schedule": "Wednesdays and Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 18,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly matches",
        "schedule": "Tuesdays, 5:00 PM - 6:30 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    # Artistic activities
    "Art Club": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["ella@mergington.edu", "noah@mergington.edu"]
    },
    "Drama Society": {
        "description": "Participate in acting, stage production, and school plays",
        "schedule": "Mondays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["amelia@mergington.edu", "jack@mergington.edu"]
    },
    # Intellectual activities
    "Mathletes": {
        "description": "Compete in math competitions and solve challenging problems",
        "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["charlotte@mergington.edu", "benjamin@mergington.edu"]
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Fridays, 2:00 PM - 3:30 PM",
        "max_participants": 14,
        "participants": ["henry@mergington.edu", "grace@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
async def get_activities():
    """Get all activities"""
    activities = {}
    cursor = activities_collection.find({})
    for doc in cursor:
        activity_name = doc.pop('_id')  # Use activity name as key
        activities[activity_name] = doc
    return activities


@app.post("/activities/{activity_name}/signup")
async def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Add student
    result = activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
async def unregister_from_activity(activity_name: str, email: str):
    """Remove a student from an activity"""
    # Validate activity exists and participant is registered
    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Participant not found in this activity")

    # Remove student
    result = activities_collection.update_one(
        {"_id": activity_name},
        {"$pull": {"participants": email}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update activity")

    return {"message": f"{email} has been removed from {activity_name}."}


# Initialize the database with the predefined activities
@app.on_event("startup")
async def init_db():
    """Initialize the database with predefined activities if empty"""
    if activities_collection.count_documents({}) == 0:
        # Convert the activities dictionary to a list of documents
        activities_data = []
        for name, details in activities.items():
            doc = details.copy()
            doc['_id'] = name  # Use activity name as the document ID
            activities_data.append(doc)
        
        # Insert all activities
        activities_collection.insert_many(activities_data)