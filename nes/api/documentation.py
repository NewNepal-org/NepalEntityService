"""Documentation rendering module for nes API.

This module handles rendering Markdown documentation files as HTML
and serving them through the API.
"""

import os
from pathlib import Path
from typing import Optional

import markdown
from fastapi import HTTPException
from fastapi.responses import HTMLResponse

# Get the project root directory (where docs/ is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
SPECS_DIR = PROJECT_ROOT / ".kiro" / "specs"
TEMPLATE_PATH = DOCS_DIR / "templates" / "documentation.html"


def load_template() -> str:
    """Load the HTML template for documentation pages."""
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback minimal template if file not found
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
</head>
<body>
    {{ content }}
</body>
</html>"""


def render_markdown_file(page_name: str) -> str:
    """Render a Markdown file to HTML.

    Args:
        page_name: Name of the page (without .md extension)

    Returns:
        Rendered HTML content

    Raises:
        HTTPException: If the file is not found or cannot be read
    """
    # Security: Prevent directory traversal with ..
    if ".." in page_name:
        raise HTTPException(status_code=404, detail="Page not found")

    # Construct file path
    if page_name == "":
        # Root path serves index.md
        file_path = DOCS_DIR / "index.md"
        page_title = "Home"
    elif page_name.startswith("specs/"):
        # Handle specs from .kiro/specs/
        spec_path = page_name[6:]  # Remove "specs/" prefix
        file_path = SPECS_DIR / f"{spec_path}.md"
        # Convert path to Title Case for page title
        page_title = spec_path.replace("/", " - ").replace("-", " ").title()
    else:
        file_path = DOCS_DIR / f"{page_name}.md"
        # Convert kebab-case to Title Case for page title
        page_title = page_name.replace("-", " ").title()

    # Check if file exists
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Page not found")

    # Security: Ensure the file is within docs or specs directory
    try:
        file_path = file_path.resolve()
        docs_resolved = str(DOCS_DIR.resolve())
        specs_resolved = str(SPECS_DIR.resolve())
        file_resolved = str(file_path)
        
        if not (file_resolved.startswith(docs_resolved) or file_resolved.startswith(specs_resolved)):
            raise HTTPException(status_code=404, detail="Page not found")
    except Exception:
        raise HTTPException(status_code=404, detail="Page not found")

    # Read and render markdown
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        # Convert markdown to HTML with extensions
        html_content = markdown.markdown(
            markdown_content,
            extensions=[
                "fenced_code",  # For code blocks with ```
                "tables",  # For tables
                "nl2br",  # Convert newlines to <br>
                "sane_lists",  # Better list handling
                "toc",  # Table of contents
                "pymdownx.superfences",  # Enhanced fenced code blocks with mermaid support
            ],
            extension_configs={
                "pymdownx.superfences": {
                    "custom_fences": [
                        {
                            "name": "mermaid",
                            "class": "mermaid",
                            "format": lambda source, language, css_class, options, md, **kwargs: f'<div class="mermaid">\n{source}\n</div>',
                        }
                    ]
                }
            },
        )

        # Load template and inject content
        template = load_template()
        rendered_html = template.replace("{{ content }}", html_content)
        rendered_html = rendered_html.replace("{{ title }}", page_title)

        return rendered_html

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Page not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rendering page: {str(e)}")


def render_404_page() -> str:
    """Render a 404 error page.

    Returns:
        HTML content for 404 page
    """
    template = load_template()

    error_content = """
    <div class="error-page">
        <h1>404</h1>
        <p>Page not found</p>
        <p>The documentation page you're looking for doesn't exist.</p>
        <div>
            <a href="/">Home</a>
            <a href="/consumers/getting-started">Getting Started</a>
            <a href="/consumers/api-guide">API Guide</a>
            <a href="/docs">OpenAPI Docs</a>
        </div>
    </div>
    """

    rendered_html = template.replace("{{ content }}", error_content)
    rendered_html = rendered_html.replace("{{ title }}", "404 - Page Not Found")

    return rendered_html


async def serve_documentation(page: str = "") -> HTMLResponse:
    """Serve a documentation page.

    Args:
        page: Page name (empty string for index)

    Returns:
        HTMLResponse with rendered documentation
    """
    try:
        html_content = render_markdown_file(page)
        return HTMLResponse(content=html_content, status_code=200)
    except HTTPException as e:
        if e.status_code == 404:
            html_content = render_404_page()
            return HTMLResponse(content=html_content, status_code=404)
        raise
