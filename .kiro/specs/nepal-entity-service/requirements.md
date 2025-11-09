# Requirements Document

## Introduction

The Nepal Entity Service is a comprehensive Python package designed to manage Nepali public entities (persons, organizations, and locations). The system serves as the foundation for the Nepal Public Accountability Portal, providing structured data management, versioning, and relationship tracking for entities in Nepal's political and administrative landscape.

The entity service hosts a public API that allows anyone to get the entity, relationship, and other information from the system. Besides, the entity will leverage web scraping capabilities assisted with GenAI/LLM to ensure data completeness and accuracy.

## Glossary

- **Entity**: A public person, organization, location in Nepal's political/administrative system
- **Entity_Database**: A database storing entity/relationship/other information with versioning support. Currently we provide a file system-based adapter at `nes-db/v2`
- **Nepal_Entity_Service** and **NES**: Core service that loads the entity database and exposes retrieval endpoints. The APIs will be read-only
- **NES API**: FastAPI web service providing entity retrieval endpoints
- **Publication_Service**: Central orchestration layer managing entity lifecycle, relationships, and versioning using core Pydantic models
- **Search_Service**: Read-optimized service providing entity and relationship search with filtering and pagination
- **Migration_Service**: Service orchestrating database updates through versioned migration scripts with Git-based tracking
- **Scraping_Service**: Standalone service for extracting and normalizing data from external sources using GenAI/LLM

- **Accountability_Portal**: Public-facing web platform for transparency and accountability
- **Entity_Type**: Classification of entities (person, organization, location, etc.)
- **Entity_SubType**: Specific classification within entity types (political_party, government_body, etc.)
- **Version_System**: Audit trail system tracking changes to entities and relationships over time using the Version model
- **Relationship_System**: System managing connections between entities using the Relationship model
- **Scraping_Tools**: ML-powered tools for building entity databases from external sources, using various providers including AWS, Google Cloud/Vertex AI, and OpenAI

## Requirements

### Requirement 1

**User Story:** As a civic tech developer, I want to access comprehensive entity data through a RESTful API, so that I can build accountability applications for Nepali citizens.

#### Acceptance Criteria

1. WHEN a developer requests entity data via API, THE Nepal_Entity_Service SHALL return structured entity information with proper HTTP status codes
2. THE Nepal_Entity_Service SHALL support filtering initially by entity type, subtype, and custom attributes, and later using powerful search algorithm.
3. THE Nepal_Entity_Service SHALL provide pagination with configurable limits.
4. THE Nepal_Entity_Service SHALL return entities in standardized JSON format with complete metadata
5. THE Nepal_Entity_Service SHALL support CORS for cross-origin requests from web applications
6. THE Nepal_Entity_Service SHALL use the highest code quality and ensure that rigorous tests are run (including code quality checks, CI/CD, black/flake8/isort/code coverage/unit, component and e2e tests)
7. THE Nepal_Entity_Service SHALL serve documentation at the root endpoint `/` using Markdown files
8. THE Nepal_Entity_Service SHALL provide API schema documentation using OpenAPI/Swagger at `/docs` endpoint
9. THE Nepal_Entity_Service SHALL render Markdown documentation on-the-fly without requiring a separate build step
10. THE Nepal_Entity_Service SHALL expose a health check API
11. [Future Enhancement] The Nepal_Entity_Service MAY provide a GraphQL API in addition to REST for flexible query capabilities

### Requirement 2

**User Story:** As a data maintainer, I want to track all changes to entity information with full audit trails, so that I can ensure data integrity and transparency.

#### Acceptance Criteria

1. WHEN an entity is modified, THE Version_System SHALL create a new version with timestamp and change metadata (including when, who changed it, for what reason)
2. THE Version_System SHALL preserve complete snapshots of entity states for historical reference
3. WHEN a version is requested, THE Nepal_Entity_Service SHALL return the exact entity state at that point in time
4. THE Version_System SHALL provide an interface through the Publication Service that allows a data maintainer to easily update an entity or a relationship
5. THE Version_System SHALL track author attribution for all changes with change descriptions

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


