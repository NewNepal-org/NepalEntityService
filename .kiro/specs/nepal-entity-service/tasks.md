# Implementation Plan - Complete V2 Rewrite (TDD Approach)

> **IMPORTANT**: This is a complete rewrite in a new `nes` package with breaking changes. The existing `nes` package will remain untouched during development and will be deleted after v2 is complete. The new database will use `nes-db/v2` instead of `entity-db`.

> **TDD METHODOLOGY**: All implementation tasks follow Red-Green-Refactor. Write failing tests first (Red), implement minimal code to pass (Green), then refactor for quality (Refactor).

> Another note: We use poetry for venv-based development.

## Phase 0: Project Setup

- [x] 0. Initialize nes package structure
  - [x] 0.1 Create nes package foundation
    - Create `nes/` directory with `__init__.py`
    - Create subdirectories: `core/`, `database/`, `services/`, `api/`, `cli/`, `scraping/`
    - Set up `pyproject.toml` for nes package (separate from nes v1)
    - Configure package metadata, dependencies, and entry points
    - _Requirements: Package structure_

  - [x] 0.2 Set up testing infrastructure
    - Create `tests/` directory for nes tests
    - Set up pytest configuration for nes
    - Create test fixtures with authentic Nepali data
    - Set up test utilities and helpers
    - _Requirements: Testing infrastructure, TDD foundation_

  - [x] 0.3 Set up core models package
    - Write tests for Entity, Relationship, Version, and base models FIRST
    - Create `nes/core/models/` with `__init__.py`
    - Create model files: `entity.py`, `relationship.py`, `version.py`, `base.py`
    - Copy and refactor models from v1 with breaking changes as needed
    - Update imports and package references to nes
    - Ensure all model tests pass
    - _Requirements: 1.1, 1.4, 7.1, 7.2, 8.1, 8.3_

  - [x] 0.4 Set up core utilities
    - Write tests for ID generation and validation FIRST
    - Create `nes/core/identifiers/` for ID generation and validation
    - Create `nes/core/constraints.py` for validation rules
    - Create `nes/core/utils/` for shared utilities
    - Copy and refactor utilities from v1 with improvements
    - Ensure all utility tests pass
    - _Requirements: Core infrastructure_

  - [x] 0.5 Configure database path
    - Update all database initialization to use `nes-db/v2` path
    - Ensure complete separation from v1's `entity-db`
    - Add configuration for database path override
    - _Requirements: Database isolation_

## Phase 1: Cultural and Multilingual Foundation

- [x] 1. Enhance Nepali context throughout the system
  - [x] 1.1 Create authentic Nepali test data
    - Create test fixtures with real Nepali politician names
    - Add authentic Nepali political party data
    - Include proper Nepali administrative divisions (provinces, districts, municipalities)
    - Add Nepali government body examples
    - Use real Nepali locations and constituencies
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 1.2 Implement Devanagari script handling
    - Write tests for Devanagari validation FIRST
    - Implement proper Devanagari script validation
    - Add romanization support for Nepali names
    - Implement transliteration utilities (Devanagari ↔ Roman)
    - Add Devanagari-aware string comparison
    - Ensure all Devanagari tests pass
    - _Requirements: 7.1_

  - [x] 1.3 Implement multilingual name handling
    - Write tests for multilingual name operations FIRST
    - Implement cross-language name matching
    - Add phonetic search for Nepali names
    - Implement fuzzy matching for transliterations
    - Add name normalization for Nepali and English variants
    - Ensure all multilingual tests pass
    - _Requirements: 7.1_

  - [x] 1.4 Add cultural context to entity types
    - Update entity subtypes with Nepali-specific classifications
    - Add proper Nepali political structure support
    - Implement Nepali administrative hierarchy
    - Add Nepali government body types
    - Document cultural context in code comments
    - _Requirements: 7.2, 7.3, 7.4_

## Phase 2: Database Layer Implementation (TDD)

