#!/bin/bash

# MCP Catalog Installation Script
# This script installs all prerequisites and dependencies for the MCP servers in the catalog

set -e  # Exit on any error

echo "MCP Catalog Installation Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    log_info "Detected OS: $OS"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Node.js (minimum version 18)
install_nodejs() {
    log_info "Checking Node.js installation..."
    
    if command_exists node; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            log_success "Node.js $(node --version) is already installed and meets requirements (>=18)"
            return 0
        else
            log_warning "Node.js version $(node --version) is too old. Upgrading to latest LTS..."
        fi
    else
        log_info "Node.js not found. Installing Node.js LTS..."
    fi

    case $OS in
        "macos")
            if command_exists brew; then
                brew install node
            else
                log_info "Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                brew install node
            fi
            ;;
        "linux")
            # Install using NodeSource repository for latest LTS
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        "windows")
            log_warning "Please install Node.js manually from https://nodejs.org/ (version 18 or higher)"
            log_warning "Then rerun this script"
            exit 1
            ;;
    esac
    
    log_success "Node.js installed: $(node --version)"
}

# Install Python (minimum version 3.10)
install_python() {
    log_info "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
            log_success "Python $(python3 --version) is already installed and meets requirements (>=3.10)"
            return 0
        else
            log_warning "Python version $(python3 --version) is too old. Need Python 3.10+"
        fi
    else
        log_info "Python 3 not found. Installing Python 3..."
    fi

    case $OS in
        "macos")
            if command_exists brew; then
                brew install python@3.11
            else
                log_info "Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
                brew install python@3.11
            fi
            ;;
        "linux")
            sudo apt-get update
            sudo apt-get install -y python3.11 python3.11-pip python3.11-venv
            ;;
        "windows")
            log_warning "Please install Python 3.11+ manually from https://python.org/"
            log_warning "Then rerun this script"
            exit 1
            ;;
    esac
    
    log_success "Python installed: $(python3 --version)"
}

# Install uv (modern Python package manager)
install_uv() {
    log_info "Installing uv (modern Python package manager)..."
    
    if command_exists uv; then
        log_success "uv is already installed: $(uv --version)"
        return 0
    fi
    
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    
    if command_exists uv; then
        log_success "uv installed: $(uv --version)"
    else
        log_error "Failed to install uv. Please install manually from https://astral.sh/uv/"
        exit 1
    fi
}

# Install additional package managers
install_package_managers() {
    log_info "Installing additional package managers..."
    
    # Install pnpm
    if ! command_exists pnpm; then
        log_info "Installing pnpm..."
        npm install -g pnpm
        log_success "pnpm installed: $(pnpm --version)"
    else
        log_success "pnpm is already installed: $(pnpm --version)"
    fi
    
    # Install yarn (optional)
    if ! command_exists yarn; then
        log_info "Installing yarn..."
        npm install -g yarn
        log_success "yarn installed: $(yarn --version)"
    else
        log_success "yarn is already installed: $(yarn --version)"
    fi
    
    # Install tsx for TypeScript execution
    if ! command_exists tsx; then
        log_info "Installing tsx for TypeScript execution..."
        npm install -g tsx
        log_success "tsx installed: $(tsx --version)"
    else
        log_success "tsx is already installed: $(tsx --version)"
    fi
    
    # Note about bun (optional, cutting-edge)
    if ! command_exists bun; then
        log_info "Bun is not installed. It's optional but used by context7-mcp"
        log_info "To install bun: curl -fsSL https://bun.sh/install | bash"
    else
        log_success "bun is already installed: $(bun --version)"
    fi
}