### Requirement 9

**User Story:** As a system architect, I want a modular service architecture with clear separation of concerns, so that the system is maintainable, testable, and scalable.

#### Acceptance Criteria

1. THE Nepal_Entity_Service SHALL implement a Publication Service as the central orchestration layer for write operations
2. THE Publication Service SHALL use Entity, Relationship, Version, and Author Pydantic models for consistent operations
3. THE Nepal_Entity_Service SHALL implement a Search Service as a separate read-optimized service
4. THE Search Service SHALL use the same Entity and Relationship models as the Publication Service
5. THE Nepal_Entity_Service SHALL implement a Migration Service for orchestrating database updates through versioned scripts
6. THE Migration Service SHALL use Publication and Search services for data operations
7. THE Nepal_Entity_Service SHALL implement a Scraping Service as a standalone data extraction service
8. THE Scraping Service SHALL not directly access the database but return normalized data for client processing
9. THE Nepal_Entity_Service SHALL support CLI, notebook, and API client applications that orchestrate services
10. THE Nepal_Entity_Service SHALL maintain clear service boundaries with well-defined interfaces

### Requirement 10

**User Story:** As an API consumer, I want fast read operations with sub-100ms response times, so that I can build responsive applications for end users.

#### Acceptance Criteria

1. THE Nepal_Entity_Service SHALL prioritize read-time latency reduction over write-time performance
2. THE Nepal_Entity_Service SHALL implement aggressive caching strategies for frequently accessed entities
3. THE Nepal_Entity_Service SHALL use read-optimized file organization and pre-computed indexes
4. THE Nepal_Entity_Service SHALL perform expensive operations (validation, normalization, indexing) during write operations
5. THE Nepal_Entity_Service SHALL target sub-100ms response times for entity retrieval operations
6. THE Nepal_Entity_Service SHALL support efficient pagination with pre-sorted data structures
7. THE Nepal_Entity_Service SHALL implement HTTP caching with ETags for unchanged data

### Requirement 11

**User Story:** As a data maintainer, I want to manage database evolution through versioned migration folders across two Git repositories, so that I can track, reproduce, and audit how the database content has changed over time.

#### Acceptance Criteria

1. THE Migration_System SHALL support sequential migration folders with numeric prefixes (000-initial-locations/, 001-update-location-names/) in the Service_API_Repository
2. THE Migration_System SHALL execute migrations in sequential order based on their numeric prefix
3. THE Migration_System SHALL store migration folders in the Service_API_Repository and entity data in the Database_Repository
4. WHEN a migration is executed, THE Migration_System SHALL commit changes to the Database_Repository with migration metadata in the commit message
5. THE Migration_System SHALL include author, date, entities created/updated, and duration in Git commit messages
6. THE Migration_System SHALL provide a command to list all available migrations with their metadata
7. THE Migration_System SHALL look for a main script file (migrate.py or run.py) within each migration folder to execute
8. THE Migration_System SHALL manage the Database_Repository as a Git submodule within the Service_API_Repository

### Requirement 12

**User Story:** As a migration author, I want to organize migrations as folders with supporting files and metadata, so that I can include data files, documentation, and authorship information together in one place.

#### Acceptance Criteria

1. THE Migration_System SHALL support migration folders containing multiple files and subdirectories
2. THE Migration_System SHALL allow migrations to include CSV files, Excel spreadsheets, JSON files, and other data formats
3. THE Migration_System SHALL require migrations to include README.md files documenting the migration purpose and approach
4. THE Migration_System SHALL require migration scripts to define AUTHOR, DATE, and DESCRIPTION metadata constants
5. THE Migration_System SHALL allow migration scripts to reference files within their migration folder using relative paths
6. THE Migration_System SHALL provide the migration folder path to the migration script at runtime
7. THE Migration_System SHALL use migration metadata for Git commit messages when changes are committed to the Database_Repository

### Requirement 13