- [-] 2. Build FileDatabase v2 with enhanced capabilities
  - [x] 2.1 Write database foundation tests FIRST
    - Write tests for EntityDatabase abstract interface
    - Write tests for FileDatabase CRUD operations
    - Write tests for entity storage and retrieval
    - Write tests for relationship storage and retrieval
    - Write tests for version storage and retrieval
    - Write tests for author storage and retrieval
    - _Requirements: Database abstraction, TDD_

  - [x] 2.2 Implement database foundation (Green)
    - Create `nes/database/` directory with `__init__.py`
    - Create `nes/database/entity_database.py` with abstract EntityDatabase class
    - Create `nes/database/file_database.py` with FileDatabase implementation
    - Implement minimal CRUD operations to pass tests
    - Use `nes-db/v2` as default database path
    - Ensure all foundation tests pass
    - _Requirements: Database abstraction_

  - [x] 2.3 Write search capability tests FIRST
    - Write tests for text-based entity search
    - Write tests for case-insensitive matching
    - Write tests for multilingual search (Nepali and English)
    - Write tests for type and subtype filtering
    - Write tests for attribute-based filtering
    - Write tests for search result ranking
    - _Requirements: 1.2, 3.2, TDD_

  - [x] 2.4 Implement search capabilities (Green)
    - Implement `search_entities()` method with text matching
    - Add case-insensitive search across name fields
    - Implement multilingual search support
    - Add search result ranking by relevance
    - Ensure all search tests pass
    - _Requirements: 1.2, 3.2_

  - [x] 2.5 Write relationship querying tests FIRST
    - Write tests for listing relationships by entity
    - Write tests for listing relationships by type
    - Write tests for temporal filtering
    - Write tests for bidirectional queries
    - _Requirements: 4.3, TDD_

  - [x] 2.6 Implement relationship querying (Green)
    - Add `list_relationships_by_entity()` method
    - Implement `list_relationships_by_type()` method
    - Add temporal filtering for relationships
    - Implement bidirectional relationship queries
    - Ensure all relationship query tests pass
    - _Requirements: 4.3_

  - [x] 2.7 Write version listing tests FIRST
    - Write tests for listing versions by entity
    - Write tests for listing versions by relationship
    - Write tests for version filtering
    - Write tests for efficient version retrieval
    - _Requirements: 2.3, TDD_

  - [x] 2.8 Implement enhanced version listing (Green)
    - Update `list_versions()` to require entity_id or relationship_id
    - Add filtering by entity/relationship
    - Implement efficient version retrieval
    - Ensure all version listing tests pass
    - _Requirements: 2.3_

  - [x] 2.9 Write caching tests FIRST
    - Write tests for cache hit/miss behavior
    - Write tests for cache TTL expiration
    - Write tests for cache invalidation on updates
    - Write tests for cache warming
    - _Requirements: TDD_

  - [x] 2.10 Implement caching layer (Green)
    - Implement in-memory cache with TTL
    - Add cache warming for frequently accessed entities
    - Implement cache invalidation on updates
    - Add cache hit/miss metrics
    - Ensure all caching tests pass
    - _Requirements: Performance_

  - [x] 2.11 Write file I/O optimization tests FIRST
    - Write tests for batch read operations
    - Write tests for concurrent read support
    - Write tests for directory traversal optimization
    - Write tests for index file usage
    - _Requirements: TDD_

  - [x] 2.12 Implement file I/O optimizations (Green)
    - Implement batch read operations
    - Add concurrent read support
    - Optimize directory traversal for listing
    - Add index files for common queries
    - Ensure all I/O optimization tests pass
    - _Requirements: Performance_

  - [x] 2.13 Refactor database layer
    - Refactor for code quality and maintainability
    - Optimize performance bottlenecks
    - Improve error handling
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

## Phase 3: Service Layer Architecture (TDD)

- [x] 3. Implement Publication Service
  - [x] 3.1 Write Publication Service tests FIRST
    - Write tests for entity creation with automatic versioning
    - Write tests for entity updates with version creation
    - Write tests for entity retrieval
    - Write tests for entity deletion (hard delete)
    - Write tests for relationship creation with versioning
    - Write tests for relationship updates
    - Write tests for relationship deletion
    - Write tests for bidirectional consistency
    - Write tests for coordinated operations
    - Write tests for rollback scenarios
    - Write tests for business rule enforcement
    - _Requirements: 9.1, 9.2, 2.4, TDD_

  - [x] 3.2 Implement Publication Service foundation (Green)
    - Create `nes/services/publication/` directory with `__init__.py`
    - Create `nes/services/publication/service.py` with PublicationService class
    - Initialize with database instance
    - Set up service coordination logic
    - Ensure foundation tests pass
    - _Requirements: 9.1, 9.2, 2.4_

  - [x] 3.3 Implement entity business logic (Green)
    - Add entity validation and constraint enforcement
    - Implement name and identifier management logic
    - Add entity-specific business rules
    - Implement entity CRUD operations with automatic versioning
    - Ensure all entity tests pass
    - _Requirements: 9.1, 9.2, 8.1, 2.1_

  - [x] 3.4 Implement relationship business logic (Green)
    - Add relationship validation and constraint enforcement
    - Implement relationship type validation
    - Add temporal relationship handling (start/end dates)
    - Implement bidirectional consistency checking
    - Add entity existence validation for relationships
    - Ensure all relationship tests pass
    - _Requirements: 9.2, 4.1, 4.2, 4.5_

  - [x] 3.5 Implement version and author management (Green)
    - Add snapshot creation and storage logic
    - Implement change description management
    - Add attribution tracking
    - Implement version retrieval by entity/relationship
    - Add author tracking and validation
    - Ensure all version/author tests pass
    - _Requirements: 2.1, 2.2, 2.3, 9.1_

  - [x] 3.6 Implement coordinated operations (Green)
    - Implement `update_entity_with_relationships()` for atomic updates
    - Add batch operation support for multiple entities
    - Implement rollback mechanisms for failed operations
    - Add cross-entity validation
    - Ensure all coordinated operation tests pass
    - _Requirements: 2.4, 4.5, 9.1, 9.2_

  - [x] 3.7 Refactor Publication Service
    - Refactor for code quality and maintainability
    - Extract common patterns into helper methods
    - Improve error handling and logging
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

