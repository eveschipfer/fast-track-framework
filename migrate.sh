#!/bin/bash

##############################################################################
# Sprint 5.0 - The Great Refactor
# Migration Script: Separate Framework from Application
#
# This script reorganizes the codebase into:
# - framework/ftf: Generic framework code (vendor)
# - framework/fast_query: ORM package
# - workbench/app: Application-specific code
# - workbench/tests: Test suite
#
# Usage:
#   bash migrate.sh
##############################################################################

set -e  # Exit on error

echo "=========================================================================="
echo "Sprint 5.0 - The Great Refactor"
echo "Separating Framework from Application"
echo "=========================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_green() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_yellow() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_red() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if we're in the larafast directory
if [ ! -d "src/ftf" ]; then
    print_red "Error: Must run from larafast directory"
    exit 1
fi

echo "Step 1: Creating directory structure..."
echo "----------------------------------------------------------------------"

# Create framework directories
mkdir -p framework/ftf
mkdir -p framework/fast_query

# Create workbench directories
mkdir -p workbench/app/models
mkdir -p workbench/app/resources
mkdir -p workbench/app/http/controllers
mkdir -p workbench/config
mkdir -p workbench/storage/logs
mkdir -p workbench/storage/framework/cache

print_green "Directory structure created"
echo ""

echo "Step 2: Moving Framework code..."
echo "----------------------------------------------------------------------"

# Move fast_query (ORM) to framework
if [ -d "src/fast_query" ]; then
    cp -r src/fast_query/* framework/fast_query/
    print_green "Moved fast_query to framework/"
fi

# Move framework modules (generic code)
# List of framework modules to move
FRAMEWORK_MODULES=(
    "core"
    "http"
    "validation"
    "events"
    "jobs"
    "auth"
    "cache"
    "i18n"
    "schedule"
    "mail"
    "storage"
    "resources"
    "cli"
    "providers"
)

for module in "${FRAMEWORK_MODULES[@]}"; do
    if [ -d "src/ftf/$module" ]; then
        cp -r "src/ftf/$module" framework/ftf/
        print_green "Moved ftf/$module to framework/"
    fi
done

# Copy ftf package files
if [ -f "src/ftf/__init__.py" ]; then
    cp src/ftf/__init__.py framework/ftf/
    print_green "Moved ftf/__init__.py to framework/"
fi

# Copy ftf/main.py if it exists (framework entry point)
if [ -f "src/ftf/main.py" ]; then
    cp src/ftf/main.py framework/ftf/
    print_green "Moved ftf/main.py to framework/"
fi

echo ""

echo "Step 3: Moving Application code..."
echo "----------------------------------------------------------------------"

# Move models to workbench/app/models
if [ -d "src/ftf/models" ]; then
    cp -r src/ftf/models/* workbench/app/models/
    print_green "Moved models to workbench/app/models/"
fi

# Move generated resources to workbench/app/resources
if [ -d "src/ftf/resources" ]; then
    # Only move specific resource files (not the core framework files)
    for file in src/ftf/resources/*_resource.py; do
        if [ -f "$file" ]; then
            cp "$file" workbench/app/resources/
            filename=$(basename "$file")
            print_green "Moved $filename to workbench/app/resources/"
        fi
    done
fi

# Create __init__.py files for app packages
touch workbench/app/__init__.py
touch workbench/app/models/__init__.py
touch workbench/app/resources/__init__.py
touch workbench/app/http/__init__.py
touch workbench/app/http/controllers/__init__.py

print_green "Created __init__.py files for app packages"
echo ""

echo "Step 4: Moving Tests..."
echo "----------------------------------------------------------------------"

# Move entire test suite to workbench
if [ -d "tests" ]; then
    cp -r tests workbench/
    print_green "Moved tests/ to workbench/tests/"
fi

# Move test utilities
if [ -d "tests/utils" ]; then
    print_green "Test utilities preserved in workbench/tests/utils/"
fi

# Move test factories
if [ -d "tests/factories" ]; then
    print_green "Test factories preserved in workbench/tests/factories/"
fi

# Move test seeders
if [ -d "tests/seeders" ]; then
    print_green "Test seeders preserved in workbench/tests/seeders/"
fi

echo ""

echo "Step 5: Moving Examples and Documentation..."
echo "----------------------------------------------------------------------"

# Move examples to workbench
if [ -d "examples" ]; then
    cp -r examples workbench/
    print_green "Moved examples/ to workbench/examples/"
fi

# Move docs (stays at root for now)
print_yellow "Documentation stays at root level (docs/)"

echo ""

echo "Step 6: Creating Workbench Entry Point..."
echo "----------------------------------------------------------------------"

# Create workbench/main.py
cat > workbench/main.py << 'EOF'
"""
Workbench Application Entry Point

This is the main entry point for the Fast Track Framework workbench application.
The workbench is a sample application that demonstrates how to use the framework.

Usage:
    uvicorn workbench.main:app --reload
"""

from ftf.http import FastTrackFramework
from ftf.core import Container

# Import app models (registers them with SQLAlchemy)
from app.models import User, Post, Comment, Role  # noqa: F401

# Create application instance
app = FastTrackFramework()

# Get container instance
container = Container()


@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Fast Track Framework - Workbench Application",
        "version": "5.0.0",
        "framework": "ftf",
        "description": "A Laravel-inspired micro-framework built on FastAPI"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Import routes (if you have them)
# from app.http.routes import register_routes
# register_routes(app)
EOF

print_green "Created workbench/main.py"
echo ""

echo "Step 7: Creating Configuration Files..."
echo "----------------------------------------------------------------------"

# Create .env example for workbench
cat > workbench/.env.example << 'EOF'
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./workbench.db

# Framework Configuration
DEBUG=True
APP_NAME="Fast Track Framework Workbench"

# Mail Configuration
MAIL_DRIVER=log
MAIL_HOST=localhost
MAIL_PORT=1025

# Cache Configuration
CACHE_DRIVER=file
CACHE_FILE_PATH=workbench/storage/framework/cache

# Storage Configuration
FILESYSTEM_DISK=local
FILESYSTEM_ROOT=workbench/storage/app
FILESYSTEM_URL=/storage
EOF

print_green "Created workbench/.env.example"

# Create gitignore for workbench
cat > workbench/.gitignore << 'EOF'
*.db
*.db-shm
*.db-wal
storage/logs/*.log
storage/framework/cache/*
!storage/framework/cache/.gitkeep
.env
__pycache__/
*.pyc
EOF

print_green "Created workbench/.gitignore"

# Create storage .gitkeep files
touch workbench/storage/logs/.gitkeep
touch workbench/storage/framework/cache/.gitkeep

print_green "Created storage .gitkeep files"
echo ""

echo "=========================================================================="
print_green "Migration Complete!"
echo "=========================================================================="
echo ""
echo "Next Steps:"
echo "1. Run: python fix_imports.py    # Fix import statements"
echo "2. Review: pyproject.toml updates"
echo "3. Run: poetry install            # Reinstall dependencies"
echo "4. Run: poetry run pytest workbench/tests/ -v    # Run tests"
echo ""
echo "The old src/ directory is preserved for reference."
echo "After verification, you can remove it with: rm -rf src/"
echo ""
