import requests
import logging
import json
from typing import Optional, Dict, Any
from . import config # Use relative import within the package

logger = logging.getLogger(__name__)

def log_to_file(msg: str) -> None:
    """Logs messages to a file for debugging purposes."""
    with open('temporary_debug_file.txt', "a") as log_file:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {msg}\n")

def execute_nerdgraph_query(query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Executes a NerdGraph query and returns the JSON response dictionary.

    Args:
        query: The GraphQL query string.
        variables: Optional dictionary of variables for parameterized queries.

    Returns:
        A dictionary representing the JSON response from NerdGraph, including potential 'errors'.
    """
    log_to_file(f"Starting execute_nerdgraph_query with query: {query[:100]}...")
    log_to_file(f"Variables: {variables}")

    if not config.API_KEY: # Check API key again just in case
        log_to_file("Configuration error: API_KEY is not set")
        return {"errors": [{"message": "Configuration error: API_KEY is not set."}]}

    headers = {
        "Content-Type": "application/json",
        "API-Key": config.API_KEY,
        "Accept": "application/json", # Ensure we get JSON back
    }
    payload: Dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    logger.info(f"Executing NerdGraph Query:\nQuery: {query}\nVariables: {variables}")

    log_to_file(f"Prepared headers and payload for NerdGraph request")

    response = None
    try:
        # Use constants from config module
        log_to_file(f"Making POST request to {config.NERDGRAPH_URL}")
        response = requests.post(config.NERDGRAPH_URL, headers=headers, json=payload, timeout=45)
        log_to_file(f"Received response with status code: {response.status_code}")
        response.raise_for_status()
        json_response = response.json()
        log_to_file(f"Successfully parsed JSON response")
        return json_response
    except requests.exceptions.Timeout:
        error_message = "NerdGraph API request timed out."
        logger.error(error_message)
        log_to_file(f"Timeout error: {error_message}")
        return {"errors": [{"message": error_message}]}
    except requests.exceptions.RequestException as e:
        error_message = f"NerdGraph API request failed: {e}"
        # Try to get more detail from response if available
        if e.response is not None:
            error_message += f" Status Code: {e.response.status_code}. Response: {e.response.text[:500]}" # Limit response length
        logger.error(error_message)
        log_to_file(f"Request exception: {error_message}")
        return {"errors": [{"message": error_message}]}
    except json.JSONDecodeError as e_json:
        error_message = f"Failed to decode NerdGraph API JSON response: {e_json}"
        # Attempt to access response text even if JSON decoding failed
        raw_response_text = ""
        if response is not None and hasattr(response, 'text'):
            raw_response_text = response.text[:500] # Limit response length
        logger.error(error_message)
        log_to_file(f"JSON decode error: {error_message}")
        return {"errors": [{"message": error_message, "raw_response": raw_response_text}]}

def format_json_response(result: Dict[str, Any]) -> str:
    """Formats the result dictionary as a JSON string for MCP return."""
    # Handle potential GraphQL errors reported within the JSON payload
    if "errors" in result and result["errors"]: # Check if errors list is not empty
        logger.error(f"NerdGraph query returned errors: {json.dumps(result['errors'], indent=2)}")
        # Pass errors through in the JSON string
    elif "data" not in result and "errors" not in result:
         # If no 'data' and no 'errors', it might be an unexpected response format
         logger.warning(f"Warning: NerdGraph response missing 'data' and 'errors' fields: {json.dumps(result, indent=2)}")

    try:
        # Return the full result (including data and/or errors)
        return json.dumps(result, indent=2)
    except TypeError as e:
        error_message = f"Failed to serialize NerdGraph response to JSON: {e}"
        logging.error(error_message)
        # Return an error structure if serialization fails
        return json.dumps({"errors": [{"message": error_message, "original_result_type": str(type(result))}]})