# Install system dependencies
install_system_dependencies() {
    log_info "Installing system dependencies..."
    
    case $OS in
        "macos")
            if command_exists brew; then
                brew install git curl wget
            fi
            ;;
        "linux")
            sudo apt-get update
            sudo apt-get install -y git curl wget build-essential gcc
            ;;
        "windows")
            log_warning "Please ensure git, curl, and build tools are installed"
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Install Python dependencies
install_python_dependencies() {
    log_info "Installing Python dependencies from requirements.txt..."
    
    cd "$(dirname "$0")"
    
    if [ -f "requirements.txt" ]; then
        # Use uv if available, fallback to pip
        if command_exists uv; then
            log_info "Using uv to install Python dependencies..."
            uv pip install -r requirements.txt
        else
            log_info "Using pip to install Python dependencies..."
            python3 -m pip install --upgrade pip
            python3 -m pip install -r requirements.txt
        fi
        log_success "Python dependencies installed"
    else
        log_warning "requirements.txt not found in current directory"
    fi
}

# Install Node.js dependencies for TypeScript servers
install_nodejs_dependencies() {
    log_info "Installing Node.js dependencies for TypeScript servers..."
    
    cd "$(dirname "$0")"
    
    # List of Node.js servers that need dependencies installed
    NODE_SERVERS=(
        "context7-mcp"
        "dexpaprika-mcp"
        "hugeicons-mcp-server"
        "math-mcp"
        "mcp-server-nationalparks"
        "metmuseum-mcp"
        "okx-mcp"
        "mcp-google-map"
        "openapi-mcp-server"
    )
    
    for server in "${NODE_SERVERS[@]}"; do
        if [ -d "$server" ]; then
            log_info "Installing dependencies for $server..."
            cd "$server"
            
            # Special fixes for specific servers
            if [ "$server" = "hugeicons-mcp-server" ]; then
                log_info "Applying fix for hugeicons-mcp-server: installing typescript"
                npm install typescript --save-dev 2>/dev/null
            elif [ "$server" = "metmuseum-mcp" ]; then
                log_info "Applying fix for metmuseum-mcp: ensuring all dependencies"
                # Install all dependencies from package.json
                npm install
                # Install additional missing dependencies
                npm install image-to-base64 --save
                # Install TypeScript as dev dependency
                npm install typescript --save-dev
                # Try to install type definitions, if not available create a declaration file
                npm install @types/image-to-base64 --save-dev 2>/dev/null || {
                    log_info "Creating type declaration for image-to-base64"
                    mkdir -p src/types
                    cat > src/types/image-to-base64.d.ts << 'EOF'
declare module 'image-to-base64' {
    function imageToBase64(url: string): Promise<string>;
    export = imageToBase64;
}
EOF
                }
                # Compile TypeScript to generate dist folder
                npx tsc
                # Mark as already installed to skip duplicate installation
                SKIP_NPM_INSTALL=true
            elif [ "$server" = "context7-mcp" ]; then
                log_info "Applying fix for context7-mcp: installing typescript"
                npm install typescript --save-dev 2>/dev/null
            elif [ "$server" = "math-mcp" ]; then
                log_info "Applying fix for math-mcp: installing typescript"
                npm install typescript --save-dev 2>/dev/null
            elif [ "$server" = "mcp-server-nationalparks" ]; then
                log_info "Applying fix for mcp-server-nationalparks: installing typescript"
                npm install typescript --save-dev 2>/dev/null
            elif [ "$server" = "okx-mcp" ]; then
                log_info "Applying fix for okx-mcp: installing typescript"
                npm install typescript --save-dev 2>/dev/null
            elif [ "$server" = "mcp-google-map" ]; then
                log_info "Applying fix for mcp-google-map: installing typescript"
                npm install typescript --save-dev 2>/dev/null
            elif [ "$server" = "openapi-mcp-server" ]; then
                log_info "Setting up openapi-mcp-server"
                # No TypeScript needed, this is a pure JavaScript module
                # Just install the dependencies
                npm install 2>/dev/null || log_warning "npm install failed for openapi-mcp-server"
                # Make the index.js executable as per postinstall script
                chmod +x index.js 2>/dev/null || log_warning "Failed to make index.js executable"
                # Skip the standard npm install below
                SKIP_NPM_INSTALL=true
            fi
            
            # Detect package manager and install (skip if already installed)
            if [ "$SKIP_NPM_INSTALL" != "true" ]; then
                if [ -f "pnpm-lock.yaml" ]; then
                    pnpm install
                elif [ -f "yarn.lock" ]; then
                    yarn install
                elif [ -f "bun.lock" ]; then
                    if command_exists bun; then
                        bun install
                    else
                        log_warning "bun.lock found but bun not installed. Using npm instead."
                        npm install
                    fi
                else
                    npm install
                fi
            fi
            # Reset the flag for next iteration
            SKIP_NPM_INSTALL=false
            
            # Build TypeScript if build script exists
            if [ -f "package.json" ] && grep -q "\"build\"" package.json; then
                log_info "Building TypeScript for $server..."
                if [ -f "pnpm-lock.yaml" ]; then
                    pnpm run build 2>/dev/null || log_warning "Build failed for $server"
                elif [ -f "yarn.lock" ]; then
                    yarn build 2>/dev/null || log_warning "Build failed for $server"
                else
                    npm run build 2>/dev/null || log_warning "Build failed for $server"
                fi
            fi
            
            cd ..
            log_success "Processed $server"
        else
            log_warning "Server directory $server not found"
        fi
    done
}