- [x] 4. Implement Search Service
  - [x] 4.1 Write Search Service tests FIRST
    - Write tests for entity text search
    - Write tests for multilingual search (Nepali and English)
    - Write tests for type and subtype filtering
    - Write tests for attribute-based filtering
    - Write tests for pagination
    - Write tests for relationship search
    - Write tests for temporal filtering
    - Write tests for version retrieval
    - _Requirements: 9.3, 3.1, 3.2, TDD_

  - [x] 4.2 Implement Search Service foundation (Green)
    - Create `nes/services/search/` directory with `__init__.py`
    - Create `nes/services/search/service.py` with SearchService class
    - Initialize with database instance
    - Implement basic query interface
    - Ensure foundation tests pass
    - _Requirements: 9.3, 3.1, 3.2_

  - [x] 4.3 Implement entity search capabilities (Green)
    - Add `search_entities()` method with text query support
    - Implement case-insensitive substring matching
    - Add support for Nepali (Devanagari) and English text search
    - Implement type and subtype filtering
    - Add attribute-based filtering with AND logic
    - Implement pagination (limit/offset)
    - Ensure all entity search tests pass
    - _Requirements: 1.2, 3.1, 3.2, 3.3, 3.4, 7.1_

  - [x] 4.4 Implement relationship and version search (Green)
    - Add `search_relationships()` method
    - Implement filtering by relationship type
    - Add source/target entity filtering
    - Implement temporal filtering (date ranges)
    - Add `get_entity_versions()` method for listing versions
    - Add `get_relationship_versions()` method
    - Ensure all relationship/version search tests pass
    - _Requirements: 4.3, 2.3_

  - [x] 4.5 Refactor Search Service
    - Refactor for code quality and maintainability
    - Optimize search performance
    - Improve error handling
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

- [-] 5. Implement Scraping Service
  - [x] 5.1 Write Scraping Service tests FIRST
    - Write tests for Wikipedia extraction
    - Write tests for data normalization
    - Write tests for translation capabilities
    - Write tests for relationship extraction
    - Write tests for external source search
    - _Requirements: 9.5, 5.1, TDD_

  - [x] 5.2 Implement Scraping Service foundation (Green)
    - Create `nes/services/scraping/` directory with `__init__.py`
    - Create `nes/services/scraping/service.py` with ScrapingService class
    - Initialize with LLM providers and web scraping tools
    - Implement pluggable extractor architecture
    - Ensure foundation tests pass
    - _Requirements: 9.5, 5.1_

  - [x] 5.3 Implement Web Scraper component (Green)
    - Create `nes/services/scraping/web_scraper.py` with WebScraper class
    - Add multi-source extraction (Wikipedia, government sites, news)
    - Implement rate limiting and respectful scraping
    - Add error handling and retry logic
    - Implement HTML parsing and content extraction
    - Ensure web scraper tests pass
    - _Requirements: 5.1_

  - [x] 5.4 Implement Translation component (Green)
    - Create `nes/services/scraping/translation.py` with translation utilities
    - Add Nepali to English translation
    - Add English to Nepali translation
    - Implement transliteration handling
    - Add language detection
    - Ensure translation tests pass
    - _Requirements: 5.1, 7.1_

  - [x] 5.5 Implement Data Normalization component (Green)
    - Create `nes/services/scraping/normalization.py` with normalization utilities
    - Add LLM-powered data structuring
    - Implement extraction of structured data from unstructured text
    - Add relationship discovery from narrative text
    - Implement name disambiguation and standardization
    - Add data quality assessment
    - Ensure normalization tests pass
    - _Requirements: 5.2, 5.3_

  - [x] 5.6 Implement scraping service methods (Green)
    - Implement `extract_from_wikipedia()` method in ScrapingService
    - Add `normalize_person_data()` method
    - Implement `extract_relationships()` method
    - Add `translate()` method
    - Implement `search_external_sources()` method
    - Ensure all scraping service tests pass
    - _Requirements: 5.1, 5.2_

  - [x] 5.7 Refactor Scraping Service
    - Refactor for code quality and maintainability
    - Optimize scraping performance
    - Improve error handling and retry logic
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

