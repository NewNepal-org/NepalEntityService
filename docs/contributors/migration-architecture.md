# Migration System Architecture

This document describes the architecture of the Open Database Updates feature, which enables community contributions to the Nepal Entity Service through versioned migration folders. The system follows database migration patterns but applies them to data changes rather than schema changes.

## Table of Contents

1. [Overview](#overview)
2. [Two-Repository Architecture](#two-repository-architecture)
3. [Linear Migration Model](#linear-migration-model)
4. [Determinism Through Persisted Snapshots](#determinism-through-persisted-snapshots)
5. [Component Architecture](#component-architecture)
6. [Data Flow](#data-flow)
7. [Git Integration](#git-integration)
8. [Performance Considerations](#performance-considerations)
9. [Design Decisions](#design-decisions)

---

## Overview

The Open Database Updates feature introduces a migration-based system for managing data evolution in the Nepal Entity Service. This system enables community contributions through versioned migration folders that contain executable Python scripts and supporting data files.

### Key Concepts

- **Migration**: A versioned folder containing a Python script and supporting files that applies specific data changes
- **Linear Model**: Migrations execute in sequential order based on numeric prefixes
- **Determinism**: Once executed, migrations create persisted snapshots that prevent re-execution
- **Two-Repository**: Application code and data are managed in separate Git repositories
- **Git-Based Tracking**: Migration history is tracked through Git commits rather than a separate database

### Design Goals

1. **Community Contributions**: Enable anyone to propose data updates via GitHub pull requests
2. **Data Provenance**: Track the source and reasoning behind every data change
3. **Reproducibility**: Ensure database state can be recreated by replaying migrations
4. **Transparency**: Maintain complete audit trail through Git history
5. **Scalability**: Handle large databases (100k-1M files) efficiently

---

## Two-Repository Architecture

The system operates across two GitHub repositories to separate application code from data:

### Service API Repository

**Repository**: https://github.com/NewNepal-org/NepalEntityService

**Contents**:
- Application code (Python packages, API, CLI)
- Migration scripts in `migrations/` directory
- Documentation and tests
- Configuration files

**Characteristics**:
- Lightweight (~10MB)
- Fast to clone and develop
- Contains code, not data
- Contributors submit PRs here

**Structure**:
```
NepalEntityService/
├── migrations/
│   ├── 000-initial-locations/
│   │   ├── migrate.py
│   │   ├── README.md
│   │   └── locations.csv
│   ├── 001-political-parties/
│   │   ├── migrate.py
│   │   ├── README.md
│   │   └── parties.json
│   └── 002-update-names/
│       ├── migrate.py
│       └── README.md
├── nes/
│   ├── services/
│   │   └── migration/
│   │       ├── manager.py
│   │       ├── runner.py
│   │       ├── context.py
│   │       └── models.py
│   └── ...
├── nes-db/  (Git submodule)
└── ...
```

### Database Repository

**Repository**: https://github.com/NewNepal-org/NepalEntityService-database

**Contents**:
- Entity JSON files (100k-1M files)
- Relationship JSON files
- Version history files
- Author files

**Characteristics**:
- Large (~1GB+)
- Managed as Git submodule at `nes-db/`
- Modified by migration execution
- Not directly edited by contributors

**Structure**:
```
nes-db/
├── v2/
│   ├── entity/
│   │   ├── person/
│   │   │   ├── ram-chandra-poudel.json
│   │   │   ├── sher-bahadur-deuba.json
│   │   │   └── ... (100k+ files)
│   │   ├── organization/
│   │   │   └── political_party/
│   │   │       └── nepali-congress.json
│   │   └── location/
│   │       └── province/
│   │           └── bagmati.json
│   ├── relationship/
│   │   └── ... (500k+ files)
│   ├── version/
│   │   └── entity/
│   │       └── person/
│   │           └── ram-chandra-poudel/
│   │               ├── v1.json
│   │               └── v2.json
│   └── author/
│       └── ... (1k+ files)
└── README.md
```

### Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    Contributor                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         1. Create migration in Service API Repo              │
│            migrations/005-add-ministers/                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         2. Submit PR to Service API Repo                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Maintainer                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         3. Review and merge PR                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         4. Execute migration locally                         │
│            nes migrate run 005-add-ministers                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         5. Migration modifies Database Repo                  │
│            Creates/updates files in nes-db/v2/               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         6. Commit to Database Repo (persisted snapshot)      │
│            git commit -m "Migration: 005-add-ministers"      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         7. Push to Database Repo remote                      │
│            git push origin main                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         8. Update submodule in Service API Repo              │
│            git add nes-db && git commit && git push          │
└─────────────────────────────────────────────────────────────┘
```

### Design Rationale

**Separation of Concerns**:
- Application code and data are managed independently
- Service API repo remains lightweight for fast development
- Database repo can grow to millions of files without affecting service development

**Review Process**:
- Migration code is reviewed separately from data changes
- Maintainers review the logic before execution
- Data changes are the result of executing reviewed code

**Performance**:
- Developers can clone Service API repo quickly
- Database repo can use different Git strategies (shallow clones, sparse checkout)
- Large data doesn't slow down code development

**Audit Trail**:
- Git history in Database repo provides complete data evolution history
- Each migration creates a commit with detailed metadata
- Rollback is possible using standard Git operations

---

## Linear Migration Model

Migrations execute in sequential order based on numeric prefixes, similar to database schema migrations (Flyway, Alembic, Django).

### Migration Naming Convention

```
NNN-descriptive-name/
```

- **NNN**: Three-digit numeric prefix (000, 001, 002, ...)
- **descriptive-name**: Kebab-case description of the migration

**Examples**:
- `000-initial-locations`
- `001-political-parties`
- `002-update-party-leadership`
- `003-add-cabinet-ministers`

### Sequential Execution

Migrations are discovered and executed in order:

```python
# Migration Manager discovers migrations
migrations = [
    Migration(prefix=0, name="initial-locations", ...),
    Migration(prefix=1, name="political-parties", ...),
    Migration(prefix=2, name="update-party-leadership", ...),
]

# Migrations execute in order
for migration in migrations:
    if not is_applied(migration):
        execute(migration)
```

### Benefits of Linear Model

**Predictability**:
- Database state is deterministic based on which migrations have run
- No branching or merging of migration paths
- Clear progression of database evolution

**Simplicity**:
- Easy to understand and reason about
- No complex dependency resolution
- Straightforward rollback (revert commits in reverse order)

**Reproducibility**:
- Running migrations 000-005 always produces the same database state
- New environments can be bootstrapped by running all migrations
- Historical states can be recreated by running migrations up to a point

### Handling Conflicts

When multiple contributors create migrations simultaneously:

1. **First merged wins**: First PR to merge gets the next prefix number
2. **Second contributor rebases**: Updates their migration prefix to next available
3. **No conflicts**: Migrations are independent folders, no merge conflicts

**Example**:
```bash
# Contributor A creates 005-add-ministers
# Contributor B creates 005-add-parties (same prefix)

# Maintainer merges A's PR first
# B's PR now conflicts

# B updates their migration:
mv migrations/005-add-parties migrations/006-add-parties
# Update all references to 006 in migrate.py and README.md
# Push update to PR
```

---

## Determinism Through Persisted Snapshots

A key design principle is that migrations are deterministic: running a migration multiple times produces the same result (no-op after first execution).

### The Problem

Without determinism:
- Re-running migrations creates duplicate entities
- Accidental re-execution corrupts data
- Difficult to recover from failures
- Unclear which migrations have been applied

### The Solution: Persisted Snapshots

When a migration executes, the resulting data snapshot is persisted in the Database Repository through a Git commit. This commit serves as proof that the migration was applied.

**Key Concept**: The persisted snapshot IS the migration tracking mechanism. No separate tracking database is needed.

### How It Works

```python
class MigrationRunner:
    async def run_migration(self, migration: Migration, force: bool = False):
        """Execute a migration and persist the snapshot."""
        
        # 1. Check if migration already applied
        if await self.is_migration_applied(migration) and not force:
            print(f"Migration {migration.full_name} already applied, skipping")
            return MigrationResult(status=MigrationStatus.SKIPPED)
        
        # 2. Execute migration script
        context = self.create_context(migration)
        await migration.script.migrate(context)
        
        # 3. Commit changes to Database Repository (persist snapshot)
        await self.commit_and_push(migration, result)
        
        # 4. Now the migration is "applied" (snapshot exists)
        return result
    
    async def is_migration_applied(self, migration: Migration) -> bool:
        """Check if migration has been applied by looking for persisted snapshot."""
        
        # Query Git log in Database Repository
        result = subprocess.run(
            ["git", "log", "--grep=^Migration:", "--format=%s"],
            cwd=self.db_repo_path,
            capture_output=True,
            text=True
        )
        
        # Parse migration names from commit messages
        applied = []
        for line in result.stdout.split('\n'):
            if line.startswith('Migration: '):
                migration_name = line.replace('Migration: ', '').strip()
                applied.append(migration_name)
        
        # Check if this migration's snapshot exists
        return migration.full_name in applied
```

### Git Commit as Snapshot

Each migration execution creates a Git commit in the Database Repository:

```
commit abc123def456...
Author: Migration System <migrations@nepalentityservice.org>
Date: 2024-03-15 10:30:00 +0000

    Migration: 005-add-cabinet-ministers
    
    Import current cabinet ministers from official records
    
    Author: contributor@example.com
    Date: 2024-03-15
    Entities created: 25
    Relationships created: 25
    Duration: 12.3s
```

**This commit represents**:
1. **Persisted Snapshot**: The actual entity/relationship files created
2. **Tracking Record**: Proof that migration 005 was applied
3. **Audit Trail**: Who, what, when, and how many changes
4. **Rollback Point**: Can revert this commit to undo the migration

### Benefits

**Determinism**:
- Running `nes migrate run --all` multiple times is safe
- First run executes pending migrations
- Subsequent runs skip already-applied migrations (detect persisted snapshots)

**Idempotency**:
- Migrations can be written to be idempotent (check before create)
- System-level idempotency through snapshot detection
- No duplicate entities from accidental re-execution

**Data Integrity**:
- Prevents corruption from re-running migrations
- Clear separation between applied and pending migrations
- Snapshot and tracking are always in sync (they're the same thing)

**Distribution**:
- Multiple maintainers see the same applied migrations
- Pulling Database Repository updates the local view
- No central tracking database needed

**Rollback**:
- Standard Git operations work: `git revert <commit-sha>`
- Reverting a commit removes the persisted snapshot
- Migration becomes "unapplied" and can be re-executed

### Comparison to Traditional Tracking

**Traditional Approach** (separate tracking table):
```
migrations_applied:
  - id: 1, name: "000-initial-locations", applied_at: "2024-01-01"
  - id: 2, name: "001-political-parties", applied_at: "2024-01-15"
```

**Problems**:
- Tracking table can get out of sync with actual data
- Requires separate database for tracking
- Rollback requires updating both data and tracking table
- Not distributed (each environment has own tracking)

**Our Approach** (persisted snapshots):
```
Git commits in Database Repository:
  - commit abc123: "Migration: 000-initial-locations" (snapshot)
  - commit def456: "Migration: 001-political-parties" (snapshot)
```

**Benefits**:
- Snapshot and tracking are the same thing (always in sync)
- No separate tracking database needed
- Rollback is just `git revert` (removes snapshot)
- Distributed via Git (pull to see applied migrations)

---

## Component Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface                             │
│  nes migrate list                                          │
│  nes migrate pending                                       │
│  nes migrate run [name]                                    │
│  nes migrate create <name>                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Migration Manager                           │
│  • Discover migrations in migrations/ directory             │
│  • Check applied migrations (query Git log)                 │
│  • Determine pending migrations                             │
│  • Validate migration structure                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Migration Runner                            │
│  • Load migration script                                    │
│  • Create migration context                                 │
│  • Execute migration                                        │
│  • Handle errors and logging                                │
│  • Commit and push (persist snapshot)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Migration Context                           │
│  • Thin API for migration scripts                           │
│  • Access to Publication Service                            │
│  • Access to Search Service                                 │
│  • Access to Scraping Service                               │
│  • File reading helpers                                     │
│  • Logging mechanism                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Publication Service                         │
│  • Create/update entities                                   │
│  • Create/update relationships                              │
│  • Automatic versioning                                     │
│  • Write to Database Repository                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Database Repository (nes-db/)                   │
│  • Entity JSON files                                        │
│  • Relationship JSON files                                  │
│  • Version history files                                    │
│  • Git history (migration tracking)                         │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### Migration Manager

**Responsibility**: Discovery and tracking of migrations

**Key Operations**:
- Scan `migrations/` directory for migration folders
- Validate migration structure (has migrate.py, README.md)
- Query Git log in Database Repository for applied migrations
- Compare discovered vs applied to find pending migrations
- Cache results to avoid repeated Git queries

**Interface**:
```python
class MigrationManager:
    async def discover_migrations(self) -> List[Migration]
    async def get_applied_migrations(self) -> List[str]
    async def get_pending_migrations(self) -> List[Migration]
    async def is_migration_applied(self, migration: Migration) -> bool
```

#### Migration Runner

**Responsibility**: Execution of migration scripts

**Key Operations**:
- Load migration script dynamically (import migrate.py)
- Create execution context with service access
- Execute migration script's `migrate()` function
- Track execution time and statistics
- Handle errors gracefully
- Commit changes to Database Repository (persist snapshot)
- Push to remote

**Interface**:
```python
class MigrationRunner:
    async def run_migration(
        self,
        migration: Migration,
        dry_run: bool = False,
        force: bool = False
    ) -> MigrationResult
    
    async def run_migrations(
        self,
        migrations: List[Migration],
        dry_run: bool = False
    ) -> List[MigrationResult]
    
    async def commit_and_push(
        self,
        migration: Migration,
        result: MigrationResult
    ) -> None
```

#### Migration Context

**Responsibility**: Provide minimal API for migration scripts

**Key Operations**:
- Expose services (publication, search, scraping)
- Provide file reading helpers (CSV, JSON, Excel)
- Provide logging mechanism
- Provide migration folder path

**Design Philosophy**: Thin wrapper, no business logic

**Interface**:
```python
class MigrationContext:
    # Services
    publication: PublicationService
    search: SearchService
    scraping: ScrapingService
    db: EntityDatabase
    
    # Helpers
    def read_csv(self, filename: str) -> List[Dict[str, Any]]
    def read_json(self, filename: str) -> Any
    def read_excel(self, filename: str, sheet_name: str = None) -> List[Dict[str, Any]]
    def log(self, message: str) -> None
    
    # Properties
    @property
    def migration_dir(self) -> Path
```

---

## Data Flow

### Migration Execution Flow

```
1. User runs: nes migrate run 005-add-ministers
                              │
                              ▼
2. CLI calls Migration Manager
   - Discover migration 005
   - Check if already applied (query Git log in nes-db/)
                              │
                              ▼
3. If not applied, CLI calls Migration Runner
   - Load migrate.py script
   - Create Migration Context
                              │
                              ▼
4. Migration Runner executes migrate(context)
   - Script reads data files
   - Script calls context.publication.create_entity(...)
   - Script calls context.publication.create_relationship(...)
                              │
                              ▼
5. Publication Service writes to Database Repository
   - Creates entity JSON files in nes-db/v2/entity/
   - Creates relationship JSON files in nes-db/v2/relationship/
   - Creates version JSON files in nes-db/v2/version/
                              │
                              ▼
6. Migration Runner commits changes (persist snapshot)
   - Stage changed files: git add nes-db/v2/
   - Create commit with metadata
   - Commit message: "Migration: 005-add-ministers\n\n..."
                              │
                              ▼
7. Migration Runner pushes to remote
   - Push to Database Repository: git push origin main
   - Snapshot is now persisted and visible to all
                              │
                              ▼
8. Service API Repository updated
   - Update submodule reference: git add nes-db
   - Commit and push to Service API Repository
                              │
                              ▼
9. Migration is now "applied"
   - Persisted snapshot exists in Database Repository
   - Re-running will skip (detect snapshot)
```

### Read Flow (Checking Applied Migrations)

```
1. User runs: nes migrate pending
                              │
                              ▼
2. Migration Manager discovers all migrations
   - Scan migrations/ directory
   - Parse folder names (NNN-descriptive-name)
   - Sort by prefix
                              │
                              ▼
3. Migration Manager queries applied migrations
   - Run: git log --grep="^Migration:" --format=%s
   - In: nes-db/ (Database Repository)
   - Parse commit messages to extract migration names
                              │
                              ▼
4. Migration Manager compares
   - Discovered: [000, 001, 002, 003, 004, 005]
   - Applied: [000, 001, 002, 003]
   - Pending: [004, 005]
                              │
                              ▼
5. CLI displays pending migrations
   - 004-update-party-leadership
   - 005-add-cabinet-ministers
```

---

## Git Integration

### Commit Message Format

Each migration execution creates a structured commit message:

```
Migration: {prefix}-{name}

{description}

Author: {author_email}
Date: {date}
Entities created: {count}
Entities updated: {count}
Relationships created: {count}
Relationships updated: {count}
Duration: {seconds}s
```

**Example**:
```
Migration: 005-add-cabinet-ministers

Import current cabinet ministers from official government records.
Adds person entities and HOLDS_POSITION relationships.

Author: contributor@example.com
Date: 2024-03-15
Entities created: 25
Relationships created: 25
Duration: 12.3s
```

### Batch Commits

For migrations that create many files (10,000+), commits are batched:

```python
BATCH_COMMIT_THRESHOLD = 1000  # Batch if more than 1000 files
BATCH_SIZE = 1000  # Files per batch

# Example: Migration creates 5,000 files
# Results in 5 commits:
#   - Migration: 005-large-import (Batch 1/5) - 1000 files
#   - Migration: 005-large-import (Batch 2/5) - 1000 files
#   - Migration: 005-large-import (Batch 3/5) - 1000 files
#   - Migration: 005-large-import (Batch 4/5) - 1000 files
#   - Migration: 005-large-import (Batch 5/5) - 1000 files
```

**Benefits**:
- Avoids huge commits that slow down Git
- Provides progress visibility
- Allows partial recovery if push fails

### Querying Migration History

```bash
# See all migrations applied
cd nes-db
git log --grep="Migration:" --oneline

# See details of specific migration
git log --grep="Migration: 005-add-cabinet-ministers"

# See what files changed
git show <commit-sha> --stat

# See full diff
git show <commit-sha>
```

### Rollback

```bash
# Revert specific migration
cd nes-db
git revert <commit-sha>
git push origin main

# This removes the persisted snapshot
# Migration becomes "unapplied" and can be re-executed
```

---

## Performance Considerations

### Large Database Repository (100k-1M files)

**Challenges**:
- Git performance degrades with many files
- Clone times become prohibitive
- Disk space requirements increase

**Solutions**:

**1. Shallow Clones**:
```bash
git clone --depth 1 https://github.com/org/nes-db.git
```

**2. Sparse Checkout**:
```bash
git clone --filter=blob:none --sparse https://github.com/org/nes-db.git
cd nes-db
git sparse-checkout set v2/entity/person
```

**3. Git Configuration**:
```bash
git config core.preloadindex true
git config core.fscache true
git config gc.auto 256
```

**4. Batch Commits**:
- Automatically split large commits
- 1000 files per commit
- Reduces Git overhead

### Migration Execution Performance

**Optimizations**:
- Async I/O for file operations
- Batch entity creation where possible
- Minimal validation (services handle it)
- Progress logging for long-running migrations

### Caching

**Applied Migrations Cache**:
```python
class MigrationManager:
    def __init__(self):
        self._applied_cache = None  # Cache Git query results
    
    async def get_applied_migrations(self):
        if self._applied_cache is not None:
            return self._applied_cache
        
        # Query Git log (expensive)
        result = subprocess.run(["git", "log", ...])
        
        # Cache result
        self._applied_cache = parse_result(result)
        return self._applied_cache
```

---

## Design Decisions

### Why Two Repositories?

**Decision**: Separate Service API and Database repositories

**Rationale**:
- **Performance**: Service API repo stays lightweight (~10MB)
- **Scalability**: Database repo can grow to 1GB+ without affecting development
- **Review Process**: Code review separate from data changes
- **Flexibility**: Different Git strategies for each repo

**Alternatives Considered**:
- Single repository: Would become huge and slow
- Database in separate storage (S3): Loses Git benefits (history, rollback)

### Why Linear Migration Model?

**Decision**: Sequential migrations with numeric prefixes

**Rationale**:
- **Simplicity**: Easy to understand and reason about
- **Predictability**: Database state is deterministic
- **Reproducibility**: Running migrations 000-N always produces same state

**Alternatives Considered**:
- Branching migrations: Too complex, hard to merge
- Timestamp-based: Conflicts when multiple contributors work simultaneously
- Dependency graph: Overkill for data migrations

### Why Persisted Snapshots for Tracking?

**Decision**: Use Git commits as migration tracking mechanism

**Rationale**:
- **Simplicity**: No separate tracking database needed
- **Sync**: Tracking and data are always in sync (they're the same thing)
- **Distribution**: Git provides distributed tracking
- **Rollback**: Standard Git operations work

**Alternatives Considered**:
- Separate tracking table: Can get out of sync with data
- Tracking file in repo: Still needs Git commits for data
- External database: Adds complexity and sync issues

### Why Thin Migration Context?

**Decision**: Minimal API, direct service access

**Rationale**:
- **Simplicity**: Less code to maintain
- **Flexibility**: Migration scripts can use full service APIs
- **Transparency**: No hidden behavior or magic

**Alternatives Considered**:
- Rich context with helpers: More maintenance burden
- Wrapper methods: Hides service capabilities
- DSL for migrations: Too restrictive

### Why File-Based Storage?

**Decision**: JSON files instead of traditional database

**Rationale**:
- **Git-Friendly**: Human-readable, easy to diff
- **Transparency**: Can inspect files directly
- **Simplicity**: No database server needed
- **Versioning**: Git provides version control

**Alternatives Considered**:
- PostgreSQL: Requires server, harder to version
- MongoDB: Same issues as PostgreSQL
- SQLite: Better, but still not as Git-friendly

---

## Additional Resources

- **Contributor Guide**: See [Migration Contributor Guide](/contributors/migration-contributor-guide) for creating migrations
- **Maintainer Guide**: See [Migration Maintainer Guide](/contributors/migration-maintainer-guide) for executing migrations
- **API Reference**: See [OpenAPI documentation](/docs) for complete API documentation
- **Data Models**: See [Data Models](/consumers/data-models) for entity schemas

---

**Last Updated:** 2024
**Version:** 2.0
