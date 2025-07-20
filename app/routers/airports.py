from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from app.services.airport_service import AirportService

router = APIRouter()
airport_service = AirportService()

@router.get('/search')
def search_airports(q: str = Query(..., min_length=1), limit: int = 10):
    results = airport_service.search_airports(q, limit)
    return JSONResponse(content=results)