## Phase 4: API Layer Implementation (TDD)

- [x] 6. Build API v2 with service architecture
  - [x] 6.1 Write API tests FIRST
    - Write tests for all entity endpoints
    - Write tests for relationship endpoints
    - Write tests for version endpoints
    - Write tests for schema endpoints
    - Write tests for health check endpoint
    - Write tests for error handling
    - Write tests for CORS functionality
    - Write tests for search functionality
    - Write tests for pagination
    - _Requirements: 1.1, 1.5, TDD_

  - [x] 6.2 Implement API foundation (Green)
    - Create `nes/api/` directory with `__init__.py`
    - Create `nes/api/app.py` with FastAPI application
    - Create `nes/api/routes/` for endpoint route files
    - Create `nes/api/responses.py` for response models
    - Set up CORS, error handling, and middleware
    - Configure API to use nes services
    - Ensure foundation tests pass
    - _Requirements: 1.1, 1.5_

  - [x] 6.3 Implement service dependencies (Green)
    - Create `get_search_service()` dependency
    - Create `get_publication_service()` dependency (for future write endpoints)
    - Create `get_database()` dependency
    - Set up dependency injection for all services
    - Ensure dependency tests pass
    - _Requirements: 1.1, 9.3_

  - [x] 6.4 Implement entities endpoint (Green)
    - Create `/api/entities` endpoint using SearchService
    - Implement search query parameter using `search_entities()`
    - Add filtering by type, subtype, and attributes
    - Implement pagination with limit/offset
    - Add version-specific entity retrieval
    - Ensure all entity endpoint tests pass
    - _Requirements: 1.1, 1.2, 3.2_

  - [x] 6.5 Implement relationship and version endpoints (Green)
    - Create `/api/entities/{id}/relationships` endpoint
    - Use SearchService for relationship queries
    - Add filtering by relationship type
    - Implement pagination and temporal filtering
    - Create `/api/versions/{id}` endpoint for listing versions
    - Ensure all relationship/version endpoint tests pass
    - _Requirements: 4.3, 2.3_

  - [x] 6.6 Implement schema and health endpoints (Green)
    - Create `/api/schemas` endpoint for entity type discovery
    - Return available entity types and subtypes
    - Implement `/api/health` endpoint
    - Check database connectivity and service status
    - Ensure all schema/health endpoint tests pass
    - _Requirements: 1.1, 1.9_

  - [x] 6.7 Implement error handling (Green)
    - Create standardized error response models
    - Implement field-level error details
    - Add proper HTTP status code mapping
    - Improve validation error messages
    - Add error logging
    - Ensure all error handling tests pass
    - _Requirements: 8.1, 8.2, 8.5_

  - [x] 6.8 Refactor API layer
    - Refactor for code quality and maintainability
    - Optimize endpoint performance
    - Improve error messages
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

- [x] 7. Implement documentation hosting
  - [x] 7.1 Write documentation tests FIRST
    - Write tests for documentation rendering
    - Write tests for page navigation
    - Write tests for 404 handling
    - Write tests for markdown parsing
    - _Requirements: 1.7, TDD_

  - [x] 7.2 Create documentation structure (Green)
    - Create `docs/` directory
    - Write `docs/index.md` as landing page
    - Create `docs/getting-started.md`
    - Write `docs/architecture.md`
    - Create `docs/api-reference.md`
    - Write `docs/data-models.md`
    - Create `docs/examples.md`
    - _Requirements: 1.7, 1.8_

  - [x] 7.3 Implement documentation rendering (Green)
    - Add markdown rendering dependency
    - Create HTML template for documentation
    - Implement root endpoint `/` to serve documentation
    - Add documentation page routing `/{page}`
    - Implement 404 handling for missing pages
    - Ensure all documentation tests pass
    - _Requirements: 1.7, 1.9_

  - [x] 7.4 Update API configuration (Green)
    - Keep API endpoints under `/api` prefix
    - Keep OpenAPI docs at `/docs`
    - Ensure documentation is served at root
    - Update CORS configuration if needed
    - _Requirements: 1.7, 1.8_

## Phase 5: CLI and Tooling (TDD)

