#!/usr/bin/env bash

# Development validation script for pyNance
# Runs all required validation steps before committing

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

CI_MODE=0

echo -e "${CYAN}========================================"
echo -e "pyNance Development Validation Script"
echo -e "========================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate TailwindCSS only usage
validate_tailwind_only() {
    echo -e "${YELLOW}[1/7] Validating TailwindCSS only usage...${NC}"
    
    local errors=0
    
    # Check if TailwindCSS config exists
    if [ ! -f "frontend/tailwind.config.js" ]; then
        echo -e "${RED}❌ TailwindCSS config not found${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ TailwindCSS config exists${NC}"
    fi
    
    # Check for custom style blocks in Vue components
    echo "Scanning for custom style blocks..."
    if grep -r "<style" frontend/src/ --include="*.vue" >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Custom style blocks found:${NC}"
        grep -r "<style" frontend/src/ --include="*.vue" | while read -r line; do
            file=$(echo "$line" | cut -d: -f1)
            echo "   - $file"
        done
        echo -e "${YELLOW}Please review these files to ensure only TailwindCSS is used${NC}"
    else
        echo -e "${GREEN}✅ No custom style blocks found${NC}"
    fi
    
    # Check for custom CSS classes (basic pattern matching)
    echo "Scanning for custom CSS classes..."
    if grep -r "class.*{" frontend/src/ --include="*.vue" --include="*.css" >/dev/null 2>&1; then
        echo -e "${RED}❌ Custom CSS classes found:${NC}"
        grep -r "class.*{" frontend/src/ --include="*.vue" --include="*.css" | head -5
        ((errors++))
    else
        echo -e "${GREEN}✅ No custom CSS classes detected${NC}"
    fi
    
    # Look for common non-TailwindCSS patterns
    echo "Checking for non-TailwindCSS patterns..."
    if grep -r -E "(\.css\s*{|#[a-zA-Z].*\s*{|\.[a-zA-Z_-]+\s*\{)" frontend/src/ --include="*.vue" --include="*.css" >/dev/null 2>&1; then
        echo -e "${RED}❌ Potential custom CSS detected${NC}"
        grep -r -E "(\.css\s*{|#[a-zA-Z].*\s*{|\.[a-zA-Z_-]+\s*\{)" frontend/src/ --include="*.vue" --include="*.css" | head -3
        ((errors++))
    else
        echo -e "${GREEN}✅ No non-TailwindCSS patterns detected${NC}"
    fi
    
    if [ $errors -gt 0 ]; then
        echo -e "${RED}❌ TailwindCSS validation failed with $errors errors${NC}"
        return 1
    else
        echo -e "${GREEN}✅ TailwindCSS validation passed${NC}"
        return 0
    fi
}

# Function to validate Python environment and tools
validate_python_env() {
    echo -e "${YELLOW}[2/7] Validating Python environment...${NC}"
    
    # Check Python version
    if python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
        echo -e "${GREEN}✅ Python 3.11+ detected${NC}"
    else
        echo -e "${RED}❌ Python 3.11+ required, found: $(python --version)${NC}"
        return 1
    fi
    
    # Check virtual environment
    if [ $CI_MODE -eq 0 ]; then
        if [ -d ".venv" ]; then
            echo -e "${GREEN}✅ Virtual environment exists${NC}"
        else
            echo -e "${RED}❌ Virtual environment missing${NC}"
            return 1
        fi
    fi
    
    # Check required tools
    local tools=("black" "ruff" "mypy" "pytest")
    if [ $CI_MODE -eq 0 ]; then
        tools+=("pre-commit")
    fi
    for tool in "${tools[@]}"; do
        if command_exists "$tool"; then
            echo -e "${GREEN}✅ $tool installed${NC}"
        else
            echo -e "${RED}❌ $tool missing${NC}"
            return 1
        fi
    done
    
    return 0
}

# Function to validate Node.js environment
validate_node_env() {
    echo -e "${YELLOW}[3/7] Validating Node.js environment...${NC}"
    
    # Check Node version
    if node --version | grep -q "v20"; then
        echo -e "${GREEN}✅ Node 20 detected${NC}"
    else
        echo -e "${YELLOW}⚠️  Node 20 recommended, found: $(node --version)${NC}"
    fi
    
    # Check if npm is available
    if command_exists npm; then
        echo -e "${GREEN}✅ npm available${NC}"
    else
        echo -e "${RED}❌ npm not found${NC}"
        return 1
    fi
    
    return 0
}

