"""Server entry points for Nepal Entity Service v2 API."""

PORT = 8195


def api():
    """Run the production API server."""
    import uvicorn

    uvicorn.run("nes.api.app:app", host="0.0.0.0", port=8080, log_level="info")


def dev():
    """Run the development server with auto-reload."""
    import uvicorn

    print("Starting Nepal Entity Service v2 development server...")
    print(f"Documentation will be available at: http://localhost:{PORT}/")
    print(f"API endpoints will be available at: http://localhost:{PORT}/api/")
    print(f"OpenAPI docs will be available at: http://localhost:{PORT}/docs")
    print("\nPress CTRL+C to stop the server\n")

    uvicorn.run(
        "nes.api.app:app", host="127.0.0.1", port=PORT, reload=True, log_level="info"
    )
