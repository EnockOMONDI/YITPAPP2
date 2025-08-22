#!/bin/bash
# Static File Cleanup Script for YITP

echo "🔧 YITP Static File Cleanup"
echo "=========================="

# Remove any custom admin static files that conflict
echo "Checking for custom admin static files..."

# Check common locations for duplicate admin files
STATIC_DIRS=(
    "static/admin"
    "*/static/admin"
    "staticfiles/admin"
)

for dir in "${STATIC_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "Found admin static directory: $dir"
        echo "Please review and remove if it contains outdated Django admin files"
    fi
done

# Clean up any .pyc files that might interfere
echo "Cleaning Python cache files..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Clear existing collected static files
echo "Clearing existing staticfiles..."
if [ -d "staticfiles" ]; then
    rm -rf staticfiles/*
fi

echo "✅ Cleanup complete. Run 'python manage.py collectstatic' to rebuild."
