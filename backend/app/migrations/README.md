# Database Migrations

This directory contains database migration scripts.

## Running Migrations

### Run a specific migration

```bash
cd backend
uv run python app/migrations/<migration_file>.py
```

### Example: Add embedding column

```bash
cd backend
uv run python app/migrations/add_embedding_column.py
```

## Migration Files

- `add_embedding_column.py`: Adds `embedding` column to `test_cases` table for vector storage

## Rollback

Each migration file includes a `downgrade()` function for rollback:

```python
import asyncio
from app.migrations.add_embedding_column import downgrade

asyncio.run(downgrade())
```
