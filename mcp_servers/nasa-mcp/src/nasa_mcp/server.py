from typing import Any, List, Union
import httpx
import json
import logging
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
from datetime import datetime

# Load data from .env file
load_dotenv()

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NasaMCPServer")

# Initialize FastMCP server
mcp = FastMCP(
    "nasa-mcp",
    description="MCP server for querying NASA (National Aeronautics and Space Administration) APIs"
)

# Constants
NASA_API_BASE = "https://api.nasa.gov"
# Get API key from https://api.nasa.gov/
API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")

async def make_nasa_request(url: str, params: dict = None) -> Union[dict[str, Any], List[Any], None]:
    """Make a request to the NASA API with proper error handling.
    Handles both JSON and binary (image) responses.
    """
    
    logger.info(f"Making request to: {url} with params: {params}")
    
    if params is None:
        params = {}
    
    # Ensure API key is included in parameters
    if "api_key" not in params:
        params["api_key"] = API_KEY
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=30.0, follow_redirects=True)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

            content_type = response.headers.get("Content-Type", "").lower()
            
            if "application/json" in content_type:
                try:
                    return response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON decode error for URL {response.url}: {json_err}")
                    logger.error(f"Response text: {response.text[:500]}") # Log beginning of text
                    return {"error": "Failed to decode JSON response", "details": str(json_err)}
            elif content_type.startswith("image/"):
                logger.info(f"Received binary image content ({content_type}) from {response.url}")
                # Return a dictionary indicating binary content was received
                return {
                    "binary_content": True, 
                    "content_type": content_type,
                    "url": str(response.url) # Return the final URL after redirects
                }
            else:
                # Handle other unexpected content types
                logger.warning(f"Unexpected content type '{content_type}' received from {response.url}")
                return {"error": f"Unexpected content type: {content_type}", "content": response.text[:500]}

        except httpx.HTTPStatusError as http_err:
            logger.error(f"HTTP error occurred: {http_err} - {http_err.response.status_code} for URL {http_err.request.url}")
            try:
                # Try to get more details from response body if possible
                error_details = http_err.response.json()
            except Exception:
                error_details = http_err.response.text[:500]
            return {"error": f"HTTP error: {http_err.response.status_code}", "details": error_details}
        except httpx.RequestError as req_err:
            logger.error(f"Request error occurred: {req_err} for URL {req_err.request.url}")
            return {"error": "Request failed", "details": str(req_err)}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return {"error": "An unexpected error occurred", "details": str(e)}

# ---------------------- APOD (Astronomy Picture of the Day) ----------------------

@mcp.tool()
async def get_astronomy_picture_of_day(date: str = None, count: int = None, thumbs: bool = False) -> str:
    """Get NASA's astronomy picture of the day.
    
    Args:
        date: Date of the image in YYYY-MM-DD format. If not specified, the current date is used.
        count: If specified, returns 'count' random images. Cannot be used with 'date'.
        thumbs: If True, returns the thumbnail URL for videos. If APOD is not a video, this parameter is ignored.
    """
    params = {}
    
    if date:
        params["date"] = date
    if count:
        params["count"] = count
    if thumbs:
        params["thumbs"] = "true"
    
    url = f"{NASA_API_BASE}/planetary/apod"
    data = await make_nasa_request(url, params)
    
    if not data:
        return "Could not retrieve astronomy picture of the day data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
         # APOD URL itself might point to an image, but the API response should be JSON
        return f"Received unexpected binary content from APOD API. URL: {data.get('url')}"

    try:
        # If count is specified, data will be a list
        if isinstance(data, list):
            result = []
            for item in data:
                result.append(f"Date: {item.get('date', 'Unknown')}")
                result.append(f"Title: {item.get('title', 'No title')}")
                result.append(f"Explanation: {item.get('explanation', 'No explanation')}")
                result.append(f"URL: {item.get('url', 'Not available')}")
                if 'copyright' in item:
                    result.append(f"Copyright: {item.get('copyright', 'Unknown')}")
                if thumbs and 'thumbnail_url' in item:
                    result.append(f"Thumbnail URL: {item.get('thumbnail_url', 'Not available')}")
                result.append("-" * 40)
            
            return "n".join(result)
        else:
            # If it's a single image
            result = f"""
Date: {data.get('date', 'Unknown')}
Title: {data.get('title', 'No title')}
Explanation: {data.get('explanation', 'No explanation')}
URL: {data.get('url', 'Not available')}
"""
            if 'copyright' in data:
                result += f"Copyright: {data.get('copyright', 'Unknown')}n"
            if thumbs and 'thumbnail_url' in data:
                result += f"Thumbnail URL: {data.get('thumbnail_url', 'Not available')}n"
            
            return result
    except Exception as e:
        logger.error(f"Error processing APOD data: {str(e)}")
        return f"Error processing astronomy picture data: {str(e)}"

# ---------------------- Asteroids NeoWs (Near Earth Object Web Service) ----------------------