# Function to run Python linting and formatting checks
validate_python_style() {
    echo -e "${YELLOW}[4/7] Validating Python code style...${NC}"
    
    echo "Running black format check..."
    if black --check backend/; then
        echo -e "${GREEN}✅ Black formatting passed${NC}"
    else
        echo -e "${RED}❌ Black formatting failed${NC}"
        return 1
    fi
    
    echo "Running ruff check..."
    if ruff check backend/; then
        echo -e "${GREEN}✅ Ruff check passed${NC}"
    else
        echo -e "${RED}❌ Ruff check failed${NC}"
        return 1
    fi
    
    echo "Running mypy check..."
    if mypy backend/ --ignore-missing-imports; then
        echo -e "${GREEN}✅ MyPy check passed${NC}"
    else
        echo -e "${RED}❌ MyPy check failed${NC}"
        return 1
    fi
    
    return 0
}

# Function to run frontend validation
validate_frontend() {
    echo -e "${YELLOW}[5/7] Validating frontend code...${NC}"
    
    if [ ! -d "frontend" ]; then
        echo -e "${YELLOW}⚠️  Frontend directory not found, skipping${NC}"
        return 0
    fi
    
    cd frontend
    
    echo "Running ESLint..."
    if npm run lint; then
        echo -e "${GREEN}✅ ESLint passed${NC}"
    else
        echo -e "${RED}❌ ESLint failed${NC}"
        cd ..
        return 1
    fi
    
    echo "Running Prettier check..."
    if npm run format -- --check; then
        echo -e "${GREEN}✅ Prettier check passed${NC}"
    else
        echo -e "${RED}❌ Prettier check failed${NC}"
        cd ..
        return 1
    fi
    
    cd ..
    return 0
}

# Function to run tests
validate_tests() {
    echo -e "${YELLOW}[6/7] Running tests...${NC}"
    
    echo "Running Python tests..."
    if python -m pytest tests/ -v; then
        echo -e "${GREEN}✅ Python tests passed${NC}"
    else
        echo -e "${RED}❌ Python tests failed${NC}"
        return 1
    fi
    
    echo "Running model field validation..."
    if python -m pytest tests/test_model_field_validation.py -v; then
        echo -e "${GREEN}✅ Model field validation passed${NC}"
    else
        echo -e "${RED}❌ Model field validation failed${NC}"
        return 1
    fi
    
    return 0
}

# Function to run pre-commit checks
validate_precommit() {
    echo -e "${YELLOW}[7/7] Running pre-commit checks...${NC}"
    
    if [ $CI_MODE -eq 1 ]; then
        echo -e "${YELLOW}Skipping pre-commit checks in CI.${NC}"
        return 0
    fi

    if pre-commit run --all-files; then
        echo -e "${GREEN}✅ Pre-commit checks passed${NC}"
    else
        echo -e "${RED}❌ Pre-commit checks failed${NC}"
        return 1
    fi
    
    return 0
}

# Function to validate environment files
validate_env_files() {
    echo -e "${YELLOW}Validating environment files...${NC}"
    
    if [ -f "backend/.env" ]; then
        echo -e "${GREEN}✅ Backend .env exists${NC}"
    else
        echo -e "${YELLOW}⚠️  Backend .env missing (copy from backend/example.env)${NC}"
    fi
    
    if [ -f "frontend/.env" ]; then
        echo -e "${GREEN}✅ Frontend .env exists${NC}"
    else
        echo -e "${YELLOW}⚠️  Frontend .env missing (copy from frontend/example.env)${NC}"
    fi
}

# Main execution
main() {
    local exit_code=0

    for arg in "$@"; do
        if [ "$arg" = "--ci" ]; then
            CI_MODE=1
        fi
    done

    if [ "${CI:-}" = "true" ] || [ "${GITHUB_ACTIONS:-}" = "true" ]; then
        CI_MODE=1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "CONTRIBUTING.md" ] || [ ! -d "backend" ]; then
        echo -e "${RED}❌ Please run this script from the project root directory${NC}"
        exit 1
    fi
    
    # Validate environment files first (non-blocking)
    validate_env_files
    
    # Run all validations
    validate_tailwind_only || exit_code=1
    validate_python_env || exit_code=1
    validate_node_env || exit_code=1
    validate_python_style || exit_code=1
    validate_frontend || exit_code=1
    validate_tests || exit_code=1
    validate_precommit || exit_code=1
    
    echo -e "${CYAN}========================================"
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}🎉 All validations passed! Ready to commit.${NC}"
    else
        echo -e "${RED}❌ Some validations failed. Please fix the issues above.${NC}"
    fi
    echo -e "${CYAN}========================================${NC}"
    
    exit $exit_code
}

# Run main function
main "$@"