- [-] 8. Implement comprehensive CLI
  - [x] 8.1 Write CLI tests FIRST
    - Write tests for all command groups
    - Write tests for command arguments and options
    - Write tests for output formatting
    - Write tests for error handling
    - _Requirements: 6.1, 15.1, TDD_

  - [x] 8.2 Implement CLI foundation (Green)
    - Create `nes/cli.py` with Click framework
    - Set up command groups structure
    - Configure entry points in pyproject.toml for `nes` command
    - Ensure foundation tests pass
    - _Requirements: 6.1, 15.1_

  - [x] 8.3 Implement server commands (Green)
    - Add `nes server start` command for production
    - Add `nes server dev` command for development
    - Implement proper help text and documentation
    - Ensure server command tests pass
    - _Requirements: 6.1, 15.1_

  - [-] 8.4 Implement search commands (Green)
    - Add `nes search <query>` command
    - Implement `nes search entities` with filters
    - Add `nes search relationships` command
    - Implement `nes show <entity-id>` for entity details
    - Add `nes versions <entity-id>` for version history
    - Ensure search command tests pass
    - _Requirements: 3.1, 3.2, 15.1_

  - [ ] 8.5 Implement scraping commands (Green)
    - Add `nes scrape wikipedia <page>` command
    - Implement `nes scrape search <query>` for external search
    - Add `nes scrape info <query>` for entity information
    - Implement preview and confirmation for imports
    - Ensure scraping command tests pass
    - _Requirements: 5.1, 15.1_

  - [ ] 8.6 Implement data management commands (Green)
    - Add `nes data import <file>` command
    - Implement `nes data export <query>` command
    - Add `nes data validate` for data quality checks
    - Implement `nes data stats` for database statistics
    - Ensure data management command tests pass
    - _Requirements: 15.1_

  - [ ] 8.7 Implement analytics commands (Green)
    - Add `nes analytics report` command
    - Implement HTML/Markdown report generation
    - Add JSON metadata export
    - Implement data completeness analysis
    - Add entity relationship graph generation
    - Ensure analytics command tests pass
    - _Requirements: 15.2_

  - [ ] 8.8 Refactor CLI
    - Refactor for code quality and maintainability
    - Improve command help text
    - Optimize command performance
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

## Phase 6: Data Maintainer Interface

- [x] 9. Create Data Maintainer Interface examples
  - [x] 9.1 Create example scripts
    - Write `examples/update_entity.py` demonstrating entity updates
    - Create `examples/create_relationship.py` for relationship creation
    - Write `examples/batch_import.py` for bulk operations
    - Create `examples/version_history.py` for version exploration
    - Update all examples to use nes package
    - Use authentic Nepali data in all examples
    - _Requirements: 2.4, 9.3_

  - [x] 9.2 Create Jupyter notebook examples
    - Create `notebooks/01_entity_management.ipynb`
    - Write `notebooks/02_relationship_management.ipynb`
    - Create `notebooks/03_data_import_workflow.ipynb`
    - Write `notebooks/04_data_quality_analysis.ipynb`
    - Update all notebooks to use nes package
    - Use authentic Nepali data in all notebooks
    - _Requirements: 9.3_

  - [x] 9.3 Write Data Maintainer documentation
    - Create `docs/data-maintainer-guide.md`
    - Document Publication Service API
    - Add code examples for common operations
    - Document best practices for data maintenance
    - Add troubleshooting guide
    - Include Nepali-specific guidance
    - _Requirements: 9.3_

## Phase 7: Advanced Features

- [x] 10. Enhance relationship system
  - [x] 10.1 Write relationship integrity tests FIRST
    - Write tests for entity existence validation
    - Write tests for circular relationship detection
    - Write tests for constraint validation
    - Write tests for integrity check CLI command
    - _Requirements: 4.5, TDD_

  - [x] 10.2 Implement relationship integrity checks (Green)
    - Implement entity existence validation
    - Add circular relationship detection
    - Create constraint validation system
    - Add integrity check CLI command
    - Ensure all integrity tests pass
    - _Requirements: 4.5_

  - [x] 10.3 Write relationship graph tests FIRST
    - Write tests for bidirectional traversal
    - Write tests for depth-limited exploration
    - Write tests for relationship path finding
    - Write tests for graph visualization
    - _Requirements: 4.3, TDD_

  - [x] 10.4 Implement relationship graph traversal (Green)
    - Add bidirectional traversal methods
    - Implement depth-limited exploration
    - Add relationship path finding
    - Create relationship graph visualization
    - Ensure all graph traversal tests pass
    - _Requirements: 4.3_

  - [x] 10.5 Refactor relationship enhancements
    - Refactor for code quality and maintainability
    - Optimize graph traversal performance
    - Improve error handling
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