@mcp.tool()
async def get_asteroids_feed(start_date: str, end_date: str = None) -> str:
    """Get a list of asteroids based on their closest approach date to Earth.
    
    Args:
        start_date: Start date for asteroid search in YYYY-MM-DD format.
        end_date: End date for asteroid search in YYYY-MM-DD format. 
        The Feed date limit is only 7 Days. If not specified, 7 days after start_date is used.
    """
    params = {
        "start_date": start_date
    }
    
    if end_date:
        params["end_date"] = end_date
    
    url = f"{NASA_API_BASE}/neo/rest/v1/feed"
    data = await make_nasa_request(url, params)
    
    if not data:
        return "Could not retrieve asteroid data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Asteroids Feed API. URL: {data.get('url')}"

    try:
        element_count = data.get('element_count', 0)
        near_earth_objects = data.get('near_earth_objects', {})
        
        result = [f"Total asteroids found: {element_count}"]
        
        for date_str, asteroids in near_earth_objects.items():
            result.append(f"nDate: {date_str}")
            result.append(f"Number of asteroids: {len(asteroids)}")
            
            for asteroid in asteroids:
                result.append(f"n  ID: {asteroid.get('id', 'Unknown')}")
                result.append(f"  Name: {asteroid.get('name', 'Unknown')}")
                result.append(f"  Estimated diameter (min): {asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_min', 'Unknown')} km")
                result.append(f"  Estimated diameter (max): {asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_max', 'Unknown')} km")
                result.append(f"  Potentially hazardous: {'Yes' if asteroid.get('is_potentially_hazardous_asteroid', False) else 'No'}")
                
                # Information about closest approach
                close_approaches = asteroid.get('close_approach_data', [])
                if close_approaches:
                    approach = close_approaches[0]
                    result.append(f"  Approach date: {approach.get('close_approach_date_full', 'Unknown')}")
                    result.append(f"  Distance (km): {approach.get('miss_distance', {}).get('kilometers', 'Unknown')}")
                    result.append(f"  Relative velocity (km/h): {approach.get('relative_velocity', {}).get('kilometers_per_hour', 'Unknown')}")
        
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Asteroids Feed data: {str(e)}")
        return f"Error processing asteroid data: {str(e)}"

@mcp.tool()
async def get_asteroid_lookup(asteroid_id: str) -> str:
    """Look up a specific asteroid based on its NASA JPL ID.
    
    Args:
        asteroid_id: Asteroid ID in the NASA JPL small body (SPK-ID) system.
    """
    url = f"{NASA_API_BASE}/neo/rest/v1/neo/{asteroid_id}"
    data = await make_nasa_request(url)
    
    if not data:
        return f"Could not retrieve data for asteroid ID {asteroid_id} due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Asteroid Lookup API. URL: {data.get('url')}"

    try:
        result = [
            f"ID: {data.get('id', 'Unknown')}",
            f"Name: {data.get('name', 'Unknown')}",
            f"Designation: {data.get('designation', 'Unknown')}",
            f"NASA JPL URL: {data.get('nasa_jpl_url', 'Not available')}",
            f"Absolute magnitude: {data.get('absolute_magnitude_h', 'Unknown')}",
            f"nEstimated diameter:",
            f"  Minimum (km): {data.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_min', 'Unknown')}",
            f"  Maximum (km): {data.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_max', 'Unknown')}",
            f"nPotentially hazardous: {'Yes' if data.get('is_potentially_hazardous_asteroid', False) else 'No'}",
            f"Sentry Object: {'Yes' if data.get('is_sentry_object', False) else 'No'}" # Corrected field name based on common API patterns
        ]
        
        # Approach information
        close_approaches = data.get('close_approach_data', [])
        if close_approaches:
            result.append("nClose approaches:")
            for i, approach in enumerate(close_approaches[:5], 1):  # Limit to first 5 to avoid overload
                result.append(f"n  Approach {i}:")
                result.append(f"  Date: {approach.get('close_approach_date_full', 'Unknown')}")
                result.append(f"  Orbiting body: {approach.get('orbiting_body', 'Unknown')}")
                result.append(f"  Distance (km): {approach.get('miss_distance', {}).get('kilometers', 'Unknown')}")
                result.append(f"  Relative velocity (km/h): {approach.get('relative_velocity', {}).get('kilometers_per_hour', 'Unknown')}")
            
            if len(close_approaches) > 5:
                result.append(f"n  ... and {len(close_approaches) - 5} more approaches.")
        
        # Orbital data
        orbital_data = data.get('orbital_data', {})
        if orbital_data:
            result.append("nOrbital data:")
            result.append(f"  Orbit determination date: {orbital_data.get('orbit_determination_date', 'Unknown')}") # Corrected field name
            result.append(f"  Semi-major axis: {orbital_data.get('semi_major_axis', 'Unknown')} AU")
            result.append(f"  Eccentricity: {orbital_data.get('eccentricity', 'Unknown')}")
            result.append(f"  Inclination: {orbital_data.get('inclination', 'Unknown')} degrees")
            result.append(f"  Orbital period: {orbital_data.get('orbital_period', 'Unknown')} days")
        
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Asteroid Lookup data: {str(e)}")
        return f"Error processing asteroid data: {str(e)}"

@mcp.tool()
async def browse_asteroids() -> str:
    """Browse the asteroid dataset."""
    url = f"{NASA_API_BASE}/neo/rest/v1/neo/browse"
    data = await make_nasa_request(url)
    
    if not data:
        return "Could not retrieve asteroid dataset due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Browse Asteroids API. URL: {data.get('url')}"

    try:
        near_earth_objects = data.get('near_earth_objects', [])
        page_info = f"Page {data.get('page', {}).get('number', 'Unknown')} of {data.get('page', {}).get('total_pages', 'Unknown')}"
        total_elements = f"Total elements: {data.get('page', {}).get('total_elements', 'Unknown')}"
        
        result = [page_info, total_elements, ""]
        
        # Limit the number of asteroids displayed to avoid excessive output
        display_limit = 10 
        count = 0
        for asteroid in near_earth_objects:
            if count >= display_limit:
                result.append(f"n... and {len(near_earth_objects) - display_limit} more asteroids on this page.")
                break
            result.append(f"ID: {asteroid.get('id', 'Unknown')}")
            result.append(f"Name: {asteroid.get('name', 'Unknown')}")
            result.append(f"Absolute magnitude: {asteroid.get('absolute_magnitude_h', 'Unknown')}")
            result.append(f"Estimated diameter (min): {asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_min', 'Unknown')} km")
            result.append(f"Estimated diameter (max): {asteroid.get('estimated_diameter', {}).get('kilometers', {}).get('estimated_diameter_max', 'Unknown')} km")
            result.append(f"Potentially hazardous: {'Yes' if asteroid.get('is_potentially_hazardous_asteroid', False) else 'No'}")
            result.append("-" * 40)
            count += 1
        
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Browse Asteroids data: {str(e)}")
        return f"Error processing asteroid data: {str(e)}"

