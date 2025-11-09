# Database Setup Guide

## Overview

The Nepal Entity Service uses a file-based database stored in the `nes-db` directory, which is managed as a Git submodule pointing to the [NepalEntityService-database](https://github.com/NewNepal-org/NepalEntityService-database) repository.

## Configuration

### Environment Variables

The database path is configured via the `NES_DB_URL` environment variable using the `file://` protocol:

```bash
# .env file
NES_DB_URL=file:///absolute/path/to/nes-db/v2
```

**Important:** The path must be absolute (starting from filesystem root `/`).

#### Examples

**Local Development (macOS/Linux):**
```bash
NES_DB_URL=file:///Users/username/projects/NepalEntityService/nes-db/v2
```

**Local Development (Windows):**
```bash
NES_DB_URL=file:///C:/Users/username/projects/NepalEntityService/nes-db/v2
```

**Docker Container:**
```bash
NES_DB_URL=file:///app/nes-db/v2
```

## Git Submodule Setup

### Initial Clone

When cloning the repository for the first time, initialize the submodule:

```bash
git clone git@github.com:NewNepal-org/NepalEntityService.git
cd NepalEntityService
git submodule init
git submodule update
```

Or clone with submodules in one command:

```bash
git clone --recurse-submodules git@github.com:NewNepal-org/NepalEntityService.git
```

### Updating the Database

To pull the latest database changes:

```bash
git submodule update --remote nes-db
```

### Committing Database Changes

If you make changes to the database that should be shared:

```bash
# Navigate to the submodule
cd nes-db

# Commit and push changes
git add .
git commit -m "Update database"
git push origin main

# Return to main repository
cd ..

# Commit the submodule reference update
git add nes-db
git commit -m "Update database submodule reference"
git push
```

## Docker Setup

The Dockerfile automatically:
1. Copies the `nes-db` directory into the container
2. Creates the `nes-db/v2` directory if it doesn't exist
3. Sets `DATABASE_URL=file:///app/nes-db/v2` as the default

### Building with Docker

```bash
# Build the image
docker build -t nepal-entity-service .

# Run with default database
docker run -p 8195:8195 nepal-entity-service

# Run with custom database path (mount volume)
docker run -p 8195:8195 \
  -v /path/to/your/database:/app/nes-db/v2 \
  -e NES_DB_URL=file:///app/nes-db/v2 \
  nepal-entity-service
```

## Directory Structure

```
NepalEntityService/
├── nes-db/                    # Git submodule
│   ├── .git                   # Submodule git metadata
│   ├── README.md              # Database repository README
│   └── v2/                    # Version 2 database files
│       ├── entities/          # Entity JSON files
│       ├── relationships/     # Relationship JSON files
│       ├── versions/          # Version history
│       └── authors/           # Author records
├── nes/                      # Application code
│   └── config.py              # Configuration with DATABASE_URL support
└── .env                       # Local environment configuration
```

## Troubleshooting

### Submodule Not Initialized

If the `nes-db` directory is empty:

```bash
git submodule init
git submodule update
```

### Permission Issues

Ensure the database directory has proper read/write permissions:

```bash
chmod -R 755 nes-db/v2
```

### Invalid NES_DB_URL

The `NES_DB_URL` must use the `file://` protocol. If you see an error like:

```
ValueError: NES_DB_URL must use 'file://' protocol
```

Check that your URL starts with `file://` and uses an absolute path:

```bash
# ✅ Correct
NES_DB_URL=file:///Users/username/projects/NepalEntityService/nes-db/v2

# ❌ Wrong - missing file:// protocol
NES_DB_URL=/Users/username/projects/NepalEntityService/nes-db/v2

# ❌ Wrong - relative path
NES_DB_URL=file://nes-db/v2
```

## Development Workflow

1. **Start with latest database:**
   ```bash
   git submodule update --remote nes-db
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your absolute path
   ```

3. **Run the service:**
   ```bash
   poetry run nes server dev
   ```

4. **Make database changes** through the API or CLI

5. **Commit database changes** (if needed):
   ```bash
   cd nes-db
   git add .
   git commit -m "Add new entities"
   git push
   cd ..
   git add nes-db
   git commit -m "Update database reference"
   ```