**User Story:** As a migration script author, I want to write migration scripts that can create, update, and delete entities and relationships, so that I can make any necessary data changes to the database.

#### Acceptance Criteria

1. THE Migration_System SHALL provide a migration script API for creating new entities through the Publication_Service
2. THE Migration_System SHALL provide a migration script API for updating existing entities through the Publication_Service
3. THE Migration_System SHALL provide a migration script API for creating and updating relationships through the Publication_Service
4. THE Migration_System SHALL provide a migration script API for querying existing entities and relationships
5. THE Migration_System SHALL ensure all migration operations go through the Publication_Service for proper versioning and validation
6. THE Migration_System SHALL provide helper functions for reading CSV, Excel, and JSON files from migration folders

### Requirement 14

**User Story:** As a migration script author, I want to access existing services in my migrations, so that I can leverage scraping, search, and publication capabilities for data processing.

#### Acceptance Criteria

1. THE Migration_System SHALL provide migration scripts with access to the Scraping_Service for data extraction and normalization
2. THE Migration_System SHALL provide migration scripts with access to the Search_Service for querying existing entities
3. THE Migration_System SHALL provide migration scripts with access to the Publication_Service for creating and updating entities
4. THE Migration_System SHALL handle service failures gracefully with error reporting

### Requirement 15

**User Story:** As a community member, I want to contribute migrations via GitHub pull requests, so that I can propose data improvements that maintainers can review and merge.

#### Acceptance Criteria

1. THE Migration_System SHALL store migrations in a dedicated directory (migrations/) in the Service_API_Repository
2. THE Migration_System SHALL enforce naming conventions for migration folders (NNN-descriptive-name/ format)
3. THE Migration_System SHALL provide documentation and templates for creating migration folders
4. THE Migration_System SHALL provide a template migration folder structure for contributors to copy

### Requirement 16

**User Story:** As a maintainer, I want to execute migrations and commit changes to Git, so that I can apply community contributions to the database.

#### Acceptance Criteria

1. THE Migration_System SHALL provide a command to execute a specific migration by name
2. THE Migration_System SHALL provide a command to execute all migrations in sequential order
3. WHEN a migration completes successfully, THE Migration_System SHALL commit changes to the Database_Repository with formatted commit message
4. THE Migration_System SHALL push commits to the remote Database_Repository after successful migration execution
5. WHEN a migration fails, THE Migration_System SHALL NOT commit changes to the Database_Repository
6. THE Migration_System SHALL log detailed error information including stack traces for failed migrations
7. WHEN a migration is executed, THE Migration_System SHALL persist the resulting data snapshot in the Database_Repository so that re-running the migration becomes deterministic
8. THE Migration_System SHALL prevent re-execution of already-applied migrations by checking persisted snapshots in the Database_Repository

### Requirement 17

**User Story:** As a data maintainer, I want to track the provenance of all data changes through Git history, so that I can understand the source and reasoning behind every modification.

#### Acceptance Criteria

1. WHEN a migration creates or updates an entity, THE Publication_Service SHALL record the migration script name as the author
2. THE Migration_System SHALL preserve contributor attribution from the migration script metadata in Git commits
3. THE Migration_System SHALL link version records to the specific migration that created them through author attribution
4. THE Migration_System SHALL maintain a complete audit trail through Git history in the Database_Repository
5. THE Migration_System SHALL format Git commit messages with migration metadata including author, date, and statistics

### Requirement 18

**User Story:** As a system administrator, I want to efficiently manage the large Database Repository containing 100k-1M files, so that Git operations remain performant and practical.

#### Acceptance Criteria

1. THE Migration_System SHALL support batch commits when migrations create or modify large numbers of files
2. THE Migration_System SHALL commit changes in batches of up to 1000 files per commit when appropriate
3. THE Migration_System SHALL provide documentation for using shallow clones and sparse checkout with the Database_Repository
4. THE Migration_System SHALL configure Git settings optimized for large repositories (core.preloadindex, core.fscache, gc.auto)
5. THE Migration_System SHALL handle Git push operations for large commits with appropriate timeouts

