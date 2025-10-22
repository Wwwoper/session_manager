#!/bin/bash
# Script to run Session Manager tests

set -e

echo "🧪 Running Session Manager Tests"
echo "=================================="
echo

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Consider activating: source venv/bin/activate"
    echo
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing..."
    pip install pytest pytest-cov
    echo
fi

# Run tests based on argument
case "${1:-all}" in
    "all")
        echo "📦 Running all tests..."
        pytest
        ;;
    "unit")
        echo "🔬 Running unit tests only..."
        pytest -m unit
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        pytest -m integration
        ;;
    "coverage")
        echo "📊 Running tests with detailed coverage..."
        pytest --cov-report=term-missing --cov-report=html
        echo
        echo "📄 Coverage report saved to htmlcov/index.html"
        ;;
    "fast")
        echo "⚡ Running fast tests only..."
        pytest -m "not slow" -x
        ;;
    "watch")
        echo "👀 Running tests in watch mode..."
        pytest-watch
        ;;
    "core")
        echo "🔧 Running core module tests..."
        pytest tests/test_core/
        ;;
    *)
        echo "Usage: $0 [all|unit|integration|coverage|fast|watch|core]"
        exit 1
        ;;
esac

echo
echo "✅ Tests completed!"