# ---------------------- DONKI (Space Weather Database Of Notifications, Knowledge, Information) ----------------------
# Helper function to format DONKI results consistently
def format_donki_results(data: list, title_prefix: str, id_key: str) -> str:
    if not data: 
        return f"No {title_prefix.lower()} data for the specified period."
    
    result = [f"{title_prefix} found: {len(data)}"]
    display_limit = 10
    count = 0

    for item in data:
        if count >= display_limit:
            result.append(f"n... and {len(data) - display_limit} more entries.")
            break
        
        result.append(f"nID: {item.get(id_key, 'Unknown')}")
        # Add common fields if they exist
        if 'startTime' in item: result.append(f"Start Time: {item.get('startTime', 'Unknown')}")
        if 'eventTime' in item: result.append(f"Event Time: {item.get('eventTime', 'Unknown')}")
        if 'sourceLocation' in item: result.append(f"Source Location: {item.get('sourceLocation', 'Unknown')}")
        if 'note' in item: result.append(f"Note: {item.get('note', 'N/A')}")
        if 'link' in item: result.append(f"Link: {item.get('link', 'N/A')}")
        
        # Specific fields for different DONKI types can be added here if needed
        # Example for CME:
        if id_key == 'activityID' and 'cmeAnalyses' in item:
            analyses = item.get('cmeAnalyses', [])
            if analyses:
                result.append("  Analyses:")
                for analysis in analyses[:2]: # Limit analyses shown
                    result.append(f"    - Time: {analysis.get('time21_5', 'N/A')}, Speed: {analysis.get('speed', 'N/A')} km/s, Type: {analysis.get('type', 'N/A')}")
        
        # Example for GST:
        if id_key == 'gstID' and 'allKpIndex' in item:
             kp_indices = item.get('allKpIndex', [])
             if kp_indices:
                 result.append("  Kp Indices (first 2):")
                 for kp in kp_indices[:2]:
                     result.append(f"    - Time: {kp.get('observedTime', 'N/A')}, Index: {kp.get('kpIndex', 'N/A')}")

        # Linked Events
        linked_events = item.get('linkedEvents', [])
        if linked_events:
            result.append("  Related event IDs (first 5):")
            result.append("    " + ", ".join([le.get('activityID', 'N/A') for le in linked_events[:5]]))

        result.append("-" * 40)
        count += 1
        
    return "n".join(result)

@mcp.tool()
async def get_coronal_mass_ejection(start_date: str = None, end_date: str = None) -> str:
    """Get coronal mass ejection (CME) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/CME"
    data = await make_nasa_request(url, params)
    
    if not data: 
        return "Could not retrieve CME data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from CME API. URL: {data.get('url')}"

    try:
        # Ensure data is a list for format_donki_results
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from CME API: {data}")
            return "Received unexpected data format from CME API."
            
        return format_donki_results(data, "Coronal Mass Ejections", "activityID")
    except Exception as e:
        logger.error(f"Error processing CME data: {str(e)}")
        return f"Error processing coronal mass ejection data: {str(e)}"

@mcp.tool()
async def get_geomagnetic_storm(start_date: str = None, end_date: str = None) -> str:
    """Get geomagnetic storm (GST) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/GST"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve GST data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from GST API. URL: {data.get('url')}"

    try:
        # Ensure data is a list for format_donki_results
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from GST API: {data}")
            return "Received unexpected data format from GST API."
            
        return format_donki_results(data, "Geomagnetic Storms", "gstID")
    except Exception as e:
        logger.error(f"Error processing GST data: {str(e)}")
        return f"Error processing geomagnetic storm data: {str(e)}"

@mcp.tool()
async def get_solar_flare(start_date: str = None, end_date: str = None) -> str:
    """Get solar flare (FLR) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/FLR"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve FLR data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from FLR API. URL: {data.get('url')}"

    try:
        # Ensure data is a list
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from FLR API: {data}")
            return "Received unexpected data format from FLR API."
            
        # Add specific FLR fields to the formatter if needed, or format here
        if not data: 
            return "No solar flare data for the specified period."
            
        result = [f"Solar Flares found: {len(data)}"]
        display_limit = 10
        count = 0
        for flare in data:
            if count >= display_limit: 
                result.append(f"n... and {len(data) - display_limit} more entries.")
                break
            result.append(f"nID: {flare.get('flrID', 'Unknown')}")
            result.append(f"Begin Time: {flare.get('beginTime', 'Unknown')}")
            result.append(f"Peak Time: {flare.get('peakTime', 'Unknown')}")
            result.append(f"End Time: {flare.get('endTime', 'Unknown')}")
            result.append(f"Class: {flare.get('classType', 'Unknown')}")
            result.append(f"Source Location: {flare.get('sourceLocation', 'Unknown')}")
            linked_events = flare.get('linkedEvents', [])
            if linked_events:
                result.append("  Related event IDs (first 5):")
                result.append("    " + ", ".join([le.get('activityID', 'N/A') for le in linked_events[:5]]))
            result.append("-" * 40)
            count += 1
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing FLR data: {str(e)}")
        return f"Error processing solar flare data: {str(e)}"

@mcp.tool()
async def get_solar_energetic_particle(start_date: str = None, end_date: str = None) -> str:
    """Get solar energetic particle (SEP) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/SEP"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve SEP data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from SEP API. URL: {data.get('url')}"

    try:
        # Ensure data is a list for format_donki_results
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from SEP API: {data}")
            return "Received unexpected data format from SEP API."
            
        return format_donki_results(data, "Solar Energetic Particle Events", "sepID")
    except Exception as e:
        logger.error(f"Error processing SEP data: {str(e)}")
        return f"Error processing solar energetic particle data: {str(e)}"

