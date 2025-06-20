#!/bin/bash

# Sleep Manager Documentation Builder
# This script builds the API documentation from docstrings using Sphinx

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCS_DIR="$PROJECT_DIR/docs"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to show usage
show_usage() {
    echo "Sleep Manager Documentation Builder"
    echo "=================================="
    echo
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  build      Build the documentation (default)"
    echo "  clean      Clean the build directory"
    echo "  serve      Build and serve documentation locally"
    echo "  check      Check for documentation issues"
    echo "  help       Show this help message"
    echo
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 serve"
    echo "  $0 clean"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if we're in the right directory
    if [[ ! -f "$PROJECT_DIR/pyproject.toml" ]]; then
        print_error "Not in the sleep-manager project directory"
        exit 1
    fi
    
    # Check if docs directory exists
    if [[ ! -d "$DOCS_DIR" ]]; then
        print_error "Documentation directory not found: $DOCS_DIR"
        exit 1
    fi
    
    # Check if sphinx-build is available
    if ! command_exists sphinx-build; then
        print_error "sphinx-build not found. Please install Sphinx:"
        print_error "  pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints myst-parser"
        exit 1
    fi
    
    # Check if Python modules are available
    if ! python3 -c "import sleep_manager" 2>/dev/null; then
        print_warning "sleep_manager module not found. Installing in development mode..."
        cd "$PROJECT_DIR"
        pip install -e .
    fi
    
    print_status "Prerequisites check passed"
}

# Function to build documentation
build_docs() {
    print_status "Building documentation..."
    
    cd "$DOCS_DIR"
    
    # Create build directory if it doesn't exist
    mkdir -p _build
    
    # Build HTML documentation
    print_status "Generating HTML documentation..."
    sphinx-build -b html . _build/html
    
    # Build PDF documentation (if available)
    if command_exists pdflatex; then
        print_status "Generating PDF documentation..."
        sphinx-build -b latex . _build/latex
        cd _build/latex
        make
        cd "$DOCS_DIR"
    else
        print_warning "pdflatex not found. Skipping PDF generation."
    fi
    
    print_status "Documentation built successfully!"
    print_status "HTML documentation: $DOCS_DIR/_build/html/index.html"
    if [[ -f "$DOCS_DIR/_build/latex/sleep-manager.pdf" ]]; then
        print_status "PDF documentation: $DOCS_DIR/_build/latex/sleep-manager.pdf"
    fi
}

# Function to clean build directory
clean_docs() {
    print_status "Cleaning build directory..."
    
    cd "$DOCS_DIR"
    
    if [[ -d "_build" ]]; then
        rm -rf _build
        print_status "Build directory cleaned"
    else
        print_status "No build directory to clean"
    fi
}

# Function to serve documentation locally
serve_docs() {
    print_status "Building and serving documentation..."
    
    # Build the documentation first
    build_docs
    
    # Check if we have a simple HTTP server
    if command_exists python3; then
        print_status "Starting local server at http://localhost:8000"
        print_status "Press Ctrl+C to stop the server"
        cd "$DOCS_DIR/_build/html"
        python3 -m http.server 8000
    else
        print_error "No HTTP server available. Please open $DOCS_DIR/_build/html/index.html in your browser"
    fi
}

# Function to check documentation
check_docs() {
    print_status "Checking documentation for issues..."
    
    cd "$DOCS_DIR"
    
    # Check for broken links
    print_status "Checking for broken links..."
    sphinx-build -b linkcheck . _build/linkcheck
    
    # Check for spelling errors (if available)
    if command_exists sphinx-build; then
        print_status "Checking for spelling errors..."
        sphinx-build -b spelling . _build/spelling
    else
        print_warning "Spelling check not available"
    fi
    
    # Check for coverage
    print_status "Checking documentation coverage..."
    sphinx-build -b coverage . _build/coverage
    
    print_status "Documentation check completed"
}

# Function to update API documentation
update_api_docs() {
    print_status "Updating API documentation from docstrings..."
    
    # This function could be extended to automatically update
    # the API documentation files based on the current code
    
    print_status "API documentation is automatically generated from docstrings"
    print_status "No manual updates needed"
}

# Main script
main() {
    # Parse command line arguments
    if [[ $# -eq 0 ]]; then
        action="build"
    else
        action="$1"
    fi
    
    case "$action" in
        build)
            check_prerequisites
            build_docs
            ;;
        clean)
            clean_docs
            ;;
        serve)
            check_prerequisites
            serve_docs
            ;;
        check)
            check_prerequisites
            check_docs
            ;;
        update)
            update_api_docs
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown action: $action"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@" 