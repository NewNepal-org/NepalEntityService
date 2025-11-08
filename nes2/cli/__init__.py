"""CLI tools for Nepal Entity Service v2."""

import click
import sys


@click.group()
@click.version_option(version="2.0.0", prog_name="nes2")
def cli():
    """Nepal Entity Service v2 - Comprehensive entity management for Nepali public entities.
    
    This CLI provides tools for searching entities, managing data, running the API server,
    scraping external sources, and generating analytics reports.
    """
    pass


# Server command group
@cli.group()
def server():
    """Server management commands.
    
    Start the API server in production or development mode.
    """
    pass


@server.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8195, type=int, help='Port to bind to')
@click.option('--workers', default=1, type=int, help='Number of worker processes')
def start(host, port, workers):
    """Start the production server.
    
    Runs the API server in production mode without auto-reload.
    """
    import uvicorn
    
    click.echo(f"Starting Nepal Entity Service v2 production server...")
    click.echo(f"Documentation will be available at: http://{host}:{port}/")
    click.echo(f"API endpoints will be available at: http://{host}:{port}/api/")
    click.echo(f"OpenAPI docs will be available at: http://{host}:{port}/docs")
    click.echo(f"\nPress CTRL+C to stop the server\n")
    
    uvicorn.run(
        "nes2.api.app:app",
        host=host,
        port=port,
        workers=workers,
        log_level="info"
    )


