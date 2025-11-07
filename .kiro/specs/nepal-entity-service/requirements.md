# Requirements Document

## Introduction

The Nepal Entity Service is a comprehensive Python package designed to manage Nepali public entities (persons, organizations, and locations). The system serves as the foundation for the Nepal Public Accountability Portal, providing structured data management, versioning, and relationship tracking for entities in Nepal's political and administrative landscape.

The entity service hosts a public API that allows anyone to get the entity, relationship, and other information from the system. Besides, the entity will leverage web scraping capabilities assisted with GenAI/LLM to ensure data completeness and accuracy.

## Glossary

- **Entity**: A public person, organization, location in Nepal's political/administrative system.
- **Entity_Database**: A database storing entity/relationship/other information with versioning support. Currently we provide a file system-based adapter.
- **Nepal_Entity_Service** and **NES**: Core service that loads the entity database and exposes retrieval endpoints. The APIs will be read-only.
- **NES API**: FastAPI web service providing entity retrieval endpoints.
- **Accountability_Portal**: Public-facing web platform for transparency and accountability
- **Entity_Type**: Classification of entities (person, organization, location, etc.)
- **Entity_SubType**: Specific classification within entity types (political_party, government_body, etc.).
- **Version_System**: Audit trail system tracking changes to entities and relationships over time
- **Relationship_System**: System managing connections between entities.
- **Scraping_Tools**: ML-powered tools for building entity databases from external source, using various providers including AWS, Google Cloud/Vertex AI, and OpenAI.

## Requirements

### Requirement 1

**User Story:** As a civic tech developer, I want to access comprehensive entity data through a RESTful API, so that I can build accountability applications for Nepali citizens.

#### Acceptance Criteria

1. WHEN a developer requests entity data via API, THE Nepal_Entity_Service SHALL return structured entity information with proper HTTP status codes
2. THE Nepal_Entity_Service SHALL support filtering initially by entity type, subtype, and custom attributes, and later using powerful search algorithm.
3. THE Nepal_Entity_Service SHALL provide pagination with configurable limits.
4. THE Nepal_Entity_Service SHALL return entities in standardized JSON format with complete metadata
5. THE Nepal_Entity_Service SHALL support CORS for cross-origin requests from web applications
6. [Extensive Goal] The Nepal_Entity_Service SHALL also allow the user to retrive appropriate information they need via a GraphQL API.
6. THE Nepal_Entity_Service SHALL use the highest code quality and ensure that rigorous tests are run (including code quality checks, CI/CD, black/flake8/isort/code coverage/unit, component and e2e tests).
7. THE Nepal_Entity_Service SHALL provide a code and service documentation and host it alongside the API.
8. THE Nepal_Entity_Service SHALL track API usage enabling metric emissions at different levels to track opportunities for future enhancements.
9. THE Nepal_Entity_Service SHALL expose a health check API.

### Requirement 2

**User Story:** As a data maintainer, I want to track all changes to entity information with full audit trails, so that I can ensure data integrity and transparency.

#### Acceptance Criteria

1. WHEN an entity is modified, THE Version_System SHALL create a new version with timestamp and change metadata (including when, who changed it, for what reason)
2. THE Version_System SHALL preserve complete snapshots of entity states for historical reference
3. WHEN a version is requested, THE Nepal_Entity_Service SHALL return the exact entity state at that point in time.
4. The Version_System SHALL provide an interface that allows a data maintainer to easily update an entity or a relationship.

### Requirement 3

**User Story:** As a researcher, I want to search and filter entities by multiple criteria, so that I can find specific entities for analysis and reporting.

#### Acceptance Criteria

1. THE Nepal_Entity_Service SHALL support entity lookup by unique identifier with exact matching
2. THE Nepal_Entity_Service SHALL filter entities by type (person, organization, location) and subtype classifications
3. WHEN attribute filters are provided as JSON, THE Nepal_Entity_Service SHALL apply AND logic for multiple criteria
4. THE Nepal_Entity_Service SHALL support offset-based pagination for large result sets
5. THE Nepal_Entity_Service SHALL return consistent result ordering for reproducible queries

### Requirement 4

**User Story:** As a system integrator, I want to manage relationships between entities, so that I can represent complex organizational and political connections.

#### Acceptance Criteria

1. THE Relationship_System SHALL store directional relationships between any two entities
2. THE Relationship_System SHALL support typed relationships with descriptive labels and metadata
3. WHEN relationships are queried, THE Nepal_Entity_Service SHALL return complete relationship information including context
4. THE Relationship_System SHALL maintain relationship versioning consistent with entity versioning
5. THE Nepal_Entity_Service SHALL validate relationship integrity before storage

### Requirement 5

**User Story:** As a data curator, I want to import entity data from multiple sources using automated scraping tools, so that I can maintain comprehensive and up-to-date entity information.

#### Acceptance Criteria

1. THE Scraping_Tools SHALL extract entity information from Wikipedia, government websites, and election databases
2. THE Scraping_Tools SHALL normalize names, dates, and organizational information across Nepali and English sources
3. WHEN duplicate entities are detected, THE Scraping_Tools SHALL provide merge recommendations with confidence scores
4. THE Scraping_Tools SHALL validate extracted data against entity schema before import
5. THE Scraping_Tools SHALL maintain source attribution for all imported data

### Requirement 6

**User Story:** As a package consumer, I want flexible installation options with optional dependencies, so that I can use only the components I need for my specific use case.

#### Acceptance Criteria

1. THE Nepal_Entity_Service SHALL provide core models and utilities without optional dependencies
2. WHERE API functionality is needed, THE Nepal_Entity_Service SHALL install FastAPI and related dependencies
3. WHERE scraping functionality is needed, THE Nepal_Entity_Service SHALL install ML and web scraping dependencies
4. THE Nepal_Entity_Service SHALL support full installation with all optional features
5. THE Nepal_Entity_Service SHALL maintain backward compatibility across minor version updates

### Requirement 7

**User Story:** As a Nepali citizen, I want entity information to use authentic Nepali names and cultural context, so that the system remains relevant to Nepal's political and social structures.

#### Acceptance Criteria

1. THE Nepal_Entity_Service SHALL support multilingual names with Nepali and English variants
2. THE Nepal_Entity_Service SHALL use authentic Nepali person names in examples and documentation
3. THE Nepal_Entity_Service SHALL reference actual Nepali organizations and political parties
4. THE Nepal_Entity_Service SHALL maintain location references using Nepal's administrative divisions
5. THE Nepal_Entity_Service SHALL preserve cultural context in entity classifications and relationships

### Requirement 8

**User Story:** As a system administrator, I want comprehensive data validation and error handling, so that I can maintain data quality and system reliability.

#### Acceptance Criteria

1. THE Nepal_Entity_Service SHALL validate all entity data against Pydantic schemas before storage
2. WHEN invalid data is submitted, THE Nepal_Entity_Service SHALL return descriptive error messages with field-level details
3. THE Nepal_Entity_Service SHALL enforce required fields including at least one primary name per entity
4. THE Nepal_Entity_Service SHALL validate external identifiers and URLs for proper format
5. THE Nepal_Entity_Service SHALL handle database errors gracefully with appropriate HTTP status codes


### Analytics System

**User Story:** As a researcher, I want to anlyze the Entity database for completeness, and accuracy.

#### Acceptance Criteria
1. THE Nepal_Entity_Service SHALL generate HTML/Markdown reports, and structured JSON metadata on data completeness and other statistics on the fly using CLI.
2. The Nepal_Entity_Service SHALL export the results on its documentation.