- [ ] 11. Implement performance optimizations
  - [ ] 11.1 Write indexing tests FIRST
    - Write tests for entity type indexes
    - Write tests for name-based search indexes
    - Write tests for attribute indexes
    - Write tests for index rebuild command
    - _Requirements: TDD_

  - [ ] 11.2 Implement pre-computed indexes (Green)
    - Create index files for entity types
    - Add name-based search indexes
    - Implement attribute indexes
    - Add index rebuild command
    - Ensure all indexing tests pass
    - _Requirements: Performance_

  - [ ] 11.3 Write cache warming tests FIRST
    - Write tests for cache warming on startup
    - Write tests for popular entity detection
    - Write tests for cache preloading
    - _Requirements: TDD_

  - [ ] 11.4 Implement cache warming (Green)
    - Add cache warming on startup
    - Implement popular entity detection
    - Add cache preloading for common queries
    - Ensure all cache warming tests pass
    - _Requirements: Performance_

  - [ ] 11.5 Write performance benchmark tests
    - Benchmark entity retrieval latency
    - Benchmark search performance
    - Benchmark cache effectiveness
    - Create performance regression tests
    - _Requirements: Performance validation_

  - [ ] 11.6 Refactor performance optimizations
    - Refactor for code quality and maintainability
    - Optimize critical paths
    - Improve monitoring and metrics
    - Add comprehensive documentation
    - Ensure all tests still pass after refactoring
    - _Requirements: Code quality_

## Phase 8: Testing and Quality Assurance

- [ ] 12. Comprehensive end-to-end testing
  - [ ] 12.1 Write end-to-end workflow tests
    - Write tests for complete entity lifecycle
    - Write tests for data import workflows
    - Write tests for relationship management
    - Write tests for version tracking
    - Use authentic Nepali data in all tests
    - _Requirements: Testing coverage_

  - [ ] 12.2 Write data quality tests
    - Write tests for data validation
    - Write tests for constraint enforcement
    - Write tests for integrity checks
    - Write tests for error handling
    - _Requirements: 8.1, 8.2_

  - [ ] 12.3 Run full test suite
    - Run all unit tests
    - Run all integration tests
    - Run all end-to-end tests
    - Run performance benchmarks
    - Verify 100% test coverage for critical paths
    - _Requirements: Quality assurance_

  - [ ] 12.4 Fix any failing tests
    - Debug and fix any test failures
    - Improve test reliability
    - Add missing test coverage
    - Document known issues
    - _Requirements: Quality assurance_

## Phase 9: Migration and Cleanup

- [ ] 13. Data migration from v1 to v2
  - [ ] 13.1 Write migration tests FIRST
    - Write tests for data format conversion
    - Write tests for data integrity validation
    - Write tests for rollback procedures
    - _Requirements: Migration support, TDD_

  - [ ] 13.2 Implement migration script (Green)
    - Write migration script to convert entity-db to nes-db/v2
    - Handle breaking changes in data format
    - Validate migrated data
    - Create migration documentation
    - Ensure all migration tests pass
    - _Requirements: Migration support_

  - [ ] 13.3 Test migration with real data
    - Test migration with sample data
    - Verify data integrity after migration
    - Test rollback procedures
    - Document migration process
    - _Requirements: Migration validation_

- [ ] 14. Final cleanup and documentation
  - [ ] 14.1 Update project documentation
    - Update README.md for v2
    - Update USAGE_EXAMPLES.md for v2
    - Create MIGRATION.md guide
    - Update all references from nes to nes
    - Add Nepali-specific documentation
    - _Requirements: Documentation_

  - [ ] 14.2 Delete v1 package
    - Remove `nes/` directory
    - Remove v1-specific tests
    - Clean up v1 dependencies
    - Update pyproject.toml to remove v1 references
    - _Requirements: Cleanup_

  - [ ] 14.3 Rename nes to nes
    - Rename `nes/` directory to `nes/`
    - Update all imports from nes to nes
    - Update pyproject.toml package name
    - Update CLI command from nes to nes
    - Update all documentation
    - Run full test suite to verify rename
    - _Requirements: Final rename_


## Phase 10: Migration System Implementation

- [ ] 13. Set up migration infrastructure and core models
  - Create migration service package structure
  - Define Migration and MigrationResult data models
  - Implement migration folder naming conventions and validation
  - _Requirements: 11.1, 11.2, 12.1, 12.2, 12.4_

- [x] 13.1 Create migration service package
  - Create `nes/services/migration/` directory
  - Add `__init__.py` with package exports
  - _Requirements: 11.1_

- [x] 13.2 Define migration data models
  - Create `nes/services/migration/models.py`
  - Implement `Migration` dataclass with prefix, name, folder_path, script_path, metadata
  - Implement `MigrationResult` dataclass with status, duration, statistics, error
  - Implement `MigrationStatus` enum (RUNNING, COMPLETED, FAILED, SKIPPED)
  - _Requirements: 11.1, 11.2, 12.4_