@server.command()
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--port', default=8195, type=int, help='Port to bind to')
def dev(host, port):
    """Start the development server with auto-reload.
    
    Runs the API server in development mode with automatic reloading
    when code changes are detected.
    """
    import uvicorn
    
    click.echo(f"Starting Nepal Entity Service v2 development server...")
    click.echo(f"Documentation will be available at: http://{host}:{port}/")
    click.echo(f"API endpoints will be available at: http://{host}:{port}/api/")
    click.echo(f"OpenAPI docs will be available at: http://{host}:{port}/docs")
    click.echo(f"\nAuto-reload enabled - server will restart on code changes")
    click.echo(f"Press CTRL+C to stop the server\n")
    
    uvicorn.run(
        "nes2.api.app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )


def main():
    """Main CLI entry point."""
    cli()


# Search command group
@cli.group()
def search():
    """Search entities and relationships.
    
    Search the entity database for entities, relationships, and version history.
    """
    pass


@search.command(name='entities')
@click.argument('query', required=False)
@click.option('--type', 'entity_type', help='Filter by entity type (person, organization, location)')
@click.option('--subtype', 'sub_type', help='Filter by entity subtype')
@click.option('--limit', default=10, type=int, help='Maximum number of results')
@click.option('--offset', default=0, type=int, help='Number of results to skip')
def search_entities(query, entity_type, sub_type, limit, offset):
    """Search for entities.
    
    Search entities by text query and optional filters. If no query is provided,
    lists all entities matching the filters.
    
    Examples:
        nes2 search entities poudel
        nes2 search entities --type person
        nes2 search entities ram --type person --limit 5
    """
    from nes2.config import Config
    import asyncio
    
    # Initialize database
    Config.initialize_database()
    search_service = Config.get_search_service()
    
    # Perform search
    async def do_search():
        results = await search_service.search_entities(
            query=query,
            entity_type=entity_type,
            sub_type=sub_type,
            limit=limit,
            offset=offset
        )
        return results
    
    results = asyncio.run(do_search())
    
    if not results:
        click.echo("No entities found.")
        return
    
    click.echo(f"\nFound {len(results)} entities:\n")
    for entity in results:
        # Get primary name
        primary_name = next(
            (n for n in entity.names if n.kind.value == 'PRIMARY'),
            entity.names[0] if entity.names else None
        )
        
        if primary_name:
            name_str = primary_name.en.full if primary_name.en else primary_name.ne.full if primary_name.ne else "Unknown"
        else:
            name_str = "Unknown"
        
        click.echo(f"  {entity.id}")
        click.echo(f"    Name: {name_str}")
        click.echo(f"    Type: {entity.type}/{entity.sub_type if entity.sub_type else 'N/A'}")
        click.echo(f"    Version: {entity.version_summary.version_number}")
        click.echo()


@search.command(name='relationships')
@click.option('--type', 'relationship_type', help='Filter by relationship type')
@click.option('--source', 'source_entity_id', help='Filter by source entity ID')
@click.option('--target', 'target_entity_id', help='Filter by target entity ID')
@click.option('--limit', default=10, type=int, help='Maximum number of results')
@click.option('--offset', default=0, type=int, help='Number of results to skip')
def search_relationships(relationship_type, source_entity_id, target_entity_id, limit, offset):
    """Search for relationships.
    
    Search relationships by type, source entity, or target entity.
    
    Examples:
        nes2 search relationships --type MEMBER_OF
        nes2 search relationships --source entity:person/ram-chandra-poudel
    """
    from nes2.config import Config
    import asyncio
    
    # Initialize database
    Config.initialize_database()
    search_service = Config.get_search_service()
    
    # Perform search
    async def do_search():
        results = await search_service.search_relationships(
            relationship_type=relationship_type,
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            limit=limit,
            offset=offset
        )
        return results
    
    results = asyncio.run(do_search())
    
    if not results:
        click.echo("No relationships found.")
        return
    
    click.echo(f"\nFound {len(results)} relationships:\n")
    for rel in results:
        click.echo(f"  {rel.id}")
        click.echo(f"    Type: {rel.type}")
        click.echo(f"    Source: {rel.source_entity_id}")
        click.echo(f"    Target: {rel.target_entity_id}")
        if rel.start_date:
            click.echo(f"    Start: {rel.start_date}")
        if rel.end_date:
            click.echo(f"    End: {rel.end_date}")
        click.echo()


@cli.command()
@click.argument('entity_id')
@click.option('--json', 'output_json', is_flag=True, help='Output in JSON format')
def show(entity_id, output_json):
    """Show detailed information about an entity.
    
    Display complete entity information including names, identifiers, and attributes.
    
    Examples:
        nes2 show entity:person/ram-chandra-poudel
        nes2 show entity:person/ram-chandra-poudel --json
    """
    from nes2.config import Config
    import asyncio
    import json
    
    # Initialize database
    Config.initialize_database()
    db = Config.get_database()
    
    # Get entity
    async def get_entity():
        return await db.get_entity(entity_id)
    
    entity = asyncio.run(get_entity())
    
    if not entity:
        click.echo(f"Error: Entity '{entity_id}' not found.", err=True)
        raise click.Abort()
    
    if output_json:
        # Output as JSON
        click.echo(json.dumps(entity.model_dump(mode='json'), indent=2))
    else:
        # Output human-readable format
        click.echo(f"\nEntity: {entity.id}\n")
        click.echo(f"Type: {entity.type}/{entity.sub_type if entity.sub_type else 'N/A'}")
        click.echo(f"Slug: {entity.slug}")
        click.echo(f"\nNames:")
        for name in entity.names:
            click.echo(f"  {name.kind.value}:")
            if name.en:
                click.echo(f"    English: {name.en.full}")
            if name.ne:
                click.echo(f"    Nepali: {name.ne.full}")
        
        if entity.identifiers:
            click.echo(f"\nIdentifiers:")
            for ident in entity.identifiers:
                click.echo(f"  {ident.scheme}: {ident.value}")
        
        if entity.attributes:
            click.echo(f"\nAttributes:")
            for key, value in entity.attributes.items():
                click.echo(f"  {key}: {value}")
        
        click.echo(f"\nVersion: {entity.version_summary.version_number}")
        click.echo(f"Created: {entity.version_summary.created_at}")
        click.echo(f"Actor: {entity.version_summary.actor.slug}")
        click.echo()


@cli.command()
@click.argument('entity_id')
@click.option('--limit', default=10, type=int, help='Maximum number of versions')
def versions(entity_id, limit):
    """Show version history for an entity.
    
    Display the complete version history for an entity or relationship.
    
    Examples:
        nes2 versions entity:person/ram-chandra-poudel
        nes2 versions entity:person/ram-chandra-poudel --limit 5
    """
    from nes2.config import Config
    import asyncio
    
    # Initialize database
    Config.initialize_database()
    db = Config.get_database()
    
    # Get versions
    async def get_versions():
        return await db.list_versions_by_entity(
            entity_or_relationship_id=entity_id,
            limit=limit,
            order='desc'
        )
    
    versions_list = asyncio.run(get_versions())
    
    if not versions_list:
        click.echo(f"No versions found for '{entity_id}'.")
        return
    
    click.echo(f"\nVersion history for {entity_id}:\n")
    for version in versions_list:
        click.echo(f"  Version {version.version_number}")
        click.echo(f"    Created: {version.created_at}")
        click.echo(f"    Actor: {version.actor.slug}")
        if version.change_description:
            click.echo(f"    Description: {version.change_description}")
        click.echo()
