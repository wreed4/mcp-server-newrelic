import json
import asyncio
from typing import Optional, Dict, Any
from fastmcp import FastMCP

# Import necessary functions and config from parent directory files
# Use absolute imports assuming project root is in sys.path
import client
import config

def register(mcp: FastMCP):
    """Registers common tools and resources with the FastMCP instance."""

    @mcp.tool()
    async def query_nerdgraph(nerdgraph_query: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Executes an arbitrary NerdGraph query against the New Relic API.
        Use this for queries not covered by specific tools/resources.

        Args:
            nerdgraph_query: The GraphQL query string. Can include variables defined in the 'variables' arg.
                             Example: 'query($accountId: Int!) { actor { account(id: $accountId) { name } } }'
            variables: An optional JSON dictionary of variables to pass with the query.
                       Example: {"accountId": 1234567}

        Returns:
            A JSON string representing the result of the query, including data and/or errors.
        """
        if not isinstance(nerdgraph_query, str) or not nerdgraph_query.strip():
            return json.dumps({"errors": [{"message": "Invalid or empty query provided."}]})

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(client.execute_nerdgraph_query, nerdgraph_query, variables),
                timeout=90.0
            )
            return client.format_json_response(result)
        except asyncio.TimeoutError:
            return json.dumps({"errors": [{"message": "NerdGraph query timed out after 90 seconds"}]})
        except Exception as e:
            return json.dumps({"errors": [{"message": f"Query execution failed: {str(e)}"}]})
