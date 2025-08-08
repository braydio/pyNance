# pyNance Development Guide

This guide provides comprehensive development standards, tooling requirements, and validation steps for contributing to pyNance.

## Table of Contents
- [Environment Setup](#environment-setup)
- [Tooling and Versions](#tooling-and-versions)
- [Code Style and Standards](#code-style-and-standards)
- [Git Workflow and Hooks](#git-workflow-and-hooks)
- [Pull Request Requirements](#pull-request-requirements)
- [Testing and Validation](#testing-and-validation)
- [CSS/Styling Enforcement](#cssstyling-enforcement)
- [Local Development Commands](#local-development-commands)
- [CI Validation Steps](#ci-validation-steps)

## Environment Setup

### Initial Setup
Run the setup script to prepare your development environment:

```bash
# Full development setup
bash scripts/setup.sh

# Or slim setup (production dependencies only)
bash scripts/setup.sh --slim
```

This script will:
- Create Python virtual environment (`.venv`)
- Install Python dependencies from `requirements.txt` and `requirements-dev.txt`
- Set up Git hooks via `core.hooksPath`
- Configure frontend dependencies
- Copy example environment files

### Environment Files
Copy and configure environment files for both backend and frontend:

```bash
# Backend environment
cp backend/example.env backend/.env

# Frontend environment
cp frontend/example.env frontend/.env
```

**Validation Steps:**
```bash
# Verify .env files exist
[ -f backend/.env ] && echo "✅ Backend .env exists" || echo "❌ Backend .env missing"
[ -f frontend/.env ] && echo "✅ Frontend .env exists" || echo "❌ Frontend .env missing"

# Verify virtual environment
[ -d .venv ] && echo "✅ Virtual environment exists" || echo "❌ Virtual environment missing"
```

## Tooling and Versions

### Required Versions
- **Python**: 3.11
- **Node.js**: 20 (specified in `.nvmrc` if available)
- **npm**: Latest compatible with Node 20

### Development Tools
- **Python Linting**: `black`, `ruff`, `mypy`, `pylint`, `bandit`
- **Python Testing**: `pytest`
- **Git Hooks**: `pre-commit`
- **Frontend**: Vue 3, Vite, TypeScript, TailwindCSS

**Validation Steps:**
```bash
# Check Python version
python --version | grep "3.11" && echo "✅ Python 3.11" || echo "❌ Wrong Python version"

# Check Node version
node --version | grep "v20" && echo "✅ Node 20" || echo "❌ Wrong Node version"

# Check required tools are installed
command -v black >/dev/null && echo "✅ black installed" || echo "❌ black missing"
command -v ruff >/dev/null && echo "✅ ruff installed" || echo "❌ ruff missing"
command -v mypy >/dev/null && echo "✅ mypy installed" || echo "❌ mypy missing"
command -v pre-commit >/dev/null && echo "✅ pre-commit installed" || echo "❌ pre-commit missing"
```

## Code Style and Standards

### Python Standards
- **Style**: PEP 8 compliance
- **Type Annotations**: Required for all functions and methods
- **Formatters**: `black` (line length: 120), `isort` (black profile)
- **Linters**: `ruff`, `mypy`, `pylint`
- **Security**: `bandit` for security checks

### Frontend Standards
- **CSS Framework**: TailwindCSS only (no custom CSS)
- **JavaScript**: ESLint with Vue 3 rules
- **Formatting**: Prettier for consistent code style

**Validation Steps:**
```bash
# Python style validation
black --check --line-length=120 backend/
isort --check-only --profile black backend/
ruff check backend/ --line-length=120
mypy backend/ --ignore-missing-imports
pylint backend/app/
bandit -r backend/app/routes

# Frontend validation
cd frontend
npm run lint
npm run format -- --check
cd ..
```

## Git Workflow and Hooks

### Git Hooks Setup
Git hooks are configured automatically via the setup script:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/*
```

### Pre-commit Configuration
Pre-commit runs automatically on commit and includes:
- `black` - Python code formatting
- `isort` - Python import sorting  
- `ruff` - Python linting with auto-fix
- `mypy` - Static type checking
- `pylint` - Python linting
- `bandit` - Security analysis
- Model field validation tests

**Validation Steps:**
```bash
# Check Git hooks are configured
git config --get core.hooksPath | grep ".githooks" && echo "✅ Git hooks configured" || echo "❌ Git hooks not configured"

# Test pre-commit setup
pre-commit run --all-files
```

## Pull Request Requirements

### Title Format
Use the following format for PR titles:
```
[component] Fix or Add <description>
```

Examples:
- `[backend] Fix transaction sync error handling`
- `[frontend] Add TailwindCSS validation hook`
- `[tests] Add coverage for forecast engine`

### Description Requirements
PR descriptions must include:
- **Affected modules**: Specify backend/frontend/tests
- **API changes**: Document new endpoints or modifications
- **Test coverage**: Confirm tests are added/updated
- **Documentation updates**: Run `doc_cleaner.py` if docs are modified

### Commit Message Format
Follow conventional commit format:
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Examples:
- `feat(auth): add token helper for API authentication`
- `fix(sync): resolve transaction duplicate detection`
- `docs(api): update forecast endpoint documentation`

**Validation Steps:**
```bash
# Validate commit messages (run locally before push)
git log --oneline -5 | grep -E "^[a-f0-9]+ (feat|fix|docs|style|refactor|test|chore)\(.+\): .+" && echo "✅ Commit format valid" || echo "❌ Commit format invalid"

# Check if doc_cleaner.py was run after doc changes
python scripts/doc_cleaner.py
git status | grep "docs/index/INDEX.md" && echo "❌ Run git add docs/index/INDEX.md" || echo "✅ Doc index up to date"
```

## Testing and Validation

### Testing Requirements
- **Unit Tests**: `pytest` for all new functionality
- **Coverage**: Minimum coverage expectations for critical paths
- **Model Validation**: `test_model_fields_are_valid` must pass
- **Integration Tests**: For API endpoints and data flows

### Pre-push Checklist
Run these commands before pushing:

```bash
# 1. Run full test suite
pytest

# 2. Run pre-commit on all files
pre-commit run --all-files

# 3. Verify model field validation
pytest tests/test_model_field_validation.py

# 4. Check test coverage (if coverage is configured)
pytest --cov=backend/app --cov-report=term-missing
```

**Validation Steps:**
```bash
# Core validation commands that must pass
echo "Running core validation..."

# Python tests
python -m pytest tests/ -v || { echo "❌ Python tests failed"; exit 1; }

# Pre-commit validation
pre-commit run --all-files || { echo "❌ Pre-commit checks failed"; exit 1; }

# Model field validation
python -m pytest tests/test_model_field_validation.py -v || { echo "❌ Model validation failed"; exit 1; }

echo "✅ All core validation passed"
```

## CSS/Styling Enforcement

### TailwindCSS Only Policy
As specified in `docs/TODO.md`, only TailwindCSS syntax is allowed for styling. No custom CSS should be used.

### TailwindCSS Validation Hook
A validation system must be implemented to ensure only TailwindCSS syntax is used:

**Implementation Requirements:**
- Pre-commit hook to scan for custom CSS
- CI/CD integration to prevent non-TailwindCSS styles
- Automated scanning of Vue components and style blocks

### CSS Validation Commands

```bash
# Check for custom CSS in Vue components (manual validation until automated hook is implemented)
echo "Checking for custom CSS usage..."

# Scan for style blocks with custom CSS (excluding TailwindCSS directives)
grep -r "<style" frontend/src/ --include="*.vue" | while read -r line; do
  file=$(echo "$line" | cut -d: -f1)
  echo "⚠️  Custom style block found in: $file"
done

# Look for non-Tailwind class patterns (basic check)
grep -r "class.*{" frontend/src/ --include="*.vue" --include="*.css" && echo "❌ Custom CSS classes found" || echo "✅ No custom CSS classes detected"

# Verify TailwindCSS is properly configured
[ -f frontend/tailwind.config.js ] && echo "✅ TailwindCSS config exists" || echo "❌ TailwindCSS config missing"
```

**Acceptance Criteria for TailwindCSS Validation:**
- All CSS validation passes without errors
- No custom CSS classes found in components
- Only TailwindCSS utility classes are used
- Pre-commit hook prevents custom CSS from being committed

## Local Development Commands

### Quick Start Commands
```bash
# Full development environment setup
bash scripts/initialize_env_dev.sh

# Manual backend start
cd backend && flask run

# Manual frontend start
cd frontend && npm install && npm run dev
```

### Development Validation Commands
```bash
# Complete local validation (run before committing)
./scripts/validate-dev.sh  # Create this script with all validation steps

# Or run individual validations:
python -m pytest tests/
pre-commit run --all-files
cd frontend && npm run lint && npm run format -- --check
```

### Documentation Maintenance
```bash
# Update documentation index after doc changes
python scripts/doc_cleaner.py
git add docs/index/INDEX.md

# Verify documentation is up to date
python scripts/doc_cleaner.py && echo "✅ Docs index updated" || echo "❌ Doc cleaner failed"
```

## CI Validation Steps

### Required CI Checks
The following validations must pass in CI/CD:

```yaml
# Example CI validation steps
- name: Python Tests
  run: python -m pytest tests/ -v

- name: Python Linting
  run: |
    black --check --line-length=120 backend/
    ruff check backend/ --line-length=120
    mypy backend/ --ignore-missing-imports
    pylint backend/app/

- name: Security Check
  run: bandit -r backend/app/routes

- name: Frontend Tests
  run: |
    cd frontend
    npm run lint
    npm run format -- --check
    npm run test

- name: TailwindCSS Validation
  run: |
    # Custom script to validate only TailwindCSS usage
    ./scripts/validate-tailwind.sh

- name: Model Field Validation
  run: python -m pytest tests/test_model_field_validation.py -v
```

### Environment Validation
```bash
# CI should validate environment setup
[ -f backend/example.env ] && echo "✅ Backend example.env exists" || exit 1
[ -f frontend/example.env ] && echo "✅ Frontend example.env exists" || exit 1
[ -f .pre-commit-config.yaml ] && echo "✅ Pre-commit config exists" || exit 1
[ -f scripts/setup.sh ] && echo "✅ Setup script exists" || exit 1
```

## Troubleshooting

### Common Issues and Solutions

**1. Pre-commit fails on first run**
```bash
# Install pre-commit hooks
pre-commit install
pre-commit run --all-files
```

**2. Python version mismatch**
```bash
# Ensure Python 3.11 is active
python --version
# Recreate virtual environment if needed
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

**3. Node version issues**
```bash
# Use nvm if available
nvm install 20
nvm use 20
# Or install Node 20 directly
```

**4. Git hooks not working**
```bash
# Relink Git hooks
git config core.hooksPath .githooks
chmod +x .githooks/*
```

## Summary

This development guide ensures consistent code quality, proper tooling setup, and comprehensive validation. All contributors must:

1. Follow the specified tooling versions (Python 3.11, Node 20)
2. Use proper code style (PEP 8, TailwindCSS only)
3. Run validation commands before committing
4. Follow PR and commit message formats
5. Maintain test coverage and documentation

The validation steps provided can be run both locally and in CI to ensure code quality and consistency across the project.
