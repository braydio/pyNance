#!/usr/bin/env bash

# TailwindCSS validation script for pyNance
# Ensures only TailwindCSS syntax is used for styling

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FRONTEND_DIR="frontend/src"
ERRORS=0

echo "🎨 TailwindCSS Validation Script"
echo "================================"

# Function to log error
log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((ERRORS++))
}

# Function to log warning
log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to log success
log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    log_error "Frontend source directory not found: $FRONTEND_DIR"
    exit 1
fi

# Check if TailwindCSS config exists
if [ ! -f "frontend/tailwind.config.js" ]; then
    log_error "TailwindCSS config not found: frontend/tailwind.config.js"
else
    log_success "TailwindCSS config exists"
fi

echo ""
echo "Scanning Vue components for custom CSS usage..."

# 1. Check for <style> blocks with custom CSS
echo "1. Checking for custom style blocks..."
STYLE_BLOCKS_FOUND=0
while IFS= read -r -d '' file; do
    if grep -l "<style" "$file" >/dev/null 2>&1; then
        echo "   Found style block in: $file"
        ((STYLE_BLOCKS_FOUND++))
        
        # Check if the style block contains scoped attribute
        if grep -l "<style scoped" "$file" >/dev/null 2>&1; then
            log_warning "Scoped style block found in $file - ensure only TailwindCSS is used"
        fi
        
        # Check for CSS rules (basic detection)
        if grep -E "^\s*\.[a-zA-Z_-]+\s*\{|^\s*#[a-zA-Z_-]+\s*\{|^\s*[a-zA-Z]+\s*\{" "$file" >/dev/null 2>&1; then
            log_error "Custom CSS rules detected in $file"
            echo "   Problematic lines:"
            grep -n -E "^\s*\.[a-zA-Z_-]+\s*\{|^\s*#[a-zA-Z_-]+\s*\{|^\s*[a-zA-Z]+\s*\{" "$file" | head -3
        fi
    fi
done < <(find "$FRONTEND_DIR" -name "*.vue" -print0)

if [ $STYLE_BLOCKS_FOUND -eq 0 ]; then
    log_success "No custom style blocks found"
fi

echo ""

# 2. Check for CSS files in src directory
echo "2. Checking for standalone CSS files..."
CSS_FILES_FOUND=0
while IFS= read -r -d '' file; do
    echo "   Found CSS file: $file"
    ((CSS_FILES_FOUND++))
    
    # Check if it's a valid TailwindCSS file (contains @tailwind directives)
    if grep -E "@tailwind|@apply" "$file" >/dev/null 2>&1; then
        log_success "Valid TailwindCSS file: $file"
    else
        log_error "Non-TailwindCSS CSS file found: $file"
    fi
done < <(find "$FRONTEND_DIR" -name "*.css" -print0)

if [ $CSS_FILES_FOUND -eq 0 ]; then
    log_success "No standalone CSS files found"
fi

echo ""

# 3. Check for style attributes with custom CSS
echo "3. Checking for inline style attributes with custom CSS..."
INLINE_STYLES_FOUND=0
while IFS= read -r -d '' file; do
    if grep -l "style=" "$file" >/dev/null 2>&1; then
        # Check if style attribute contains CSS properties (not just TailwindCSS variables)
        if grep -E "style=\"[^\"]*:[^\"]*\"" "$file" >/dev/null 2>&1; then
            echo "   Found inline styles in: $file"
            ((INLINE_STYLES_FOUND++))
            log_warning "Inline CSS styles found in $file - consider using TailwindCSS classes"
            # Show some examples
            grep -n -E "style=\"[^\"]*:[^\"]*\"" "$file" | head -2
        fi
    fi
done < <(find "$FRONTEND_DIR" -name "*.vue" -print0)

if [ $INLINE_STYLES_FOUND -eq 0 ]; then
    log_success "No problematic inline styles found"
fi

echo ""

