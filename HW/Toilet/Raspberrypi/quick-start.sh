#!/bin/bash
# 🚀 라즈베리파이 새장 화장실 청소 시스템 - 빠른 시작

set -e

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🐦 라즈베리파이 새장 화장실 청소 시스템 - 빠른 시작${NC}"
echo "=================================================="

# uv 설치 확인
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️ uv가 설치되지 않았습니다.${NC}"
    echo
    echo "다음 중 하나를 선택하세요:"
    echo "1. 전체 자동 설치: ./setup-env.sh"
    echo "2. uv만 설치: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo
    exit 1
fi

echo -e "${GREEN}✅ uv 확인됨: $(uv --version)${NC}"

# pyproject.toml 확인
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}❌ pyproject.toml 파일이 없습니다.${NC}"
    echo "올바른 디렉토리에서 실행하고 있는지 확인하세요."
    exit 1
fi

# 가상환경 및 의존성 설치
echo -e "${BLUE}📦 의존성 확인 및 설치...${NC}"
uv sync

echo
echo -e "${GREEN}🚀 시스템 실행 옵션:${NC}"
echo "1. 일반 모드:     uv run clean-system"
echo "2. 헤드리스 모드: uv run clean-system --headless"
echo "3. 테스트 모드:   uv run clean-system --test --headless"
echo "4. 레거시 모드:   uv run python main.py"
echo
echo -e "${BLUE}🔍 시스템 검사:${NC}"
echo "1. 의존성 검사:   uv run clean-system --check-deps"
echo "2. 하드웨어 검사: uv run clean-system --check-hardware"
echo
echo -e "${YELLOW}💡 Makefile 사용:${NC}"
echo "make help  # 모든 명령어 보기"
echo "make run   # 시스템 실행"
echo "make check # 전체 검사"

# 사용자 선택
echo
read -p "바로 시스템을 실행하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 클린 버전 시스템을 시작합니다...${NC}"
    uv run clean-system
fi 