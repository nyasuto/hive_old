#!/bin/bash

# =============================================================================
# Hive Dependencies Check Script
# 
# Comprehensive verification of system requirements and dependencies
# =============================================================================

set -euo pipefail

# =============================================================================
# Configuration
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# Utility Functions
# =============================================================================

print_header() {
    echo -e "${PURPLE}=================================${NC}"
    echo -e "${PURPLE}🐝 Hive Dependencies Check${NC}"
    echo -e "${PURPLE}=================================${NC}"
    echo
}

print_section() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "--------------------------------"
}

check_ok() {
    echo -e "  ${GREEN}✅ $1${NC}"
}

check_warn() {
    echo -e "  ${YELLOW}⚠️  $1${NC}"
}

check_error() {
    echo -e "  ${RED}❌ $1${NC}"
}

check_info() {
    echo -e "  ${CYAN}ℹ️  $1${NC}"
}

# =============================================================================
# System Requirements Check
# =============================================================================

check_system_requirements() {
    print_section "System Requirements"
    
    # OS Detection
    if [[ "$OSTYPE" == "darwin"* ]]; then
        check_ok "Operating System: macOS"
        OS_TYPE="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        check_ok "Operating System: Linux"
        OS_TYPE="linux"
    else
        check_warn "Operating System: $OSTYPE (not fully tested)"
        OS_TYPE="unknown"
    fi
    
    # Architecture
    ARCH=$(uname -m)
    if [[ "$ARCH" == "x86_64" || "$ARCH" == "arm64" ]]; then
        check_ok "Architecture: $ARCH"
    else
        check_warn "Architecture: $ARCH (may have compatibility issues)"
    fi
    
    # Memory
    if command -v free >/dev/null 2>&1; then
        MEMORY_KB=$(free -k | grep '^Mem:' | awk '{print $2}')
        MEMORY_GB=$((MEMORY_KB / 1024 / 1024))
    elif command -v vm_stat >/dev/null 2>&1; then
        MEMORY_BYTES=$(sysctl -n hw.memsize)
        MEMORY_GB=$((MEMORY_BYTES / 1024 / 1024 / 1024))
    else
        MEMORY_GB=0
    fi
    
    if [[ $MEMORY_GB -ge 8 ]]; then
        check_ok "Memory: ${MEMORY_GB}GB (sufficient)"
    elif [[ $MEMORY_GB -ge 4 ]]; then
        check_warn "Memory: ${MEMORY_GB}GB (minimum, 8GB+ recommended)"
    else
        check_warn "Memory: Could not detect or insufficient"
    fi
    
    # Disk Space
    DISK_AVAIL=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4}')
    check_info "Available disk space: $DISK_AVAIL"
    
    echo
}

# =============================================================================
# Core Dependencies Check
# =============================================================================