- [x] 13.3 Implement migration folder validation
  - Create `nes/services/migration/validation.py`
  - Implement function to validate migration folder structure (has migrate.py, README.md)
  - Implement function to validate migration naming convention (NNN-descriptive-name)
  - Implement function to validate migration metadata (AUTHOR, DATE, DESCRIPTION)
  - _Requirements: 12.1, 12.2, 12.4, 15.2_

- [ ] 14. Implement Migration Manager for discovery and tracking
  - Implement migration discovery from migrations/ directory
  - Implement checking for persisted snapshots in Database Repository
  - Implement pending migrations detection
  - _Requirements: 11.1, 11.2, 11.4, 11.8, 16.8_

- [x] 14.1 Implement migration discovery
  - Create `nes/services/migration/manager.py`
  - Implement `MigrationManager` class with `discover_migrations()` method
  - Scan migrations/ directory for folders matching NNN-* pattern
  - Sort migrations by numeric prefix
  - Load migration metadata from script files
  - _Requirements: 11.1, 11.2, 15.1_

- [x] 14.2 Implement persisted snapshot checking
  - Implement `get_applied_migrations()` method in MigrationManager
  - Query Git log in Database Repository for migration commits
  - Parse commit messages to extract migration names
  - Cache results to avoid repeated Git queries
  - _Requirements: 11.4, 16.7, 16.8_

- [x] 14.3 Implement pending migrations detection
  - Implement `get_pending_migrations()` method in MigrationManager
  - Compare discovered migrations with applied migrations
  - Return migrations that haven't been applied yet
  - Implement `is_migration_applied()` method for single migration check
  - _Requirements: 11.2, 16.8_

- [x] 15. Implement Migration Context for script execution
  - Create thin context with service access
  - Implement file reading helpers (CSV, JSON, Excel)
  - Implement logging mechanism
  - _Requirements: 12.5, 12.6, 13.6_

- [x] 15.1 Create Migration Context class
  - Create `nes/services/migration/context.py`
  - Implement `MigrationContext` class with service references
  - Provide direct access to publication, search, scraping, and db services
  - Provide migration_dir property
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 14.1, 14.2, 14.3_

- [x] 15.2 Implement file reading helpers
  - Implement `read_csv()` method with CSV parsing
  - Implement `read_json()` method with JSON parsing
  - Implement `read_excel()` method with Excel parsing
  - Handle file not found errors gracefully
  - _Requirements: 12.5, 12.6, 13.6_

- [x] 15.3 Implement logging mechanism
  - Implement `log()` method for migration progress logging
  - Store logs in context for later retrieval
  - Print logs to console during execution
  - _Requirements: 16.6_

- [x] 16. Implement Migration Runner for execution
  - Implement migration script loading and execution
  - Implement deterministic execution (check before run)
  - Implement error handling and logging
  - _Requirements: 11.2, 13.1, 13.2, 13.3, 13.4, 13.5, 16.1, 16.5, 16.6, 16.7, 16.8_

- [x] 16.1 Create Migration Runner class
  - Create `nes/services/migration/runner.py`
  - Implement `MigrationRunner` class with service dependencies
  - Implement `create_context()` method to build MigrationContext
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 16.2 Implement migration script loading
  - Implement `_load_script()` method to dynamically import migrate.py
  - Validate script has `migrate()` function
  - Validate script has required metadata (AUTHOR, DATE, DESCRIPTION)
  - Handle syntax errors gracefully
  - _Requirements: 11.7, 12.4, 16.6_

- [x] 16.3 Implement deterministic execution
  - Implement `run_migration()` method with determinism check
  - Check if migration already applied before execution
  - Skip execution if persisted snapshot exists (return SKIPPED status)
  - Support force flag to allow re-execution
  - _Requirements: 16.1, 16.7, 16.8_

- [x] 16.4 Implement migration execution
  - Execute migration script's `migrate()` function with context
  - Track execution time
  - Capture logs from context
  - Handle all exceptions and create MigrationResult
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 16.5, 16.6_

- [x] 16.5 Implement batch migration execution
  - Implement `run_migrations()` method for multiple migrations
  - Execute migrations in sequential order
  - Skip already-applied migrations
  - Stop on first failure or continue based on flag
  - _Requirements: 11.2, 16.2_

- [x] 17. Implement Git integration for persistence
  - Implement commit creation with migration metadata
  - Implement batch commits for large migrations
  - Implement push to remote Database Repository
  - _Requirements: 11.3, 11.5, 16.3, 16.4, 16.7, 17.1, 17.2, 17.3, 17.4, 17.5, 18.1, 18.2, 18.5_

