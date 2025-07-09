# 🐦 라즈베리파이 새장 화장실 청소 시스템 Makefile
# uv를 사용한 편리한 명령어 모음

.PHONY: help install setup run run-headless run-test clean check deps hardware lint format sync

# 기본 목표
help: ## 사용 가능한 명령어 목록 표시
	@echo "🐦 라즈베리파이 새장 화장실 청소 시스템"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# 설치 및 환경 설정
install: ## 전체 환경 설치 (자동화 스크립트 실행)
	@echo "🔧 전체 환경 설치 시작..."
	./setup-env.sh

setup: ## uv 의존성 설치만 (빠른 설정)
	@echo "📦 uv 의존성 설치..."
	uv sync

# 실행 명령어
run: ## 메인 시스템 실행 (클린 버전)
	@echo "🚀 클린 버전 시스템 시작..."
	uv run clean-system

run-headless: ## 헤드리스 모드로 실행 (SSH 접속 시)
	@echo "🚀 헤드리스 모드 시작..."
	uv run clean-system --headless

run-test: ## 테스트 모드로 실행 (하드웨어 없이)
	@echo "🧪 테스트 모드 시작..."
	uv run clean-system --test --headless

run-legacy: ## 레거시 메인 런처 실행
	@echo "🔄 레거시 시스템 시작..."
	uv run python main.py

run-reserve: ## Reserve 폴더의 PI 카메라 클라이언트 실행
	@echo "📷 Reserve PI 카메라 클라이언트 시작..."
	uv run python Reserve/pi_camera_client.py

# 검사 및 확인
check: ## 모든 의존성 및 하드웨어 검사
	@echo "🔍 시스템 검사 중..."
	uv run clean-system --check-deps
	uv run clean-system --check-hardware

deps: ## Python 의존성만 검사
	@echo "📋 의존성 검사 중..."
	uv run clean-system --check-deps

hardware: ## 하드웨어 연결 상태만 검사
	@echo "🔌 하드웨어 검사 중..."
	uv run clean-system --check-hardware

# 개발 도구
lint: ## 코드 린트 (flake8)
	@echo "🔍 코드 린트 실행..."
	uv run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

format: ## 코드 포매팅 (black + isort)
	@echo "✨ 코드 포매팅 실행..."
	uv run black .
	uv run isort .

test: ## 단위 테스트 실행
	@echo "🧪 테스트 실행..."
	uv run pytest

sync: ## uv 의존성 동기화
	@echo "🔄 의존성 동기화..."
	uv sync

# 정리 및 관리
clean: ## 캐시 및 임시 파일 정리
	@echo "🧹 정리 중..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.log" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
	@echo "✅ 정리 완료"

clean-venv: ## 가상환경 완전 삭제
	@echo "🗑️ 가상환경 삭제..."
	rm -rf .venv/
	@echo "✅ 가상환경 삭제 완료"

reinstall: clean-venv setup ## 가상환경 재설치
	@echo "🔄 가상환경 재설치 완료"

# 시스템 서비스 관리 (sudo 필요)
service-install: ## systemd 서비스 설치
	@echo "⚙️ systemd 서비스 설치..."
	sudo systemctl enable toilet-cleaning.service
	@echo "✅ 자동 시작 활성화"

service-start: ## 서비스 시작
	sudo systemctl start toilet-cleaning.service

service-stop: ## 서비스 정지
	sudo systemctl stop toilet-cleaning.service

service-status: ## 서비스 상태 확인
	sudo systemctl status toilet-cleaning.service

service-logs: ## 서비스 로그 확인
	sudo journalctl -u toilet-cleaning.service -f

service-remove: ## 서비스 제거
	@echo "🗑️ systemd 서비스 제거..."
	sudo systemctl stop toilet-cleaning.service 2>/dev/null || true
	sudo systemctl disable toilet-cleaning.service 2>/dev/null || true
	sudo rm -f /etc/systemd/system/toilet-cleaning.service
	sudo systemctl daemon-reload
	@echo "✅ 서비스 제거 완료"

# 모니터링
monitor: ## 실시간 시스템 모니터링
	@echo "📊 시스템 모니터링..."
	watch -n 2 'vcgencmd measure_temp && free -h && df -h /'

camera-test: ## 카메라 테스트
	@echo "📷 카메라 테스트..."
	timeout 5 libcamera-hello --timeout 2000

serial-test: ## 시리얼 포트 확인
	@echo "🔌 시리얼 포트 확인..."
	@ls /dev/tty{USB,ACM,S}* 2>/dev/null || echo "시리얼 포트를 찾을 수 없습니다"

# 정보 표시
info: ## 시스템 정보 표시
	@echo "🍓 라즈베리파이 시스템 정보"
	@echo "============================="
	@echo "OS: $$(lsb_release -d | cut -f2)"
	@echo "Python: $$(python3 --version)"
	@echo "Architecture: $$(uname -m)"
	@echo "Temperature: $$(vcgencmd measure_temp 2>/dev/null || echo 'N/A')"
	@echo "Memory: $$(free -h | grep Mem | awk '{print $$3 "/" $$2}')"
	@echo "Disk: $$(df -h / | tail -1 | awk '{print $$3 "/" $$2 " (" $$5 ")"}')"
	@echo "uv version: $$(uv --version 2>/dev/null || echo 'Not installed')"

# 개발 환경
dev: ## 개발 환경 설정 (추가 도구 설치)
	@echo "🛠️ 개발 환경 설정..."
	uv sync --extra dev
	@echo "✅ 개발 도구 설치 완료"

# 기본 목표
all: install check ## 전체 설치 및 검사 실행 