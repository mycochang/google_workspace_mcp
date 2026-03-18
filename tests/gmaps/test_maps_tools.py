import json
import pytest
from unittest.mock import Mock, patch, AsyncMock
from gmaps.maps_tools import (
    google_workspace_search_places,
    google_workspace_get_travel_time,
)

# Mock responses
MOCK_PLACES_RESPONSE = {
    "status": "OK",
    "results": [
        {
            "name": "Parcheggio Huber",
            "formatted_address": "Via Otto Huber, 18, 39012 Merano BZ, Italy",
            "rating": 4.2,
            "user_ratings_total": 120,
            "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
            "geometry": {"location": {"lat": 46.671, "lng": 11.164}},
        }
    ],
}

MOCK_DIRECTIONS_RESPONSE = {
    "status": "OK",
    "routes": [
        {
            "summary": "Via Otto Huber",
            "legs": [
                {
                    "distance": {"text": "5.0 km", "value": 5000},
                    "duration": {"text": "12 mins", "value": 720},
                    "start_address": "Origin St, 1",
                    "end_address": "Dest St, 2",
                }
            ],
        }
    ],
}


@pytest.fixture
def mock_env_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test_api_key_123")


@pytest.mark.asyncio
async def test_search_places_success(mock_env_api_key):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = MOCK_PLACES_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result_str = await google_workspace_search_places("Parcheggio Huber Merano")
        result = json.loads(result_str)

        assert result["query"] == "Parcheggio Huber Merano"
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "Parcheggio Huber"
        assert "46.671,11.164" in result["results"][0]["maps_url"]


@pytest.mark.asyncio
async def test_search_places_missing_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

    result_str = await google_workspace_search_places("Parcheggio Huber")
    assert "Error: GOOGLE_MAPS_API_KEY is not set" in result_str
    assert "Prototype Note" in result_str


@pytest.mark.asyncio
async def test_get_travel_time_success(mock_env_api_key):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_response = Mock()
        mock_response.json.return_value = MOCK_DIRECTIONS_RESPONSE
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result_str = await google_workspace_get_travel_time("Origin", "Destination")
        result = json.loads(result_str)

        assert result["distance"] == "5.0 km"
        assert result["duration"] == "12 mins"
        assert result["mode"] == "driving"


@pytest.mark.asyncio
async def test_get_travel_time_invalid_mode(mock_env_api_key):
    result_str = await google_workspace_get_travel_time("A", "B", mode="flying")
    assert "Error: mode must be one of" in result_str


@pytest.mark.asyncio
async def test_get_travel_time_missing_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)

    result_str = await google_workspace_get_travel_time("A", "B")
    assert "Error: GOOGLE_MAPS_API_KEY is not set" in result_str
