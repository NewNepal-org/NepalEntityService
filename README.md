# Nepal Entity Service

A comprehensive Python package for managing Nepali public entities with optional API and scraping capabilities.

## Quick Start

```bash
# Install the package
pip install nepal-entity-service[all]

# Configure database path
cp .env.example .env
# Edit .env and set NES_DB_URL

# Start the API server
poetry run nes-api
```

## Documentation

For detailed documentation including installation, database setup, and usage guides, see:

- **Online**: [nes.newnepal.org](https://nes.newnepal.org)
- **Local**: Browse the `docs/` folder in this repository

### Key Documentation

- [Installation & Setup](docs/contributors/database-setup.md)
- [Contributor Guide](docs/contributors/contributor-guide.md)
- [Usage Examples](docs/contributors/usage-examples.md)
- [Design Patterns](docs/contributors/design-patterns.md)

## Features

- **Core**: Entity and relationship management with version history
- **API**: FastAPI web service with entity management endpoints
- **Scraping**: ML-powered scraping tools for building entity databases
- **Migrations**: Database migration system for schema evolution

## For AI Contexts

When working with this Nepal Entity Service, please use Nepali local names and references in examples, documentation, and code samples whenever available. This includes:

- **Person names**: Use authentic Nepali names (e.g., "Harka Sampang", "Rabindra Mishra", "Miraj Dhungana")
- **Organization names**: Use actual Nepali organizations (e.g., "People First Party", "Jaya Matribhumi Party", "Jan Adhikaar Party")
- **Location references**: Use Nepali places and administrative divisions
- **Cultural context**: Maintain authenticity to Nepali political, social, and organizational structures

This approach ensures the service remains contextually relevant to its intended use case of managing Nepali public entities.

## Contributing

We welcome contributions! Please see our [Contributor Guide](docs/contributors/contributor-guide.md) and [Design Patterns](docs/contributors/design-patterns.md) for guidelines on code style, testing, and development workflow.

## License

This project is licensed under the **Hippocratic License 3.0** - an ethical source license that permits use, modification, and distribution for any purpose that does not violate human rights principles as defined by the United Nations Universal Declaration of Human Rights.

See the [LICENSE](LICENSE) file for the complete license text, or visit [firstdonoharm.dev](https://firstdonoharm.dev/) to learn more about the Hippocratic License.