# Install Python server dependencies
install_python_server_dependencies() {
    log_info "Installing Python server dependencies..."
    
    cd "$(dirname "$0")"
    
    # List of Python servers
    PYTHON_SERVERS=(
        "bibliomantic-mcp-server"
        "biomcp"
        "call-for-papers-mcp/call-for-papers-mcp-main"
        "car-price-mcp-main"
        "fruityvice-mcp"
        "game-trends-mcp"
        "huggingface-mcp-server"
        "mcp-nixos"
        "mcp-osint-server"
        "mcp-reddit"
        "unit-converter-mcp"
        "medcalc"
        "movie-recommender-mcp/movie-reccomender-mcp"
        "nasa-mcp"
        "paper-search-mcp"
        "scientific_computation_mcp"
        "weather_mcp"
        "wikipedia-mcp"
        "time-mcp"
    )
    
    for server in "${PYTHON_SERVERS[@]}"; do
        if [ -d "$server" ]; then
            log_info "Installing dependencies for $server..."
            cd "$server"
            
            # Special handling for unit-converter-mcp
            if [ "$server" = "unit-converter-mcp" ]; then
                log_info "Special setup for unit-converter-mcp: installing fastmcp"
                
                if command_exists uv; then
                    log_info "Installing unit-converter-mcp dependencies with uv..."
                    uv pip install fastmcp || log_warning "Failed to install fastmcp"
                    if [ -f "pyproject.toml" ]; then
                        log_info "Installing unit-converter-mcp package in editable mode..."
                        uv pip install -e . || log_warning "uv install failed for unit-converter-mcp"
                    fi
                else
                    log_warning "uv not found, installing unit-converter-mcp dependencies with pip"
                    python3 -m pip install fastmcp || log_warning "Failed to install fastmcp"
                    if [ -f "pyproject.toml" ]; then
                        python3 -m pip install -e . || log_warning "pip install failed for unit-converter-mcp"
                    fi
                fi
            # Special handling for mcp-reddit
            elif [ "$server" = "mcp-reddit" ]; then
                log_info "Special setup for mcp-reddit: checking Python version compatibility"
                
                # First, fix Python version requirement if needed
                if [ -f "pyproject.toml" ]; then
                    # Check if Python version requirement is too high
                    if grep -q 'requires-python = ">=3.11"' pyproject.toml; then
                        log_info "Adjusting Python version requirement from 3.11 to 3.10 for compatibility..."
                        sed -i.bak 's/requires-python = ">=3.11"/requires-python = ">=3.10"/' pyproject.toml || \
                        sed -i '' 's/requires-python = ">=3.11"/requires-python = ">=3.10"/' pyproject.toml 2>/dev/null
                    fi
                fi
                
                if command_exists uv; then
                    log_info "Installing mcp-reddit dependencies with uv..."
                    uv pip install redditwarp fastmcp dnspython praw uvicorn hatchling || log_warning "Some dependencies may have failed"
                    if [ -f "pyproject.toml" ]; then
                        log_info "Installing mcp-reddit package in editable mode..."
                        uv pip install -e . || log_warning "uv install failed for mcp-reddit"
                    fi
                else
                    log_warning "uv not found, installing mcp-reddit dependencies with pip"
                    python3 -m pip install redditwarp fastmcp dnspython praw uvicorn hatchling || log_warning "Some dependencies may have failed"
                    if [ -f "pyproject.toml" ]; then
                        python3 -m pip install -e . || log_warning "pip install failed for mcp-reddit"
                    fi
                fi
            # Special handling for time-mcp
            elif [ "$server" = "time-mcp" ]; then
                log_info "Special setup for time-mcp: installing mcp-server-time"
                
                if command_exists uv; then
                    log_info "Installing time-mcp dependencies with uv..."
                    uv pip install mcp pydantic tzdata tzlocal || log_warning "Failed to install dependencies"
                    if [ -f "pyproject.toml" ]; then
                        log_info "Installing time-mcp package in editable mode..."
                        uv pip install -e . || log_warning "uv install failed for time-mcp"
                    fi
                else
                    log_warning "uv not found, installing time-mcp dependencies with pip"
                    python3 -m pip install mcp pydantic tzdata tzlocal || log_warning "Failed to install dependencies"
                    if [ -f "pyproject.toml" ]; then
                        python3 -m pip install -e . || log_warning "pip install failed for time-mcp"
                    fi
                fi
            # Standard installation for other servers
            elif [ -f "uv.lock" ] && command_exists uv; then
                uv sync 2>/dev/null || log_warning "uv sync failed for $server"
            elif [ -f "pyproject.toml" ] && command_exists uv; then
                uv pip install -e . 2>/dev/null || log_warning "uv install failed for $server"
            elif [ -f "requirements.txt" ]; then
                if command_exists uv; then
                    uv pip install -r requirements.txt 2>/dev/null || log_warning "uv pip install failed for $server"
                else
                    python3 -m pip install -r requirements.txt 2>/dev/null || log_warning "pip install failed for $server"
                fi
            fi
            
            cd - >/dev/null
            log_success "Processed $server"
        else
            log_warning "Server directory $server not found"
        fi
    done
}