# 4. Check for common CSS-in-JS patterns
echo "4. Checking for CSS-in-JS patterns..."
CSSINJS_FOUND=0
while IFS= read -r -d '' file; do
    # Look for object-style CSS definitions
    if grep -E "(styles?\s*=\s*\{|css\s*=\s*\{|\.[a-zA-Z_-]+\s*=\s*\{[^}]*color:|[^}]*background:|[^}]*margin:|[^}]*padding:)" "$file" >/dev/null 2>&1; then
        echo "   Found potential CSS-in-JS in: $file"
        ((CSSINJS_FOUND++))
        log_warning "Potential CSS-in-JS pattern found in $file"
    fi
done < <(find "$FRONTEND_DIR" -name "*.vue" -name "*.js" -name "*.ts" -print0)

if [ $CSSINJS_FOUND -eq 0 ]; then
    log_success "No CSS-in-JS patterns found"
fi

echo ""

# 5. Check for imported CSS files
echo "5. Checking for CSS imports..."
CSS_IMPORTS_FOUND=0
while IFS= read -r -d '' file; do
    if grep -E "import.*\.css|require.*\.css" "$file" >/dev/null 2>&1; then
        echo "   Found CSS import in: $file"
        ((CSS_IMPORTS_FOUND++))
        grep -n -E "import.*\.css|require.*\.css" "$file"
        
        # Check if it's importing main TailwindCSS file or custom CSS
        if grep -E "import.*['\"].*tailwind|import.*['\"].*main\.css|import.*['\"].*index\.css" "$file" >/dev/null 2>&1; then
            log_success "Valid TailwindCSS import in $file"
        else
            log_warning "Custom CSS import found in $file - verify it only contains TailwindCSS"
        fi
    fi
done < <(find "$FRONTEND_DIR" -name "*.vue" -name "*.js" -name "*.ts" -print0)

if [ $CSS_IMPORTS_FOUND -eq 0 ]; then
    log_success "No CSS imports found"
fi

echo ""

# 6. Validate TailwindCSS class usage patterns
echo "6. Validating TailwindCSS class patterns..."
INVALID_CLASSES_FOUND=0

# Common non-TailwindCSS class patterns to flag
NON_TAILWIND_PATTERNS=(
    "\.btn[^-]"           # Bootstrap-style button classes
    "\.form-control"      # Bootstrap form classes
    "\.container[^-]"     # Generic container classes
    "\.row[^-]"          # Bootstrap row classes
    "\.col-[0-9]"        # Bootstrap column classes (not TailwindCSS)
    "\.navbar"           # Bootstrap navbar
    "\.card[^-]"         # Generic card classes
    "\.modal[^-]"        # Generic modal classes
)

while IFS= read -r -d '' file; do
    for pattern in "${NON_TAILWIND_PATTERNS[@]}"; do
        if grep -E "$pattern" "$file" >/dev/null 2>&1; then
            if [ $INVALID_CLASSES_FOUND -eq 0 ]; then
                echo "   Checking for non-TailwindCSS class patterns..."
            fi
            log_warning "Potential non-TailwindCSS class pattern '$pattern' found in $file"
            ((INVALID_CLASSES_FOUND++))
        fi
    done
done < <(find "$FRONTEND_DIR" -name "*.vue" -print0)

if [ $INVALID_CLASSES_FOUND -eq 0 ]; then
    log_success "No non-TailwindCSS class patterns detected"
fi

echo ""

# Final report
echo "================================"
echo "TailwindCSS Validation Summary"
echo "================================"

if [ $ERRORS -eq 0 ]; then
    log_success "All TailwindCSS validation checks passed!"
    echo ""
    echo "✨ Your code follows TailwindCSS-only styling guidelines."
    exit 0
else
    log_error "Found $ERRORS TailwindCSS validation errors"
    echo ""
    echo "Please fix the issues above to ensure only TailwindCSS is used for styling."
    echo ""
    echo "Guidelines:"
    echo "• Use TailwindCSS utility classes instead of custom CSS"
    echo "• Avoid <style> blocks with custom CSS rules"
    echo "• Use TailwindCSS's @apply directive if component styles are needed"
    echo "• Remove inline style attributes with CSS properties"
    echo "• Consider using TailwindCSS's component layer for reusable styles"
    echo ""
    echo "For more information, see the TailwindCSS documentation:"
    echo "https://tailwindcss.com/docs"
    
    exit 1
fi