- [x] 17.1 Implement commit creation
  - Implement `commit_and_push()` method in MigrationRunner
  - Format commit message with migration metadata
  - Stage changed files in Database Repository
  - Create Git commit with formatted message
  - _Requirements: 11.3, 11.5, 16.3, 17.1, 17.2, 17.3, 17.5_

- [x] 17.2 Implement batch commits
  - Detect when migration creates more than 1000 files
  - Split commits into batches of 1000 files each
  - Create multiple commits with batch metadata
  - _Requirements: 18.1, 18.2_

- [x] 17.3 Implement push to remote
  - Push commits to remote Database Repository
  - Handle push failures gracefully
  - Use appropriate timeout for large pushes
  - _Requirements: 16.4, 18.5_

- [x] 17.4 Implement Git configuration
  - Configure Git settings for large repositories
  - Set core.preloadindex, core.fscache, gc.auto
  - _Requirements: 18.4_

- [x] 18. Implement CLI commands
  - Implement `nes migrate list` command
  - Implement `nes migrate pending` command
  - Implement `nes migrate run` command
  - Implement `nes migrate create` command
  - _Requirements: 11.6, 15.3, 15.4, 16.1, 16.2_

- [x] 18.1 Implement migrate list command
  - Create `nes/cli/migrate.py` with Click command group
  - Implement `list` command to show all migrations with status
  - Display migration metadata (author, date, description)
  - Show applied vs pending status
  - _Requirements: 11.6_

- [x] 18.2 Implement migrate pending command
  - Implement `pending` command to show only pending migrations
  - Display migration metadata
  - Show count of pending migrations
  - _Requirements: 11.6_

- [x] 18.3 Implement migrate run command
  - Implement `run` command to execute specific migration
  - Support `--all` flag to run all pending migrations
  - Support `--dry-run` flag to skip persistence
  - Support `--force` flag to allow re-execution
  - Display progress and results
  - _Requirements: 16.1, 16.2_

- [x] 18.4 Implement migrate create command
  - Implement `create` command to generate migration folder from template
  - Determine next available prefix number
  - Create migration folder with NNN-descriptive-name format
  - Copy template migrate.py with pre-filled metadata
  - Copy template README.md
  - _Requirements: 15.3, 15.4_

- [x] 19. Create migration templates
  - Create template migrate.py with documentation
  - Create template README.md with structure
  - _Requirements: 12.3, 15.3, 15.4_

- [x] 19.1 Create migrate.py template
  - Create `nes/services/migration/templates/migrate.py.template`
  - Include metadata placeholders (AUTHOR, DATE, DESCRIPTION)
  - Include comprehensive documentation of context methods
  - Include example code patterns
  - _Requirements: 12.3, 15.3_

- [x] 19.2 Create README.md template
  - Create `nes/services/migration/templates/README.md.template`
  - Include sections for Purpose, Data Sources, Changes, Dependencies, Notes
  - _Requirements: 12.3, 15.3_

- [x] 20. Implement CI/CD workflows
  - Create GitHub Actions workflow for migration preview
  - Create GitHub Actions workflow for migration persistence
  - _Requirements: 16.2, 16.3, 16.4, 17.4_

- [x] 20.1 Create migration preview workflow
  - Create `.github/workflows/migration-preview.yml`
  - Trigger on pull request to migrations/ directory
  - Execute migrations in isolated environment
  - Generate statistics (entities/relationships created)
  - Post comment on PR with statistics and logs link
  - _Requirements: 16.2, 16.3, 17.4_

- [x] 20.2 Create migration persistence workflow
  - Create `.github/workflows/migration-persistence.yml`
  - Trigger on PR merge to main branch
  - Trigger on schedule (daily at 2 AM UTC)
  - Check for pending migrations
  - Execute pending migrations
  - Commit to Database Repository
  - Push to remote
  - Update submodule reference in Service API Repository
  - _Requirements: 16.2, 16.3, 16.4, 17.4_

- [x] 21. Add documentation
  - Write contributor guide for creating migrations
  - Write maintainer guide for reviewing and executing migrations
  - Document migration system architecture
  - _Requirements: 15.3_

- [x] 21.1 Write contributor documentation
  - Create `docs/migration-contributor-guide.md`
  - Document step-by-step process for creating migrations
  - Include examples of common migration patterns
  - Document how to test migrations locally
  - _Requirements: 15.3_

- [x] 21.2 Write maintainer documentation
  - Create `docs/migration-maintainer-guide.md`
  - Document PR review process
  - Document how to execute migrations
  - Document troubleshooting common issues
  - _Requirements: 15.3_

- [x] 21.3 Write architecture documentation
  - Create `docs/migration-architecture.md`
  - Document two-repository architecture
  - Document linear migration model
  - Document determinism through persisted snapshots
  - _Requirements: 11.3, 11.8_
