# server.py
import os
from fastmcp import FastMCP

# Import feature modules
from .features import common, entities, apm, synthetics, alerts

# --- FastMCP Server Initialization ---
# Dependencies are defined here, but execution relies on fastmcp CLI handling them
# unless run directly with `python server.py` (not recommended for this setup).
mcp = FastMCP(
    "New Relic NerdGraph MCP Server",
    dependencies=["requests"] # Core dependency needed by client.py
)

# --- Register Features ---
# Call the register function from each feature module
print("Registering common features...")
common.register(mcp)
print("Registering entity features...")
entities.register(mcp)
print("Registering APM features...")
apm.register(mcp)
print("Registering Synthetics features...")
synthetics.register(mcp)
print("Registering Alerts features...")
alerts.register(mcp)

print("Registering performance debugging guide prompt...")
# --- Register Performance Debugging Guide Prompt ---
@mcp.prompt("nerdgraph-performance-guide")
def nerdgraph_performance_debugging_guide():
    """
    Comprehensive guide for using New Relic's NerdGraph API to debug application performance issues.

    This prompt provides detailed examples and workflows for:
    - Identifying slow applications and bottlenecks
    - Entity-based performance analysis
    - NRQL queries for deep-dive investigations
    - Distributed tracing analysis
    - Common debugging workflows
    - Best practices and troubleshooting tips
    """
    try:
        import os
        # Get the root directory of the project
        current_dir = os.path.dirname(__file__)  # features directory
        parent_dir = os.path.dirname(current_dir)  # mcp_server_newrelic directory
        root_dir = os.path.dirname(parent_dir)  # project root
        guide_path = os.path.join(root_dir, 'nerdgraph-performance-debugging-guide.md')

        with open(guide_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError as e:
        return ""

print("Feature registration complete.")

# --- Entry point function for console script ---
def main():
    """Main entry point for the console script."""
    mcp.run()

# --- Main execution block (for info and potential direct run debugging) ---
if __name__ == "__main__":
    # This block is primarily for informational purposes when the script is run directly.
    # The recommended way to run is: `fastmcp run server.py:mcp`
    # Direct execution (`python server.py`) does not automatically handle dependencies
    # listed in the FastMCP constructor.
    print("\n--- New Relic MCP Server ---")
    # Check for required config (already checked in config.py, but good to double-check here)
    try:
        import config
        if not config.API_KEY:
             print("ERROR: NEW_RELIC_API_KEY environment variable is not set.")
        if not config.ACCOUNT_ID:
            print("WARNING: NEW_RELIC_ACCOUNT_ID environment variable is not set. Some features require it.")
    except ImportError:
         print("ERROR: Could not import config.py")
    except Exception as e:
         print(f"ERROR loading configuration: {e}")


    print("\nThis script defines the MCP server instance.")
    print("To run the server with dependency management, use the command:")
    print("  fastmcp run server.py:mcp")
    print("\nEnsure NEW_RELIC_API_KEY and NEW_RELIC_ACCOUNT_ID are set in your environment.")

    # You could potentially add code here to start the server directly using uvicorn
    # for development/debugging, but `fastmcp run` is the intended method.
    # Example (requires `pip install uvicorn`):
    # import uvicorn
    # print("\nAttempting to start server directly with uvicorn (for debugging)...")
    # try:
    #     uvicorn.run(mcp.app, host="127.0.0.1", port=8000) # mcp.app exposes the ASGI app
    # except Exception as e:
    #     print(f"Failed to start uvicorn: {e}")