check_core_dependencies() {
    print_section "Core Dependencies"
    
    local missing_deps=()
    
    # tmux
    if command -v tmux >/dev/null 2>&1; then
        TMUX_VERSION=$(tmux -V | sed 's/tmux //')
        TMUX_MAJOR=$(echo "$TMUX_VERSION" | cut -d. -f1)
        TMUX_MINOR=$(echo "$TMUX_VERSION" | cut -d. -f2)
        
        if [[ $TMUX_MAJOR -gt 3 || ($TMUX_MAJOR -eq 3 && $TMUX_MINOR -ge 0) ]]; then
            check_ok "tmux: $TMUX_VERSION"
        else
            check_warn "tmux: $TMUX_VERSION (version 3.0+ recommended)"
        fi
    else
        check_error "tmux: Not installed"
        missing_deps+=("tmux")
    fi
    
    # Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | sed 's/Python //')
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        
        if [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -ge 9 ]]; then
            check_ok "Python: $PYTHON_VERSION"
        else
            check_warn "Python: $PYTHON_VERSION (version 3.9+ recommended)"
        fi
    else
        check_error "Python 3: Not installed"
        missing_deps+=("python3")
    fi
    
    # Git
    if command -v git >/dev/null 2>&1; then
        GIT_VERSION=$(git --version | sed 's/git version //')
        check_ok "Git: $GIT_VERSION"
    else
        check_error "Git: Not installed"
        missing_deps+=("git")
    fi
    
    # Claude Code
    if command -v claude-code >/dev/null 2>&1; then
        CLAUDE_VERSION=$(claude-code --version 2>/dev/null || echo "unknown")
        check_ok "Claude Code: $CLAUDE_VERSION"
        
        # Check authentication
        if claude-code auth status >/dev/null 2>&1; then
            check_ok "Claude Code: Authenticated"
        else
            check_warn "Claude Code: Not authenticated (run: claude-code auth login)"
        fi
    else
        check_error "Claude Code: Not installed"
        missing_deps+=("claude-code")
    fi
    
    # Show installation instructions for missing dependencies
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        echo
        echo -e "${YELLOW}Missing dependencies installation:${NC}"
        
        if [[ "$OS_TYPE" == "macos" ]]; then
            echo "# macOS (using Homebrew):"
            for dep in "${missing_deps[@]}"; do
                case $dep in
                    tmux) echo "brew install tmux" ;;
                    python3) echo "brew install python3" ;;
                    git) echo "brew install git" ;;
                    claude-code) echo "# Download from https://claude.ai/code" ;;
                esac
            done
        elif [[ "$OS_TYPE" == "linux" ]]; then
            echo "# Ubuntu/Debian:"
            for dep in "${missing_deps[@]}"; do
                case $dep in
                    tmux) echo "sudo apt install tmux" ;;
                    python3) echo "sudo apt install python3 python3-pip" ;;
                    git) echo "sudo apt install git" ;;
                    claude-code) echo "# Download from https://claude.ai/code" ;;
                esac
            done
        fi
    fi
    
    echo
}

# =============================================================================
# Python Environment Check
# =============================================================================

check_python_environment() {
    print_section "Python Environment"
    
    # Python path and modules
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_PATH=$(which python3)
        check_info "Python executable: $PYTHON_PATH"
        
        # Virtual environment detection
        if [[ -n "${VIRTUAL_ENV:-}" ]]; then
            check_ok "Virtual environment: $VIRTUAL_ENV"
        elif [[ -d "$PROJECT_ROOT/.venv" ]]; then
            check_warn "Virtual environment detected but not activated: $PROJECT_ROOT/.venv"
            check_info "Activate with: source .venv/bin/activate"
        else
            check_warn "No virtual environment detected (recommended for isolation)"
        fi
        
        # PYTHONPATH
        if [[ -n "${PYTHONPATH:-}" ]]; then
            check_info "PYTHONPATH: $PYTHONPATH"
        else
            check_warn "PYTHONPATH not set (add project root: export PYTHONPATH=\"$PROJECT_ROOT:\$PYTHONPATH\")"
        fi
        
        # Pip
        if python3 -m pip --version >/dev/null 2>&1; then
            PIP_VERSION=$(python3 -m pip --version | awk '{print $2}')
            check_ok "pip: $PIP_VERSION"
        else
            check_error "pip: Not available"
        fi
        
        # Test Hive module imports
        echo
        check_info "Testing Hive module imports..."
        
        cd "$PROJECT_ROOT"
        
        # Legacy modules removed - test current architecture modules
        if python3 -c "import sys; sys.path.insert(0, 'scripts'); import hive_cli" 2>/dev/null; then
            check_ok "hive_cli module: Available"
        else
            check_error "hive_cli module: Import failed"
        fi
        
        if python3 -c "import sys; sys.path.insert(0, 'scripts'); import worker_communication" 2>/dev/null; then
            check_ok "worker_communication module: Available"
        else
            check_error "worker_communication module: Import failed"
        fi
        
        if python3 -c "import sys; sys.path.insert(0, 'scripts'); import hive_watch" 2>/dev/null; then
            check_ok "hive_watch module: Available"
        else
            check_error "hive_watch module: Import failed"
        fi
        
    else
        check_error "Python 3 not available for environment check"
    fi
    
    echo
}

# =============================================================================
# Dependencies File Check
# =============================================================================

