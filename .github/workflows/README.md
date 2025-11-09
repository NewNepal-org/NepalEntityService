# GitHub Actions Workflows for Migration System

This directory contains automated workflows for the Nepal Entity Service migration system.

## Workflows

### 1. Migration Preview (`migration-preview.yml`)

**Trigger**: Pull request with changes to `migrations/` directory

**Purpose**: Validates and previews migrations before they are merged

**What it does**:
- Detects new or modified migrations in the PR
- Validates migration folder structure (checks for `migrate.py` and `README.md`)
- Executes migrations in dry-run mode
- Generates statistics (entities/relationships created)
- Posts a comment on the PR with preview results and logs link

**Benefits**:
- Catches errors before merge
- Provides visibility into what the migration will do
- Helps reviewers understand the impact of changes

### 2. Migration Persistence (`migration-persistence.yml`)

**Triggers**:
- Push to `main` branch with changes to `migrations/` directory
- Scheduled daily at 2 AM UTC
- Manual workflow dispatch

**Purpose**: Executes approved migrations and persists data to the Database Repository

**What it does**:
- Checks for pending migrations (not yet applied)
- Executes pending migrations with auto-commit
- Creates/modifies files in the Database Repository (`nes-db/` submodule)
- Commits changes to Database Repository with migration metadata
- Pushes commits to Database Repository remote
- Updates submodule reference in Service API Repository
- Creates GitHub issue on failure for maintainer attention

**Benefits**:
- Automates migration execution after PR merge
- Ensures migrations are applied consistently
- Maintains complete audit trail in Git history
- Handles large file operations with appropriate Git configuration
- Provides failure notifications for quick response

## Configuration

### Required Secrets

- `DATABASE_REPO_TOKEN` (optional): GitHub token with write access to the Database Repository
  - If not provided, falls back to default `github.token`
  - Required if Database Repository is in a different organization

### Environment Variables

The workflows use the following environment variables:
- `NES_DB_PATH`: Path to the Database Repository (defaults to `./nes-db`)

## Workflow Execution Flow

```
1. Contributor creates PR with migration
   ↓
2. Migration Preview workflow runs
   - Validates migration structure
   - Executes in dry-run mode
   - Posts preview comment on PR
   ↓
3. Maintainer reviews PR and preview results
   ↓
4. PR is merged to main
   ↓
5. Migration Persistence workflow runs
   - Checks for pending migrations
   - Executes migrations
   - Commits to Database Repository
   - Pushes to remote
   - Updates submodule reference
   ↓
6. Data is now available in Database Repository
```

## Determinism and Idempotency

Both workflows are designed to be deterministic and idempotent:

- **Migration Preview**: Always runs in dry-run mode, never persists changes
- **Migration Persistence**: Checks for already-applied migrations before execution
  - Uses persisted snapshots in Database Repository as source of truth
  - Skips migrations that have already been applied
  - Safe to run multiple times (scheduled job runs daily)

## Troubleshooting

### Migration Preview Fails

If the preview workflow fails:
1. Check the workflow logs for error details
2. Verify migration folder structure (must have `migrate.py` and `README.md`)
3. Check for Python syntax errors in migration script
4. Ensure migration script has required metadata (AUTHOR, DATE, DESCRIPTION)

### Migration Persistence Fails

If the persistence workflow fails:
1. An issue will be automatically created with the `migration` and `urgent` labels
2. Check the workflow logs for error details
3. Common issues:
   - Git push timeout (large number of files)
   - Database Repository access issues
   - Migration script runtime errors
4. Migrations can be executed manually using `nes migration run --all`

### Manual Execution

To manually execute migrations:

```bash
# Check pending migrations
nes migration list --pending

# Execute specific migration
nes migration run <migration-name>

# Execute all pending migrations
nes migration run --all
```

## Monitoring

- **Preview Results**: Check PR comments for migration preview statistics
- **Persistence Status**: Check workflow runs in the Actions tab
- **Migration History**: Check Git log in Database Repository for applied migrations
- **Failures**: Check Issues tab for automatically created failure notifications

## Further Documentation

- [Migration System Design](../../.kiro/specs/open-database-updates/design.md)
- [Migration Requirements](../../.kiro/specs/open-database-updates/requirements.md)
- [Implementation Tasks](../../.kiro/specs/open-database-updates/tasks.md)
