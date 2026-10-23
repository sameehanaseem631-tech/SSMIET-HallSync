
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 1. Login / Authentication
from app.routers.auth import router as auth_router

# 2. Dashboard
from app.routers.dashboard import router as dashboard_router

# 3. Seminar Hall
from app.routers.halls import router as halls_router

# 4. Booking
from app.routers.booking import router as bookings_router

# 5. Calendar
from app.routers.calendar import router as calendar_router

# 6. Campus Map
from app.routers.campus_map import router as campus_map_router

# 7. Resources
from app.routers.resource import router as resources_router

# 8. Maintenance
from app.routers.maintenance import router as maintenance_router

# 9. Reports
from app.routers.reports import router as reports_router

# 10. AI Hall Recommendation
from app.routers.ai import router as ai_router


# Create FastAPI application
app = FastAPI(
    title="SSMIET HallSync AI",
    description=(
        "Smart Hall Allotment, Event Scheduling, "
        "and Resource Management System "
        "for SSM Institute of Engineering and Technology"
    ),
    version="1.0.0",
)


# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/", tags=["General"])
def home():
    return {
        "message": "SSMIET HallSync AI Backend is running",
        "status": "success",
        "version": "1.0.0",
    }


# Health check endpoint
@app.get("/health", tags=["General"])
def health_check():
    return {
        "status": "healthy",
        "application": "SSMIET HallSync AI",
    }


# Register API routers

# Login / Authentication
app.include_router(auth_router)

# Dashboard
app.include_router(dashboard_router)

# Seminar Hall
app.include_router(halls_router)

# Booking
app.include_router(bookings_router)

# Calendar
app.include_router(calendar_router)

# Campus Map
app.include_router(campus_map_router)

# Resources
app.include_router(resources_router)

# Maintenance
app.include_router(maintenance_router)

# Reports
app.include_router(reports_router)

# AI Recommendation
app.include_router(ai_router)
