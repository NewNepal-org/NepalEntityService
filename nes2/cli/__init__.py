"""CLI tools for Nepal Entity Service v2."""

import sys


def dev():
    """Run the development server with auto-reload."""
    import uvicorn
    
    print("Starting Nepal Entity Service v2 development server...")
    print("Documentation will be available at: http://localhost:8195/")
    print("API endpoints will be available at: http://localhost:8195/api/")
    print("OpenAPI docs will be available at: http://localhost:8195/docs")
    print("\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "nes2.api.app:app",
        host="127.0.0.1",
        port=8195,
        reload=True,
        log_level="info"
    )


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Nepal Entity Service v2 CLI")
        print("\nUsage:")
        print("  nes2 <command>")
        print("\nCommands:")
        print("  server    Start the development server")
        print("\nFor development server, you can also use: nes2-dev")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "server":
        dev()
    else:
        print(f"Unknown command: {command}")
        print("Run 'nes2' without arguments to see available commands")
        sys.exit(1)