check_project_dependencies() {
    print_section "Project Dependencies"
    
    cd "$PROJECT_ROOT"
    
    # Requirements files
    if [[ -f "requirements.txt" ]]; then
        check_ok "requirements.txt: Found"
        
        # Check if requirements are installed
        if python3 -m pip check >/dev/null 2>&1; then
            check_ok "Python packages: All dependencies satisfied"
        else
            check_warn "Python packages: Some dependencies may be missing"
            check_info "Install with: pip install -r requirements.txt"
        fi
        
        # List key dependencies
        echo "  Key dependencies:"
        if grep -q "pytest" requirements.txt; then
            check_info "    pytest (testing)"
        fi
        if grep -q "ruff" requirements.txt; then
            check_info "    ruff (linting)"
        fi
        if grep -q "mypy" requirements.txt; then
            check_info "    mypy (type checking)"
        fi
        
    else
        check_warn "requirements.txt: Not found"
    fi
    
    # Development dependencies
    if [[ -f "requirements-dev.txt" ]]; then
        check_ok "requirements-dev.txt: Found"
    else
        check_warn "requirements-dev.txt: Not found"
    fi
    
    echo
}

# =============================================================================
# Directory Structure Check
# =============================================================================

check_directory_structure() {
    print_section "Directory Structure"
    
    cd "$PROJECT_ROOT"
    
    # Core directories
    local core_dirs=("workers" "scripts" "tests" "docs" "config" "templates" "web")
    
    for dir in "${core_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            check_ok "Directory: $dir/"
        else
            check_error "Directory: $dir/ (missing)"
        fi
    done
    
    # Hive runtime directories
    local hive_dirs=(".hive" ".hive/logs" ".hive/worker_data")
    
    echo
    check_info "Hive runtime directories:"
    for dir in "${hive_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            check_ok "$dir/"
        else
            check_warn "$dir/ (will be created on startup)"
        fi
    done
    
    # Script permissions
    echo
    check_info "Script permissions:"
    for script in scripts/*.sh; do
        if [[ -x "$script" ]]; then
            check_ok "$(basename "$script"): Executable"
        else
            check_warn "$(basename "$script"): Not executable (run: chmod +x $script)"
        fi
    done
    
    echo
}

# =============================================================================
# Configuration Check
# =============================================================================

check_configuration() {
    print_section "Configuration"
    
    cd "$PROJECT_ROOT"
    
    # Project configuration files
    local config_files=("pyproject.toml" "Makefile" "CLAUDE.md")
    
    for file in "${config_files[@]}"; do
        if [[ -f "$file" ]]; then
            check_ok "Config: $file"
        else
            check_warn "Config: $file (missing)"
        fi
    done
    
    # tmux configuration
    if [[ -f "$HOME/.tmux.conf" ]]; then
        check_ok "tmux config: ~/.tmux.conf exists"
    else
        check_info "tmux config: ~/.tmux.conf not found (optional)"
    fi
    
    # Claude Code configuration
    if [[ -f "$HOME/.claude/config.json" ]]; then
        check_ok "Claude Code config: ~/.claude/config.json exists"
        
        # Check permissions
        CLAUDE_PERMS=$(stat -c "%a" "$HOME/.claude/config.json" 2>/dev/null || stat -f "%A" "$HOME/.claude/config.json" 2>/dev/null || echo "unknown")
        if [[ "$CLAUDE_PERMS" == "600" ]]; then
            check_ok "Claude Code config: Secure permissions (600)"
        else
            check_warn "Claude Code config: Permissions $CLAUDE_PERMS (should be 600)"
        fi
    else
        check_warn "Claude Code config: ~/.claude/config.json not found"
    fi
    
    echo
}

# =============================================================================
# Performance Check
# =============================================================================

check_performance() {
    print_section "Performance Check"
    
    cd "$PROJECT_ROOT"
    
    # File system performance
    check_info "Testing file system performance..."
    
    TEST_DIR=".hive/test_performance"
    mkdir -p "$TEST_DIR"
    
    # File creation test
    start_time=$(date +%s%N)
    for i in {1..100}; do
        echo "test" > "$TEST_DIR/test_$i.txt"
    done
    end_time=$(date +%s%N)
    
    file_create_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
    
    if [[ $file_create_time -lt 1000 ]]; then
        check_ok "File creation: ${file_create_time}ms (good)"
    elif [[ $file_create_time -lt 5000 ]]; then
        check_warn "File creation: ${file_create_time}ms (acceptable)"
    else
        check_warn "File creation: ${file_create_time}ms (slow, may impact performance)"
    fi
    
    # Cleanup
    rm -rf "$TEST_DIR"
    
    # Memory usage simulation
    check_info "Testing basic Python operations..."
    
    if python3 -c "
import time
start = time.time()
data = [i for i in range(10000)]
result = sum(data)
end = time.time()
print(f'Python performance: {(end-start)*1000:.1f}ms')
" 2>/dev/null; then
        check_ok "Python performance: Functional"
    else
        check_warn "Python performance: Could not test"
    fi
    
    echo
}

# =============================================================================
# Integration Test
# =============================================================================

run_integration_test() {
    print_section "Integration Test"
    
    cd "$PROJECT_ROOT"
    
    check_info "Running basic integration test..."
    
    # Test current architecture functionality
    INTEGRATION_TEST_RESULT=$(python3 << 'EOF'
import sys
import os

try:
    # Add scripts directory to path
    scripts_dir = os.path.join(os.getcwd(), 'scripts')
    sys.path.insert(0, scripts_dir)
    
    import hive_cli
    import worker_communication
    import hive_watch
    
    # Test basic module initialization
    cli = hive_cli.HiveCLI()
    print("✅ Current architecture integration: SUCCESS")
    print("✅ hive_cli module: Functional")
    print("✅ worker_communication module: Available")
    print("✅ hive_watch module: Available")
    
    # Cleanup
    os.chdir(original_cwd)
    import shutil
    shutil.rmtree(temp_dir)
    
    print("✅ Integration test: PASSED")

except ImportError as e:
    print(f"❌ Integration test: FAILED - Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Integration test: FAILED - {e}")
    sys.exit(1)
EOF
)

    echo "$INTEGRATION_TEST_RESULT"
    
    if echo "$INTEGRATION_TEST_RESULT" | grep -q "Integration test: PASSED"; then
        check_ok "Integration test: All systems functional"
    else
        check_error "Integration test: Failed - see output above"
    fi
    
    echo
}

# =============================================================================
# Summary and Recommendations
# =============================================================================

print_summary() {
    print_section "Summary and Recommendations"
    
    echo -e "${GREEN}🎉 Dependency check completed!${NC}"
    echo
    
    echo "📋 Quick Setup Commands:"
    echo
    
    if [[ "$OS_TYPE" == "macos" ]]; then
        cat << 'EOF'
# macOS Setup:
brew install tmux python3 git
pip3 install -r requirements.txt
export PYTHONPATH="$PWD:$PYTHONPATH"
chmod +x scripts/*.sh
EOF
    elif [[ "$OS_TYPE" == "linux" ]]; then
        cat << 'EOF'
# Linux Setup:
sudo apt install tmux python3 python3-pip git
pip3 install -r requirements.txt
export PYTHONPATH="$PWD:$PYTHONPATH"
chmod +x scripts/*.sh
EOF
    fi
    
    echo
    echo "🚀 Next Steps:"
    echo "1. Install any missing dependencies shown above"
    echo "2. Run: ./scripts/start-small-hive.sh"
    echo "3. Test with: python3 scripts/hive_cli.py status"
    echo "4. Check documentation: docs/setup-guide.md"
    echo
    
    echo -e "${CYAN}📚 Useful Commands:${NC}"
    echo "  make help                    # Show all available commands"
    echo "  make quality                 # Run quality checks"
    echo "  make test                    # Run test suite"
    echo "  ./scripts/start-small-hive.sh  # Start Hive"
    echo "  python3 scripts/hive_cli.py status    # Test current system"
    echo
    
    echo -e "${PURPLE}🍯 Happy coding with Hive!${NC}"
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    print_header
    
    check_system_requirements
    check_core_dependencies
    check_python_environment
    check_project_dependencies
    check_directory_structure
    check_configuration
    check_performance
    run_integration_test
    print_summary
}

# Run main function
main "$@"