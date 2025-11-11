#!/bin/bash

# Sleep Manager Test Runner
# This script runs the test suite for the sleep manager

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Function to check if virtual environment exists
USE_UV=0

setup_environment() {
    if command -v uv >/dev/null 2>&1; then
        USE_UV=1
        print_status "Using uv to run tests with the dev dependency group."
        return
    fi

    if [[ ! -d "$PROJECT_DIR/venv" ]]; then
        print_error "Virtual environment not found. Install dependencies with uv or create a venv:"
        print_error "  uv sync --group dev"
        print_error "  # or fallback"
        print_error "  python3 -m venv venv && source venv/bin/activate && pip install -e .[dev]"
        exit 1
    fi

    if ! "$PROJECT_DIR/venv/bin/python" -c "import pytest" 2>/dev/null; then
        print_error "pytest not found in virtual environment. Install dependencies using uv or pip:"
        print_error "  uv sync --group dev"
        print_error "  # or"
        print_error "  source venv/bin/activate && pip install -e .[dev]"
        exit 1
    fi
}

run_pytest() {
    if [[ "$USE_UV" -eq 1 ]]; then
        uv run --group dev pytest "$@"
    else
        "$PROJECT_DIR/venv/bin/python" -m pytest "$@"
    fi
}

# Function to run tests
run_tests() {
    local test_type="$1"
    local test_path="$2"
    
    print_header "Running $test_type tests..."
    
    cd "$PROJECT_DIR"
    
    case "$test_type" in
        "unit")
            run_pytest tests/test_sleeper.py tests/test_waker.py -v
            ;;
        "integration")
            run_pytest tests/test_integration.py -v
            ;;
        "all")
            run_pytest tests/ -v
            ;;
        "coverage")
            if [[ "$USE_UV" -ne 1 ]]; then
                if ! "$PROJECT_DIR/venv/bin/python" -c "import pytest_cov" 2>/dev/null; then
                    print_warning "pytest-cov not found. Installing it..."
                    "$PROJECT_DIR/venv/bin/python" -m pip install pytest-cov
                fi
            fi
            run_pytest tests/ --cov=sleep_manager --cov-report=html --cov-report=term-missing
            ;;
        "quick")
            run_pytest tests/ -x -v
            ;;
        *)
            print_error "Unknown test type: $test_type"
            exit 1
            ;;
    esac
}

# Function to show test help
show_help() {
    echo "Sleep Manager Test Runner"
    echo "========================"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  unit        Run unit tests only"
    echo "  integration Run integration tests only"
    echo "  all         Run all tests (default)"
    echo "  coverage    Run tests with coverage report"
    echo "  quick       Run tests and stop on first failure"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 unit        # Run only unit tests"
    echo "  $0 coverage    # Run tests with coverage"
    echo "  $0 quick       # Quick test run"
}

# Main script
main() {
    print_status "Sleep Manager Test Runner"
    print_status "========================="
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_DIR/pyproject.toml" ]]; then
        print_error "Not in the sleep-manager project directory"
        exit 1
    fi
    
    setup_environment
    
    # Parse command line arguments
    case "${1:-all}" in
        "unit")
            run_tests "unit"
            ;;
        "integration")
            run_tests "integration"
            ;;
        "all")
            run_tests "all"
            ;;
        "coverage")
            run_tests "coverage"
            print_status "Coverage report generated in htmlcov/index.html"
            ;;
        "quick")
            run_tests "quick"
            ;;
        "help"|"-h"|"--help")
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
    
    print_status "Tests completed successfully!"
}

# Run main function
main "$@" 
