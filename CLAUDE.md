# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open WebUI is an extensible, feature-rich, self-hosted AI platform that operates entirely offline. It's a full-stack application with a Python FastAPI backend and a SvelteKit frontend, designed to provide a web interface for various LLM runners including Ollama and OpenAI-compatible APIs.

## Architecture

### Backend (Python/FastAPI)
- **Main Framework**: FastAPI with SQLAlchemy for database operations
- **Database**: Supports SQLite (default), PostgreSQL, MySQL with migration system via Alembic
- **Authentication**: JWT-based with support for OAuth2, LDAP, and external providers
- **Real-time**: WebSocket support via Socket.IO for live chat features
- **Caching**: Redis integration for performance optimization
- **Vector Storage**: Multiple vector database support (ChromaDB, Qdrant, Milvus, OpenSearch, Elasticsearch)

### Frontend (SvelteKit)
- **Framework**: SvelteKit with TypeScript
- **Styling**: Tailwind CSS with custom themes
- **State Management**: Svelte stores with localStorage persistence
- **Build Tool**: Vite with various build modes (development, production)

### Key Directories
- `backend/open_webui/` - Main backend application code
- `src/` - Frontend SvelteKit application
- `static/` - Static assets including Pyodide for client-side Python execution
- `backend/data/` - Database files and uploads
- `docs/` - Documentation files

## Development Commands

### Frontend Development
```bash
# Development server with hot reload
npm run dev

# Development on specific port
npm run dev:5050

# Build for production
npm run build

# Build for different environments
npm run build:bjny    # Build for Beijing environment
npm run build:nkxz    # Build for Nanjing environment

# Type checking
npm run check

# Linting
npm run lint           # Run all linters
npm run lint:frontend  # ESLint for frontend
npm run lint:types    # TypeScript checking
npm run lint:backend  # Python linting

# Format code
npm run format         # Prettier for frontend
npm run format:backend # Black for Python backend

# Testing
npm run test:frontend  # Vitest tests
npm run cy:open       # Cypress E2E testing
```

### Backend Development
```bash
# Start backend server
cd backend
python -m open_webui.main

# Run with development settings
./start_dev.sh

# Run database migrations
python -m alembic upgrade head

# Python linting and formatting
pylint backend/
black . --exclude ".venv/|/venv/"
```

### Docker Development
```bash
# Start full stack with Docker
docker-compose up -d

# Build and start
make startAndBuild

# Stop services
make stop

# Update and rebuild
make update
```

## Configuration

### Environment Variables
Key configuration variables are managed in `backend/open_webui/env.py`:
- `WEBUI_AUTH` - Authentication enable/disable
- `OLLAMA_BASE_URL` - Ollama server URL
- `OPENAI_API_KEY` - OpenAI API key
- `DATABASE_URL` - Database connection string
- `REDIS_URL` - Redis connection string

### Build Modes
The frontend supports different build configurations:
- `development` - Local development with hot reload
- `bjny` - Beijing environment configuration
- `nkxz` - Nanjing environment configuration

## Key Features

### Model Management
- Support for multiple LLM providers (Ollama, OpenAI-compatible APIs)
- Dynamic model loading and configuration
- Model permission system with user-based access control

### Chat Features
- Real-time chat with streaming responses
- File upload and document processing
- RAG (Retrieval Augmented Generation) integration
- Web search capabilities
- Voice/video call support

### User Management
- Role-based access control (RBAC)
- User groups and permissions
- OAuth2 integration
- LDAP support

### Plugin System
- Pipeline framework for custom Python functions
- Function calling tools
- Webhook support
- External API integration

## Database Schema

The application uses SQLAlchemy ORM with the following main models:
- `User` - User accounts and authentication
- `Chat` - Chat sessions and conversations
- `Message` - Individual chat messages
- `Model` - Available AI models
- `Document` - Uploaded files and documents
- `Knowledge` - RAG knowledge base
- `Function` - Custom Python functions

## Testing

### Frontend Tests
- Unit tests with Vitest
- E2E tests with Cypress
- Type checking with TypeScript

### Backend Tests
- pytest for unit tests
- Docker integration tests
- Database migration tests

## Deployment

### Docker Deployment
- Multi-stage Docker builds
- GPU support with CUDA images
- Ollama bundled images available

### Production Considerations
- Redis for caching and session storage
- PostgreSQL for production database
- SSL/TLS configuration
- Load balancing support

## Development Workflow

1. **Setup**: Clone repository and install dependencies
2. **Backend**: Configure environment variables and start FastAPI server
3. **Frontend**: Run development server with hot reload
4. **Database**: Run migrations when schema changes
5. **Testing**: Run appropriate test suites before committing
6. **Building**: Create production builds for deployment

## Important Notes

- Try to answer questions in Chinese as much as possible.
- The application uses Python 3.11+ and Node.js 18+
- Database migrations are handled by Alembic
- Frontend builds are automatically copied to backend static directory
- Pyodide is included for client-side Python execution
- The codebase supports multiple deployment environments