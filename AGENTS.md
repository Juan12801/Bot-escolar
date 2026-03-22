# Agent Guidelines - Bot Escolar

This is a Python Telegram bot for managing school tasks with MongoDB storage and scheduled notifications.

## Project Structure

```
Bot escolar/
├── bot.py          # Main entry point, bot initialization
├── config.py       # Environment variable configuration
├── database.py     # MongoDB operations
├── handlers.py     # Telegram command and callback handlers
├── scheduler.py    # APScheduler for daily notifications
├── requirements.txt
└── .env            # Environment variables (BOT_TOKEN, MONGO_URI, etc.)
```

## Commands

### Run the Bot
```bash
python bot.py
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file with:
```
BOT_TOKEN=your_telegram_bot_token
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=bot_escolar
COLLECTION_NAME=tasks
GROUP_CHAT_ID=-123456789
NOTIFICATION_HOUR=15
```

## Code Style Guidelines

### Python Version
- Python 3.10+

### Formatting
- 4 spaces for indentation (no tabs)
- Maximum 100 characters per line
- Use single quotes for strings unless containing single quotes
- Add trailing commas in multi-line collections

### Imports
Order imports in three sections (each separated by a blank line):
1. Standard library (`logging`, `asyncio`, `datetime`)
2. Third-party packages (`telegram`, `pymongo`, `apscheduler`)
3. Local modules (`config`, `database`, `handlers`)

```python
import logging
import asyncio
from telegram.ext import ApplicationBuilder

import config
import handlers
```

### Naming Conventions
- **Functions/variables**: `snake_case` (e.g., `add_task`, `get_pending_tasks`)
- **Classes**: `PascalCase` (e.g., `TaskManager`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `BOT_TOKEN`)
- **Private items**: Prefix with `_` (e.g., `_internal_func`)
- **Type aliases**: `PascalCase` (e.g., `TaskDict`)

### Type Annotations
- Use type hints for all function parameters and return types
- Use the `typing` module for complex types (`Optional`, `List`, `Dict`, etc.)
- Define type aliases for complex dict structures

```python
from typing import Optional

def get_task_by_id(task_id: str) -> Optional[Dict]:
    ...
```

### Async/Await
- All Telegram handlers must be `async def`
- Always use `await` for async operations
- Use `asyncio.run()` in entry points
- Group related awaits when possible

### Error Handling
- Never use bare `except:` clauses; always specify exception type
- Catch specific exceptions (`KeyError`, `ValueError`, `ObjectId`)
- Log errors with `logger.error()` before user-facing error messages
- Return early on errors when appropriate

```python
# Good
try:
    result = collection.delete_one({"_id": ObjectId(task_id)})
    return result.deleted_count > 0
except Exception:
    return False

# Avoid
try:
    ...
except:
    pass
```

### Logging
- Use `logging.getLogger(__name__)` for module loggers
- Log at appropriate levels: `DEBUG` (development), `INFO` (runtime), `ERROR` (failures)
- Include context in log messages (e.g., user IDs, task names)

```python
logger = logging.getLogger(__name__)
logger.info(f"Task added with ID: {task_id}")
logger.error(f"Error listing tasks: {e}")
```

### MongoDB Operations (database.py)
- Always convert `ObjectId` to string before returning to handlers
- Handle `ObjectId` conversion in try/except blocks
- Use descriptive variable names for query results
- Convert cursor results to lists when needed

### Telegram Handlers (handlers.py)
- Use `Update` and `ContextTypes.DEFAULT_TYPE` type hints
- Always call `await query.answer()` for callback queries
- Use `reply_markup` for inline keyboards
- Handle missing arguments gracefully with user-friendly messages

### Testing
No formal test suite exists. For manual testing:
1. Start the bot with `python bot.py`
2. Test commands: `/start`, `/add`, `/del`
3. Test inline button callbacks
4. Verify MongoDB operations in the database

### Deployment
- Hosted on Railway (see `railway.toml`) and Render (see `render.yaml`)
- Environment variables set in hosting platform dashboard
- Bot uses polling mode (`start_polling`)
- Scheduler runs daily at `NOTIFICATION_HOUR` (default 15:00)

## Security Considerations
- Never commit `.env` file (already in `.gitignore`)
- Validate user input before database operations
- Use parameterized queries (handled by pymongo)
- Log security-relevant events