@mcp.tool()
async def get_magnetopause_crossing(start_date: str = None, end_date: str = None) -> str:
    """Get magnetopause crossing (MPC) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/MPC"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve MPC data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from MPC API. URL: {data.get('url')}"

    try:
        # Ensure data is a list for format_donki_results
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from MPC API: {data}")
            return "Received unexpected data format from MPC API."
            
        return format_donki_results(data, "Magnetopause Crossings", "mpcID")
    except Exception as e:
        logger.error(f"Error processing MPC data: {str(e)}")
        return f"Error processing magnetopause crossing data: {str(e)}"

@mcp.tool()
async def get_radiation_belt_enhancement(start_date: str = None, end_date: str = None) -> str:
    """Get radiation belt enhancement (RBE) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/RBE"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve RBE data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from RBE API. URL: {data.get('url')}"

    try:
        # Ensure data is a list for format_donki_results
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from RBE API: {data}")
            return "Received unexpected data format from RBE API."
            
        return format_donki_results(data, "Radiation Belt Enhancements", "rbeID")
    except Exception as e:
        logger.error(f"Error processing RBE data: {str(e)}")
        return f"Error processing radiation belt enhancement data: {str(e)}"

@mcp.tool()
async def get_hight_speed_stream(start_date: str = None, end_date: str = None) -> str: # Note: High* Speed Stream
    """Get high speed stream (HSS) data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 30 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/HSS"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve HSS data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from HSS API. URL: {data.get('url')}"

    try:
        # Ensure data is a list for format_donki_results
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from HSS API: {data}")
            return "Received unexpected data format from HSS API."
            
        return format_donki_results(data, "High Speed Streams", "hssID")
    except Exception as e:
        logger.error(f"Error processing HSS data: {str(e)}")
        return f"Error processing high speed stream data: {str(e)}"

@mcp.tool()
async def get_wsa_enlil_simulation(start_date: str = None, end_date: str = None) -> str:
    """Get WSA+Enlil simulation data.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 7 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
    """
    params = {}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/WSAEnlilSimulations"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve WSA+Enlil simulation data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from WSA+Enlil API. URL: {data.get('url')}"

    try:
        # Ensure data is a list
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from WSA+Enlil API: {data}")
            return "Received unexpected data format from WSA+Enlil API."
            
        # Format WSA+Enlil results (structure is more complex)
        if not data: 
            return "No WSA+Enlil simulation data for the specified period."
            
        result = [f"WSA+Enlil Simulations found: {len(data)}"]
        display_limit = 5
        count = 0
        for sim in data:
            if count >= display_limit: 
                result.append(f"n... and {len(data) - display_limit} more simulations.")
                break
            result.append(f"nSimulation ID: {sim.get('simulationID', 'Unknown')}")
            result.append(f"Model Completion Time: {sim.get('modelCompletionTime', 'Unknown')}")
            # Add more fields as needed, e.g., impactList
            impacts = sim.get('impactList', [])
            if impacts:
                result.append("  Impacts (first 2):")
                for impact in impacts[:2]:
                    result.append(f"    - Location: {impact.get('location', 'N/A')}, Arrival: {impact.get('arrivalTime', 'N/A')}")
            result.append("-" * 40)
            count += 1
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing WSA+Enlil simulation data: {str(e)}")
        return f"Error processing WSA+Enlil simulation data: {str(e)}"

@mcp.tool()
async def get_notifications(start_date: str = None, end_date: str = None, notification_type: str = "all") -> str:
    """Get DONKI notifications.
    
    Args:
        start_date: Start date in YYYY-MM-DD format. Defaults to 7 days before current date.
        end_date: End date in YYYY-MM-DD format. Defaults to current date.
        notification_type: Notification type. Options: all, FLR, SEP, CME, IPS, MPC, GST, RBE, report.
    """
    params = {"type": notification_type}
    if start_date: params["startDate"] = start_date
    if end_date: params["endDate"] = end_date
    
    url = f"{NASA_API_BASE}/DONKI/notifications"
    data = await make_nasa_request(url, params)

    if not data: 
        return "Could not retrieve DONKI notifications due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Notifications API. URL: {data.get('url')}"

    try:
        # Ensure data is a list
        if not isinstance(data, list):
            logger.error(f"Unexpected non-list response from Notifications API: {data}")
            return "Received unexpected data format from Notifications API."
            
        # Format notifications results
        if not data: 
            return "No notifications for the specified period and type."
            
        result = [f"Notifications found: {len(data)}"]
        display_limit = 10
        count = 0
        for notification in data:
            if count >= display_limit: 
                result.append(f"n... and {len(data) - display_limit} more notifications.")
                break
            result.append(f"nID: {notification.get('messageID', 'Unknown')}")
            result.append(f"Type: {notification.get('messageType', 'Unknown')}")
            result.append(f"Issue Time: {notification.get('messageIssueTime', 'Unknown')}")
            result.append(f"Header: {notification.get('messageHeader', 'N/A')}")
            # Body can be long, maybe truncate
            body = notification.get('messageBody', 'N/A')
            result.append(f"Body: {body[:200]}{'...' if len(body) > 200 else ''}") 
            result.append("-" * 40)
            count += 1
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Notifications data: {str(e)}")
        return f"Error processing notifications: {str(e)}"

# ---------------------- Earth ----------------------

@mcp.tool()
async def get_earth_imagery(lat: float, lon: float, date: str = None, dim: float = 0.025, cloud_score: bool = False) -> str:
    """Get Earth imagery from Landsat 8 satellite.
    
    Args:
        lat: Latitude.
        lon: Longitude.
        date: Image date in YYYY-MM-DD format. If not specified, the most recent image is used.
        dim: Width and height of the image in degrees (0.025 degrees is approximately 2.7 km).
        cloud_score: Calculate the percentage of the image covered by clouds (currently not available).
    """
    params = {
        "lat": lat,
        "lon": lon,
        "dim": dim
    }
    
    if date:
        params["date"] = date
    # cloud_score parameter seems deprecated or unavailable based on docs
    # if cloud_score:
    #     params["cloud_score"] = "True"
    
    url = f"{NASA_API_BASE}/planetary/earth/imagery"
    data = await make_nasa_request(url, params)
    
    if not data:
        return "Could not retrieve Earth imagery due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        # Handle specific case where API returns error message instead of image/JSON
        if isinstance(data.get("details"), str) and "No Landsat 8 imagery available" in data["details"]:
             return f"No Landsat 8 imagery available for the specified location and date (Lat: {lat}, Lon: {lon}, Date: {date or 'latest'})."
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    
    # Handle binary content
    if isinstance(data, dict) and data.get("binary_content"):
        # The API returned the image directly
        return f"Received image data directly ({data.get('content_type')}). Cannot display image content, but the image is available at the requested URL: {data.get('url')}"

    # If it's not binary, it should be JSON containing the URL
    try:
        result = [
            f"Earth image metadata for coordinates: Lat {lat}, Lon {lon}",
            f"Date: {data.get('date', 'Unknown')}",
            f"ID: {data.get('id', 'Unknown')}",
            f"Image URL: {data.get('url', 'Not available')}" # This URL should point to the image
        ]
        
        # Cloud score might be present in JSON even if binary isn't returned
        if 'cloud_score' in data and data['cloud_score'] is not None: # Check for None explicitly
            result.append(f"Cloud score: {data.get('cloud_score')}")
        else:
            result.append("Cloud score: Not available")

        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Earth Imagery JSON data: {str(e)}")
        return f"Error processing Earth imagery data: {str(e)}"

@mcp.tool()
async def get_earth_assets(lat: float, lon: float, date: str, dim: float = 0.025) -> str:
    """Get information about available imagery assets for a specific location and date.
    
    Args:
        lat: Latitude.
        lon: Longitude.
        date: Date in YYYY-MM-DD format.
        dim: Width and height of the image in degrees (0.025 degrees is approximately 2.7 km).
    """
    params = {
        "lat": lat,
        "lon": lon,
        "date": date,
        "dim": dim
    }
    
    url = f"{NASA_API_BASE}/planetary/earth/assets"
    # This endpoint is expected to return JSON based on docs
    data = await make_nasa_request(url, params)
    
    if not data:
        return "Could not retrieve Earth asset data due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
         # Handle specific case where API returns error message
        if isinstance(data.get("details"), str) and "No Landsat 8 assets found" in data["details"]:
             return f"No Landsat 8 assets found for the specified location and date range (Lat: {lat}, Lon: {lon}, Date: {date})."
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Earth Assets API. URL: {data.get('url')}"

    try:
        # The structure might have changed, docs mention 'results' array now?
        # Let's assume the old structure for now based on previous code
        # If 'results' is the key for a list: assets = data.get('results', [])
        # If it's a single result: assets = [data] if data else []
        
        # Based on the docs example, it seems to return a single object with 'id' and 'dataset'
        # Let's refine based on the example query structure
        
        asset_id = data.get('id')
        asset_dataset = data.get('dataset')
        asset_date = data.get('date', 'Unknown').split('T')[0] # Extract date part
        
        if not asset_id:
             # Check if response is like {'count': 0, 'results': []}
             if data.get('count') == 0 and isinstance(data.get('results'), list):
                 return f"No Landsat 8 assets found for the specified location and date range (Lat: {lat}, Lon: {lon}, Date: {date})."
             else:
                 logger.warning(f"Unexpected JSON structure from Earth Assets API: {data}")
                 return "No asset ID found in the response."

        result = [
            f"Asset found for coordinates: Lat {lat}, Lon {lon}",
            f"Date (closest): {asset_date}",
            f"ID: {asset_id}",
            f"Dataset: {asset_dataset}"
            # The API doesn't seem to return a direct URL here anymore based on docs
        ]
        
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Earth Assets data: {str(e)}")
        return f"Error processing asset data: {str(e)}"

# ---------------------- EPIC (Earth Polychromatic Imaging Camera) ----------------------

@mcp.tool()
async def get_epic_imagery(collection: str = "natural") -> str:
    """Get images from the EPIC (Earth Polychromatic Imaging Camera).
    
    Args:
        collection: Collection type. Options: natural, enhanced.
    """
    if collection not in ["natural", "enhanced"]:
        return "Invalid collection. Available options: natural, enhanced."
    
    # Use the 'images' endpoint to get the latest images
    api_path = f"/EPIC/api/{collection}/images"
    
    url = f"{NASA_API_BASE}{api_path}"
    data = await make_nasa_request(url)
    
    if not data: 
        return f"Could not retrieve EPIC images for latest date due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict):
        if "error" in data:
            return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
        if data.get("binary_content"):
            return f"Received unexpected binary content from EPIC API. URL: {data.get('url')}"
    
    # Ensure data is a list
    if not isinstance(data, list):
        logger.error(f"Unexpected non-list response from EPIC API: {data}")
        return "Received unexpected data format from EPIC API."

    try:
        if not data:  # Empty list
            return f"No EPIC images available for the most recent date."
        
        result = [f"EPIC images found: {len(data)}"]
        display_limit = 10
        count = 0
        
        for image_meta in data:
            if count >= display_limit:
                result.append(f"n... and {len(data) - display_limit} more images.")
                break

            image_date_time = image_meta.get('date', 'Unknown')
            image_identifier = image_meta.get('identifier', 'Unknown') # Use identifier if available
            image_name = image_meta.get('image', 'Unknown') # Base name like epic_1b_... 
            
            # Build image URL
            if image_date_time != 'Unknown' and image_name != 'Unknown':
                try:
                    # Extract date parts for URL path
                    dt_obj = datetime.strptime(image_date_time, '%Y-%m-%d %H:%M:%S')
                    year, month, day = dt_obj.strftime('%Y'), dt_obj.strftime('%m'), dt_obj.strftime('%d')
                    # Construct archive URL
                    archive_url = f"https://api.nasa.gov/EPIC/archive/{collection}/{year}/{month}/{day}/png/{image_name}.png"
                    # Add API key for direct access
                    image_url_with_key = f"{archive_url}?api_key={API_KEY}"
                except ValueError:
                    logger.warning(f"Could not parse date {image_date_time} for EPIC image URL construction.")
                    image_url_with_key = "URL construction failed"
            else:
                image_url_with_key = "URL not available"

            result.append(f"nIdentifier: {image_identifier}")
            result.append(f"Date/Time: {image_date_time}")
            result.append(f"Caption: {image_meta.get('caption', 'No caption')}")
            result.append(f"Image Name: {image_name}")
            result.append(f"Archive URL: {image_url_with_key}")
            
            # Coordinates
            coords = image_meta.get('centroid_coordinates', {})
            if coords:
                result.append(f"Centroid Coordinates: Lat {coords.get('lat', 'N/A')}, Lon {coords.get('lon', 'N/A')}")
            
            result.append("-" * 40)
            count += 1
            
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing EPIC image data: {str(e)}")
        return f"Error processing EPIC image data: {str(e)}"

@mcp.tool()
async def get_epic_imagery_by_date(date: str, collection: str = "natural") -> str:
    """Get images from the EPIC (Earth Polychromatic Imaging Camera) for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format.
        collection: Collection type. Options: natural, enhanced.
    """
    if collection not in ["natural", "enhanced"]:
        return "Invalid collection. Available options: natural, enhanced."
    
    # Use the 'date' endpoint to get images for a specific date
    api_path = f"/EPIC/api/{collection}/date/{date}"
    
    url = f"{NASA_API_BASE}{api_path}"
    data = await make_nasa_request(url)
    
    if not data: 
        return f"Could not retrieve EPIC images for date {date} due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict):
        if "error" in data:
            return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
        if data.get("binary_content"):
            return f"Received unexpected binary content from EPIC API. URL: {data.get('url')}"
    
    # Ensure data is a list
    if not isinstance(data, list):
        logger.error(f"Unexpected non-list response from EPIC API: {data}")
        return "Received unexpected data format from EPIC API."

    try:
        if not data:  # Empty list
            return f"No EPIC images available for the specified date ({date})."
        
        result = [f"EPIC images found for date {date}: {len(data)}"]
        display_limit = 10
        count = 0
        
        for image_meta in data:
            if count >= display_limit:
                result.append(f"n... and {len(data) - display_limit} more images.")
                break

            image_date_time = image_meta.get('date', 'Unknown')
            image_identifier = image_meta.get('identifier', 'Unknown') # Use identifier if available
            image_name = image_meta.get('image', 'Unknown') # Base name like epic_1b_... 
            
            # Build image URL
            if image_date_time != 'Unknown' and image_name != 'Unknown':
                try:
                    # Extract date parts for URL path
                    dt_obj = datetime.strptime(image_date_time, '%Y-%m-%d %H:%M:%S')
                    year, month, day = dt_obj.strftime('%Y'), dt_obj.strftime('%m'), dt_obj.strftime('%d')
                    # Construct archive URL
                    archive_url = f"https://api.nasa.gov/EPIC/archive/{collection}/{year}/{month}/{day}/png/{image_name}.png"
                    # Add API key for direct access
                    image_url_with_key = f"{archive_url}?api_key={API_KEY}"
                except ValueError:
                    logger.warning(f"Could not parse date {image_date_time} for EPIC image URL construction.")
                    image_url_with_key = "URL construction failed"
            else:
                image_url_with_key = "URL not available"

            result.append(f"nIdentifier: {image_identifier}")
            result.append(f"Date/Time: {image_date_time}")
            result.append(f"Caption: {image_meta.get('caption', 'No caption')}")
            result.append(f"Image Name: {image_name}")
            result.append(f"Archive URL: {image_url_with_key}")
            
            # Coordinates
            coords = image_meta.get('centroid_coordinates', {})
            if coords:
                result.append(f"Centroid Coordinates: Lat {coords.get('lat', 'N/A')}, Lon {coords.get('lon', 'N/A')}")
            
            result.append("-" * 40)
            count += 1
            
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing EPIC image data: {str(e)}")
        return f"Error processing EPIC image data: {str(e)}"

@mcp.tool()
async def get_epic_dates(collection: str = "natural") -> str:
    """Get available dates for EPIC images.
    
    Args:
        collection: Collection type. Options: natural, enhanced.
    """
    if collection not in ["natural", "enhanced"]:
        return "Invalid collection. Available options: natural, enhanced."
    
    url = f"{NASA_API_BASE}/EPIC/api/{collection}/all"
    data = await make_nasa_request(url)
    
    if not data: 
        return f"Could not retrieve available dates for EPIC {collection} collection due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict):
        if "error" in data:
            return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
        if data.get("binary_content"):
            return f"Received unexpected binary content from EPIC Dates API. URL: {data.get('url')}"
    
    # Ensure data is a list
    if not isinstance(data, list):
        logger.error(f"Unexpected non-list response from EPIC Dates API: {data}")
        return "Received unexpected data format from EPIC Dates API."

    try:
        if not data:  # Empty list
            return f"No dates available for EPIC images from the {collection} collection."
        
        # Data is a list of objects like {'date': 'YYYY-MM-DD HH:MM:SS'}
        # Extract unique dates (YYYY-MM-DD part)
        unique_dates = sorted(list(set(item.get('date', '').split(' ')[0] for item in data if item.get('date'))))
        
        result = [f"Available dates for EPIC {collection} images: {len(unique_dates)}"]
        
        # Show dates in groups of 10 per line
        for i in range(0, len(unique_dates), 10):
            result.append(", ".join(unique_dates[i:i+10]))
        
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing available dates for EPIC images: {str(e)}")
        return f"Error processing available dates for EPIC images: {str(e)}"

# ---------------------- Exoplanet ----------------------

@mcp.tool()
async def get_exoplanet_data(query: str = None, table: str = "exoplanets", format: str = "json") -> str:
    """Get data from NASA's Exoplanet Archive.
    
    Args:
        query: Specific query to filter results using Exoplanet Archive syntax. Example: "pl_orbper > 300 and pl_rade < 2"
        table: Table to query. Common options: exoplanets (confirmed planets), cumulative (Kepler Objects of Interest), koi (subset of cumulative), tce (Threshold Crossing Events).
        format: Output format. Options: json, csv, xml, ipac. Default: json.
    """
    base_url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI"
    
    params = {
        "table": table,
        "format": format
    }
    
    if query:
        # Basic validation/sanitization could be added here if needed
        params["where"] = query
    
    # The exoplanet API doesn't use api.nasa.gov, so no NASA API key needed
    # It also might return non-JSON formats directly
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Requesting Exoplanet data: {base_url} with params: {params}")
            response = await client.get(base_url, params=params, timeout=60.0) # Increased timeout for potentially large queries
            response.raise_for_status()
            
            content_type = response.headers.get("Content-Type", "").lower()

            # Handle different formats
            if format == "json" and "application/json" in content_type:
                try:
                    data = response.json()
                except json.JSONDecodeError as json_err:
                    logger.error(f"Exoplanet JSON decode error: {json_err}")
                    return f"Error: Failed to decode JSON response from Exoplanet Archive. Response text: {response.text[:500]}"
            elif format != "json" and ("text/" in content_type or "application/xml" in content_type or "application/csv" in content_type):
                 # Return raw text for non-JSON formats, limited length
                 text_response = response.text
                 limit = 2000 # Limit output size
                 if len(text_response) > limit:
                     return f"Received {format.upper()} data (truncated):n{text_response[:limit]}n... (response truncated)"
                 else:
                     return f"Received {format.upper()} data:n{text_response}"
            else:
                # Unexpected content type for the requested format
                logger.warning(f"Exoplanet API returned unexpected content type '{content_type}' for format '{format}'. URL: {response.url}")
                return f"Error: Exoplanet Archive returned unexpected content type '{content_type}'. Response text: {response.text[:500]}"

            # Process JSON data
            if not isinstance(data, list):
                 logger.error(f"Unexpected non-list JSON response from Exoplanet Archive: {data}")
                 return "Received unexpected JSON data format from Exoplanet Archive."
            
            if not data:
                return "No exoplanet data found for the specified query."
            
            result = []
            total_found = len(data)
            display_limit = 10 
            
            if total_found > display_limit:
                result.append(f"Found {total_found} entries. Showing the first {display_limit}:")
                data_to_display = data[:display_limit]
            else:
                result.append(f"Found {total_found} entries:")
                data_to_display = data
            
            for entry in data_to_display:
                # Dynamically display available fields (up to a limit)
                entry_details = []
                max_fields = 8
                fields_shown = 0
                for key, value in entry.items():
                    if fields_shown >= max_fields:
                        entry_details.append("  ... (more fields exist)")
                        break
                    # Simple display, skip null/empty values if desired
                    if value is not None and value != "": 
                        entry_details.append(f"  {key}: {value}")
                        fields_shown += 1
                
                if entry_details:
                    result.append("n" + "n".join(entry_details))
                    result.append("-" * 40)
                else:
                    # Handle case where entry might be empty or only has nulls
                    result.append(f"nEntry found, but no displayable data (ID might be {entry.get('id', 'N/A')}).")
                    result.append("-" * 40)

            return "n".join(result)
        
        except httpx.HTTPStatusError as http_err:
            logger.error(f"Exoplanet API HTTP error: {http_err} - {http_err.response.status_code}")
            return f"Error: Exoplanet Archive returned HTTP status {http_err.response.status_code}. Response: {http_err.response.text[:500]}"
        except httpx.RequestError as req_err:
            logger.error(f"Exoplanet API request error: {req_err}")
            return f"Error: Failed to connect to Exoplanet Archive. {str(req_err)}"
        except Exception as e:
            logger.error(f"Error processing Exoplanet data: {str(e)}")
            return f"Error processing exoplanet data: {str(e)}"

# ---------------------- Mars Rover Photos ----------------------

# Define valid rovers and their cameras
ROVER_CAMERAS = {
    "curiosity": ["FHAZ", "RHAZ", "MAST", "CHEMCAM", "MAHLI", "MARDI", "NAVCAM"],
    "opportunity": ["FHAZ", "RHAZ", "NAVCAM", "PANCAM", "MINITES"],
    "spirit": ["FHAZ", "RHAZ", "NAVCAM", "PANCAM", "MINITES"]
}

@mcp.tool()
async def get_mars_rover_photos(rover_name: str, sol: int = None, earth_date: str = None, camera: str = None, page: int = 1) -> str:
    """Get photos from a Mars rover (Curiosity, Opportunity, Spirit).
    Specify either sol (Martian day) or earth_date (YYYY-MM-DD), but not both.
    
    Args:
        rover_name: Name of the rover (curiosity, opportunity, spirit).
        sol: Martian sol (day number, starting from landing). Use if not using earth_date.
        earth_date: Earth date in YYYY-MM-DD format. Use if not using sol.
        camera: Filter by camera abbreviation (e.g., FHAZ, RHAZ, MAST, NAVCAM, PANCAM). See documentation for full list per rover.
        page: Page number for results (25 photos per page).
    """
    rover_name = rover_name.lower()
    if rover_name not in ROVER_CAMERAS:
        return f"Invalid rover name. Available rovers: {', '.join(ROVER_CAMERAS.keys())}"
    
    if sol is not None and earth_date is not None:
        return "Error: Specify either sol or earth_date, but not both."
    if sol is None and earth_date is None:
        return "Error: Specify either sol or earth_date."
        
    params = {"page": page}
    if sol is not None:
        params["sol"] = sol
    if earth_date is not None:
        params["earth_date"] = earth_date
        
    if camera:
        camera = camera.upper()
        if camera not in ROVER_CAMERAS[rover_name]:
            return f"Invalid camera '{camera}' for rover '{rover_name}'. Available cameras: {', '.join(ROVER_CAMERAS[rover_name])}"
        params["camera"] = camera
        
    url = f"{NASA_API_BASE}/mars-photos/api/v1/rovers/{rover_name}/photos"
    data = await make_nasa_request(url, params)
    
    if not data:
        return f"Could not retrieve Mars Rover photos for {rover_name} due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Mars Rover Photos API. URL: {data.get('url')}"
    
    # The response should be a dictionary containing a 'photos' list
    if not isinstance(data, dict) or "photos" not in data:
        logger.error(f"Unexpected response format from Mars Rover Photos API: {data}")
        return "Received unexpected data format from Mars Rover Photos API."

    try:
        photos = data.get("photos", [])
        if not photos:
            query_details = f"sol={sol}" if sol is not None else f"earth_date={earth_date}"
            if camera: query_details += f", camera={camera}"
            return f"No photos found for rover '{rover_name}' with criteria: {query_details}, page {page}."
        
        result = [f"Mars Rover Photos for '{rover_name}' (Page {page}): {len(photos)} found on this page."]
        display_limit = 10 # Limit display per page in the result string
        count = 0
        
        for photo in photos:
            if count >= display_limit:
                result.append(f"n... and {len(photos) - display_limit} more photos on this page.")
                break
                
            result.append(f"nPhoto ID: {photo.get('id', 'Unknown')}")
            result.append(f"Sol: {photo.get('sol', 'Unknown')}")
            result.append(f"Earth Date: {photo.get('earth_date', 'Unknown')}")
            result.append(f"Camera: {photo.get('camera', {}).get('name', 'Unknown')} ({photo.get('camera', {}).get('full_name', 'N/A')})")
            result.append(f"Image URL: {photo.get('img_src', 'Not available')}")
            result.append(f"Rover: {photo.get('rover', {}).get('name', 'Unknown')} (Status: {photo.get('rover', {}).get('status', 'N/A')}) ")
            result.append("-" * 40)
            count += 1
            
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Mars Rover Photos data: {str(e)}")
        return f"Error processing Mars Rover Photos data: {str(e)}"

@mcp.tool()
async def get_mars_rover_manifest(rover_name: str) -> str:
    """Get the mission manifest for a Mars rover (Curiosity, Opportunity, Spirit).
    Provides mission details like landing/launch dates, status, max sol/date, total photos, and photo counts per sol.
    
    Args:
        rover_name: Name of the rover (curiosity, opportunity, spirit).
    """
    rover_name = rover_name.lower()
    if rover_name not in ROVER_CAMERAS:
        return f"Invalid rover name. Available rovers: {', '.join(ROVER_CAMERAS.keys())}"
        
    url = f"{NASA_API_BASE}/mars-photos/api/v1/manifests/{rover_name}"
    data = await make_nasa_request(url)
    
    if not data:
        return f"Could not retrieve mission manifest for {rover_name} due to a connection error."
    
    # Check for error response (must be a dictionary)
    if isinstance(data, dict) and "error" in data:
        return f"API Error: {data.get('error')} - Details: {data.get('details', 'N/A')}"
    if isinstance(data, dict) and data.get("binary_content"):
        return f"Received unexpected binary content from Mars Rover Manifest API. URL: {data.get('url')}"
    
    # Response should be a dictionary containing 'photo_manifest'
    if not isinstance(data, dict) or "photo_manifest" not in data:
        logger.error(f"Unexpected response format from Mars Rover Manifest API: {data}")
        return "Received unexpected data format from Mars Rover Manifest API."

    try:
        manifest = data.get("photo_manifest", {})
        result = [
            f"Mission Manifest for Rover: {manifest.get('name', 'Unknown')}",
            f"Status: {manifest.get('status', 'Unknown')}",
            f"Launch Date: {manifest.get('launch_date', 'Unknown')}",
            f"Landing Date: {manifest.get('landing_date', 'Unknown')}",
            f"Max Sol: {manifest.get('max_sol', 'Unknown')}",
            f"Max Earth Date: {manifest.get('max_date', 'Unknown')}",
            f"Total Photos: {manifest.get('total_photos', 'Unknown')}",
            "nPhoto Summary per Sol (showing latest 5 sols with photos):"
        ]
        
        photos_per_sol = manifest.get('photos', [])
        # Sort by sol descending to show latest first
        photos_per_sol_sorted = sorted(photos_per_sol, key=lambda x: x.get('sol', -1), reverse=True)
        
        display_limit = 5
        count = 0
        for sol_info in photos_per_sol_sorted:
            if count >= display_limit:
                result.append(f"n... and {len(photos_per_sol) - display_limit} more sols with photos.")
                break
            result.append(f"  Sol {sol_info.get('sol', 'N/A')}: {sol_info.get('total_photos', 0)} photos")
            result.append(f"    Cameras: {', '.join(sol_info.get('cameras', []))}")
            count += 1
            
        return "n".join(result)
    except Exception as e:
        logger.error(f"Error processing Mars Rover Manifest data: {str(e)}")
        return f"Error processing Mars Rover Manifest data: {str(e)}"


# Main function
def main():
    """Start the mcp server"""
    mcp.run()

if __name__ == "__main__":
    mcp.run(transport='stdio')