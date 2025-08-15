# pyNance Organizational Plan

## Executive Summary

This document outlines the organizational improvements implemented for the pyNance personal finance dashboard to enhance security, maintainability, and developer experience.

## Key Issues Identified

### Security & Privacy Concerns
- **Tracked .bashrc**: Contains environment variable templates but was tracked in version control, risking exposure of local developer configurations
- **Missing .gitignore rules**: Gaps in protection against secrets, credentials, and local development files
- **Lock file confusion**: Global `*.lock` ignore was preventing reproducible builds

### Organizational Issues
- **Mixed configuration**: Environment variables scattered between .bashrc and various locations
- **Untracked development tooling**: `mcp-sqlite-projects-server/` directory with unclear purpose
- **Documentation gaps**: Missing clear setup instructions for new developers

## Actions Taken

### 1. Security Hardening
- ✅ Converted `.bashrc` → `.bashrc.example` (template)
- ✅ Created `backend/.env.example` with all backend configuration variables
- ✅ Created `frontend/.env.example` with all frontend (Vite) configuration variables
- ✅ Enhanced `.gitignore` with comprehensive rules for:
  - Environment files (`.env`, `.env.*`, `.envrc`)
  - Shell profiles (`.bashrc`, `.zshrc`)
  - Secrets and credentials
  - Database files and state
  - Development tools and local services
  - Build artifacts and caches
  - OS-specific files

### 2. Build Reproducibility
- ✅ Removed global `*.lock` ignore rule
- ✅ Ensured `package-lock.json` is tracked for reproducible Node.js builds
- ✅ Added specific ignores for cache directories while preserving lock files

### 3. Configuration Management
- ✅ Centralized environment variable definitions in template files
- ✅ Clear separation between backend and frontend configurations
- ✅ Maintained backward compatibility with existing `example.env` files

## Current Project Structure

```
pyNance/
├── backend/                 # Flask application
│   ├── app/                 # Application code
│   │   ├── routes/          # API endpoints
│   │   ├── models.py        # Data models
│   │   ├── services/        # Business logic
│   │   └── helpers/         # Utility functions
│   ├── migrations/          # Database migrations
│   ├── tests/               # Backend tests
│   ├── .env.example         # ✨ NEW: Backend config template
│   └── requirements.txt     # Python dependencies
├── frontend/                # Vue.js + Vite application
│   ├── src/                 # Frontend source code
│   ├── public/              # Static assets
│   ├── .env.example         # ✨ NEW: Frontend config template
│   └── package.json         # Node.js dependencies
├── docs/                    # Documentation
├── scripts/                 # Development and utility scripts
├── tests/                   # Integration tests
├── .bashrc.example          # ✨ NEW: Shell environment template
├── .gitignore               # ✨ UPDATED: Enhanced security rules
└── ORGANIZATION.md          # ✨ NEW: This document
```

## Developer Onboarding

### Initial Setup
1. **Clone and enter the repository**
   ```bash
   git clone [repository-url]
   cd pyNance
   ```

2. **Set up environment files**
   ```bash
   # Backend configuration
   cp backend/.env.example backend/.env
   # Edit backend/.env with your actual values

   # Frontend configuration  
   cp frontend/.env.example frontend/.env
   # Edit frontend/.env with your actual values

   # Optional: Shell environment (if you want project-specific shell setup)
   cp .bashrc.example .bashrc
   source .bashrc
   ```

3. **Set up Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # or .venv/Scripts/activate on Windows
   pip install -r backend/requirements.txt
   ```

4. **Set up Node.js environment**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Initialize database**
   ```bash
   # Follow specific database setup instructions in backend/README.md
   ```

### Configuration Guide

#### Backend Environment Variables (`backend/.env`)
- **Flask Configuration**: `FLASK_ENV`, `LOG_LEVEL`, `SQL_ECHO`
- **Database**: `DATABASE_NAME`, `CLIENT_NAME`
- **Plaid Integration**: `PLAID_CLIENT_ID`, `PLAID_SECRET_KEY`, `PLAID_ENV`
- **Teller Integration**: `TELLER_APP_ID`, `TELLER_WEBHOOK_SECRET`
- **Vector DB/LLM Tools**: `CHROMA_*`, `QDRANT_*`, `LOCALAI_*`

#### Frontend Environment Variables (`frontend/.env`)
- **Vite Configuration**: `VITE_SESSION_MODE`, `VITE_APP_API_BASE_URL`
- **Integration Settings**: `VITE_TELLER_APP_ID`, `VITE_PLAID_CLIENT_ID`
- **User Settings**: `VITE_USER_ID_PLAID`, `PHONE_NBR`

## Security Best Practices

### What NOT to Commit
- ❌ Real API keys, secrets, or tokens
- ❌ Local `.env` files with actual credentials
- ❌ Database files (`.db`, `.sqlite3`)
- ❌ Local shell profiles (`.bashrc`, `.zshrc`)
- ❌ IDE-specific settings
- ❌ Local development tools and their data

### What TO Commit
- ✅ Template files (`.env.example`, `.bashrc.example`)
- ✅ Lock files (`package-lock.json`, `poetry.lock`)
- ✅ Documentation and guides
- ✅ Test configurations and fixtures
- ✅ Build and deployment scripts

## Development Tools

### mcp-sqlite-projects-server
- **Status**: Ignored as local development tooling
- **Purpose**: SQLite project management server (based on directory contents)
- **Setup**: This appears to be a local development tool. If needed:
  1. Set it up separately according to its documentation
  2. Ensure any generated data/configs remain local
  3. Consider moving to `tools/` directory if it becomes essential for development

### Recommended Additions

#### Pre-commit Hooks (Future Enhancement)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.6
    hooks:
      - id: ruff

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]
```

## Architecture Notes

### Backend (Flask)
- Uses Flask application factory pattern
- Configuration loaded via python-dotenv from `backend/.env`
- Database migrations managed via Flask-Migrate
- API routes organized by feature domain

### Frontend (Vue.js + Vite)
- Vue 3 with Composition API
- Vite for build tooling and development server
- Environment variables prefixed with `VITE_`
- Component-based architecture with reusable UI components

### Integration Points
- **Plaid**: Banking data aggregation
- **Teller**: Alternative banking API
- **Vector Databases**: Chroma/Qdrant for AI/ML features
- **Local AI**: LocalAI integration for language models

## Maintenance

### Regular Tasks
- Review and update environment templates when new configuration is added
- Audit `.gitignore` rules when adding new development tools
- Update this documentation when project structure changes
- Rotate API keys and secrets according to security policies

### Monitoring
- Watch for accidentally committed secrets
- Review large file additions to prevent binary data leaks
- Ensure new team members follow onboarding procedures

## Future Improvements

### Short Term
1. Add pre-commit hooks for automated quality checks
2. Set up secret scanning in CI/CD pipeline
3. Create developer-friendly Makefile or npm scripts
4. Add container-based development environment

### Long Term
1. Migrate to more structured configuration management (e.g., python-decouple)
2. Implement proper secret management for production
3. Add comprehensive API documentation
4. Consider monorepo tooling for better backend/frontend coordination

---

**Last Updated**: Generated during organizational security audit  
**Maintainer**: Development team  
**Review Schedule**: Quarterly or when onboarding new developers