# Setup environment variables
setup_environment() {
    log_info "environment variables..."
    
    cd "$(dirname "$0")"
    
    if [ -f "api_key" ]; then
        log_info "API key template found. Please edit api_key file with your actual API keys:"
        log_info "- NPS_API_KEY: Get from https://www.nps.gov/subjects/developer/"
        log_info "- ALPHAGENOME_API_KEY: For biomedical research (optional)"
        log_info "- CBIO_TOKEN: For cBioPortal access (optional)"
        log_info "- NASA_API_KEY: Get from https://api.nasa.gov/"
        log_info "- GOOGLE_MAPS_API_KEY: Get from https://console.cloud.google.com/apis/credentials"
        log_info "- HF_TOKEN: Get from https://huggingface.co/docs/hub/security-tokens"

        log_warning ""
    fi
}

# Main installation function
main() {
    log_info "Starting MCP Catalog installation..."
    
    detect_os
    install_nodejs
    install_python
    install_uv
    install_system_dependencies
    install_package_managers
    install_python_dependencies
    install_nodejs_dependencies
    install_python_server_dependencies
    setup_environment
    
    echo ""
    log_success "MCP Catalog installation completed!"
    echo ""
    log_info "Next steps: "
    echo "1. Edit the api_key file with your actual API keys"
    echo "2. Source environment variables: source api_key"
    echo "3. Run individual servers using commands from commands.json"
    echo "4. Test with MCP Inspector: npx @modelcontextprotocol/inspector"
    echo ""
    log_info "For troubleshooting, check individual server READMEs in their respective directories"
}

# Run main function
main "$@"