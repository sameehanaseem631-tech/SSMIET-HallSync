
import json
import time

from fastapi import APIRouter, Depends, HTTPException
from google import genai
from sqlalchemy.orm import Session

from app.database import get_db, settings
from app.models import Booking, Hall, User
from app.routers.booking import get_current_user
from app.schemas.recommendation import HallRecommendationRequest


router = APIRouter(
    prefix="/api/ai",
    tags=["AI Recommendations"],
)


@router.post("/recommend-hall")
def recommend_hall(
    data: HallRecommendationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    total_started = time.perf_counter()

    # 1. Check API key
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key is missing from .env",
        )

    # 2. Validate event time
    if data.end_time <= data.start_time:
        raise HTTPException(
            status_code=422,
            detail="End time must be later than start time",
        )

    # 3. Find halls with sufficient capacity
    db_started = time.perf_counter()

    halls = (
        db.query(Hall)
        .filter(
            Hall.is_available.is_(True),
            Hall.capacity >= data.attendees,
        )
        .order_by(Hall.id)
        .all()
    )

    candidates = []

    # 4. Check booking conflicts and facilities
    for hall in halls:
        conflict = (
            db.query(Booking.id)
            .filter(
                Booking.hall_id == hall.id,
                Booking.event_date == data.event_date,
                Booking.status.in_(
                    ["pending", "approved", "confirmed"]
                ),
                Booking.start_time < data.end_time,
                Booking.end_time > data.start_time,
            )
            .first()
        )

        if conflict:
            continue

        facilities_text = (hall.facilities or "").lower()

        missing_facilities = [
            facility.strip().lower()
            for facility in data.required_facilities
            if facility.strip().lower() not in facilities_text
        ]

        if missing_facilities:
            continue

        candidates.append({
            "hall_id": hall.id,
            "hall_name": hall.name,
            "location": hall.location,
            "capacity": hall.capacity,
            "available_seats": hall.capacity - data.attendees,
            "facilities": hall.facilities or "",
        })

    print(
        f"Hall database checks completed in "
        f"{time.perf_counter() - db_started:.2f} seconds"
    )

    # 5. Return immediately if no suitable halls exist
    if not candidates:
        return {
            "ai_provider": "Google Gemini",
            "recommendation_count": 0,
            "recommendations": [],
            "message": "No available halls match your requirements.",
        }

    # 6. Build Gemini prompt
    prompt = f"""
You are the AI hall recommendation assistant for SSMIET HallSync AI.

Event date: {data.event_date}
Start time: {data.start_time}
End time: {data.end_time}
Attendees: {data.attendees}
Required facilities: {data.required_facilities}

Verified available halls:
{json.dumps(candidates, ensure_ascii=False)}

Return valid JSON only, without Markdown code fences.

Use exactly this structure:
{{
    "ranked_hall_ids": [1, 2],
    "explanations": {{
        "1": "Why this hall is suitable",
        "2": "Why this hall is suitable"
    }}
}}

Rules:
- Recommend only IDs in the verified list.
- Never invent halls or facilities.
- Prefer suitable capacity with fewer unused seats.
- Give a concise reason for each hall.
"""

    # 7. Call Gemini and log response time
    try:
        print("Starting Gemini recommendation request...")
        gemini_started = time.perf_counter()

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={
                "timeout": 20_000,
            },
        )

        response = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt,
        )

        print(
            "Gemini response received in "
            f"{time.perf_counter() - gemini_started:.2f} seconds"
        )

        answer = response.output_text

        if not answer:
            raise ValueError("Gemini returned an empty response")

        answer = answer.strip()

        # Handle optional Markdown code fences
        if answer.startswith("```"):
            answer = answer.split("\n", 1)[1]
            answer = answer.rsplit("```", 1)[0].strip()

        result = json.loads(answer)

        # 8. Validate returned IDs against verified database halls
        candidates_by_id = {
            hall["hall_id"]: hall
            for hall in candidates
        }

        ranked_ids = []

        for hall_id in result.get("ranked_hall_ids", []):
            if (
                isinstance(hall_id, int)
                and not isinstance(hall_id, bool)
                and hall_id in candidates_by_id
                and hall_id not in ranked_ids
            ):
                ranked_ids.append(hall_id)

        explanations = result.get("explanations", {})
        recommendations = []

        # Ranked halls first
        for hall_id in ranked_ids:
            recommendations.append({
                **candidates_by_id[hall_id],
                "reason": explanations.get(
                    str(hall_id),
                    "This hall meets the event requirements.",
                ),
            })

        # Preserve other verified candidates if Gemini omitted them
        for hall in candidates:
            if hall["hall_id"] not in ranked_ids:
                recommendations.append({
                    **hall,
                    "reason": (
                        "This hall meets the requirements, "
                        "but Gemini did not rank it."
                    ),
                })

        print(
            "Total recommendation time: "
            f"{time.perf_counter() - total_started:.2f} seconds"
        )

        return {
            "ai_provider": "Google Gemini",
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "message": "Recommendations generated successfully.",
        }

    except Exception as exc:
        print(
            "Gemini recommendation error:",
            repr(exc),
        )

        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini recommendation failed. "
                "Check the server terminal for the exact error."
            ),
        )
