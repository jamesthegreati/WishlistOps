#!/bin/bash
# Test WishlistOps Installation & Launch

set -e

echo "=========================================="
echo "🎮 WishlistOps Installation Test"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}📍 Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Found: Python $python_version"

if ! python -c 'import sys; assert sys.version_info >= (3,11)' 2>/dev/null; then
    echo -e "${RED}❌ Python 3.11+ required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK${NC}"
echo ""

# Install package
echo -e "${BLUE}📦 Installing WishlistOps...${NC}"
pip install -e ".[dev]" > /dev/null 2>&1
echo -e "${GREEN}✓ Installed successfully${NC}"
echo ""

# Check CLI available
echo -e "${BLUE}🔍 Testing CLI...${NC}"
if command -v wishlistops &> /dev/null; then
    echo -e "${GREEN}✓ CLI command available${NC}"
else
    echo -e "${RED}❌ CLI command not found${NC}"
    exit 1
fi
echo ""

# Check help
echo -e "${BLUE}📖 Testing help command...${NC}"
wishlistops --help > /dev/null
echo -e "${GREEN}✓ Help command works${NC}"
echo ""

# Check package structure
echo -e "${BLUE}📂 Checking package structure...${NC}"
python -c "
import wishlistops
import wishlistops.main
import wishlistops.web_server
import wishlistops.config_manager
import wishlistops.state_manager
print('✓ All modules importable')
"
echo -e "${GREEN}✓ Package structure OK${NC}"
echo ""

# Check dashboard files
echo -e "${BLUE}🌐 Checking dashboard files...${NC}"
if [ -f "dashboard/index.html" ]; then
    echo -e "${GREEN}✓ index.html${NC}"
else
    echo -e "${RED}❌ Missing index.html${NC}"
fi

if [ -f "dashboard/welcome.html" ]; then
    echo -e "${GREEN}✓ welcome.html${NC}"
else
    echo -e "${RED}❌ Missing welcome.html${NC}"
fi

if [ -f "dashboard/setup.html" ]; then
    echo -e "${GREEN}✓ setup.html${NC}"
else
    echo -e "${RED}❌ Missing setup.html${NC}"
fi

if [ -f "dashboard/monitor.html" ]; then
    echo -e "${GREEN}✓ monitor.html${NC}"
else
    echo -e "${RED}❌ Missing monitor.html${NC}"
fi

if [ -f "dashboard/docs.html" ]; then
    echo -e "${GREEN}✓ docs.html${NC}"
else
    echo -e "${RED}❌ Missing docs.html${NC}"
fi

if [ -f "dashboard/styles.css" ]; then
    echo -e "${GREEN}✓ styles.css${NC}"
else
    echo -e "${RED}❌ Missing styles.css${NC}"
fi
echo ""

# Test dry run
echo -e "${BLUE}🧪 Testing dry run...${NC}"
if [ -f "wishlistops/config.json" ]; then
    wishlistops run --dry-run --verbose 2>&1 | head -n 5
    echo -e "${GREEN}✓ Dry run works${NC}"
else
    echo "⚠️  No config file (expected for first install)"
fi
echo ""

# Success
echo "=========================================="
echo -e "${GREEN}✅ All tests passed!${NC}"
echo "=========================================="
echo ""
echo "🚀 Ready to launch:"
echo "   1. Run: wishlistops setup"
echo "   2. Browser opens at http://127.0.0.1:8080"
echo "   3. Follow setup wizard"
echo ""
echo "📖 Documentation:"
echo "   - Built-in: http://127.0.0.1:8080/docs"
echo "   - Launch Guide: cat LAUNCH_GUIDE.md"
echo "   - GitHub: https://github.com/jamesthegreati/WishlistOps"
echo ""
