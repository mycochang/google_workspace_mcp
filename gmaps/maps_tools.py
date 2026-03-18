"""
Google Maps Tools Prototype

Provides MCP tools for interacting with Google Maps APIs (Places, Directions).
Requires GOOGLE_MAPS_API_KEY in the environment.
"""

import os
import json
import logging
import urllib.parse
from typing import Optional

import httpx
from core.server import server

logger = logging.getLogger(__name__)


def _get_api_key() -> str:
    """Retrieve the Google Maps API key, raising an error if missing."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_MAPS_API_KEY is not set. Please add it to your .env file to use Google Maps tools."
        )
    return api_key


@server.tool()
async def google_workspace_search_places(
    query: str, location: Optional[str] = None
) -> str:
    """
    Search for places using the Google Maps Places API.

    Args:
        query: The search query (e.g., "Parcheggio Huber Merano", "restaurants near Central Park")
        location: Optional location bias in "lat,lon" format.

    Returns:
        JSON string containing matching places with names, addresses, ratings, and Google Maps URLs.
    """
    try:
        api_key = _get_api_key()
    except ValueError as e:
        return f"Error: {e}\n\nPrototype Note: For testing without a key, you can manually construct links like: https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": api_key}
    if location:
        params["location"] = location

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                return f"Google Maps API returned status: {data.get('status')} - {data.get('error_message', '')}"

            results = []
            for place in data.get("results", [])[:5]:  # Limit to top 5 results
                lat = place["geometry"]["location"]["lat"]
                lng = place["geometry"]["location"]["lng"]
                results.append(
                    {
                        "name": place.get("name"),
                        "address": place.get("formatted_address"),
                        "rating": place.get("rating"),
                        "user_ratings_total": place.get("user_ratings_total"),
                        "place_id": place.get("place_id"),
                        "maps_url": f"https://www.google.com/maps/search/?api=1&query={lat},{lng}&query_place_id={place.get('place_id')}",
                    }
                )

            return json.dumps({"query": query, "results": results}, indent=2)

    except httpx.RequestError as e:
        logger.error(f"Error calling Google Maps API: {e}")
        return f"Network error occurred while calling Google Maps API: {e}"


@server.tool()
async def google_workspace_get_travel_time(
    origin: str, destination: str, mode: str = "driving"
) -> str:
    """
    Calculate travel time and distance between two locations using Google Maps Directions API.

    Args:
        origin: The starting address or coordinates.
        destination: The target address or coordinates.
        mode: Travel mode ("driving", "walking", "bicycling", "transit"). Defaults to "driving".

    Returns:
        JSON string containing the estimated travel time, distance, and basic route information.
    """
    try:
        api_key = _get_api_key()
    except ValueError as e:
        return f"Error: {e}"

    if mode not in ["driving", "walking", "bicycling", "transit"]:
        return "Error: mode must be one of 'driving', 'walking', 'bicycling', or 'transit'."

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "mode": mode,
        "key": api_key,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                return f"Google Maps API returned status: {data.get('status')} - {data.get('error_message', '')}"

            route = data["routes"][0]
            leg = route["legs"][0]

            result = {
                "origin": leg["start_address"],
                "destination": leg["end_address"],
                "mode": mode,
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "summary": route.get("summary", "No summary available"),
            }

            return json.dumps(result, indent=2)

    except httpx.RequestError as e:
        logger.error(f"Error calling Google Maps API: {e}")
        return f"Network error occurred while calling Google Maps API: {e}"
