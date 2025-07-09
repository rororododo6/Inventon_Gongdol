#!/bin/bash
# 🍓 라즈베리파이 새장 화장실 청소 시스템 환경 설정
# uv를 사용한 자동 설치 스크립트

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 함수: 색상 출력
print_step() {
    echo -e "${BLUE}🔧 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}💡 $1${NC}"
}

# 헤더
echo -e "${PURPLE}"
echo "🐦 라즈베리파이 새장 화장실 자동 청소 시스템"
echo "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" "=" 
echo -e "${NC}"

# 시스템 정보 확인
print_step "시스템 정보 확인"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Python: $(python3 --version)"
echo "아키텍처: $(uname -m)"

# 라즈베리파이 확인
if ! command -v vcgencmd &> /dev/null; then
    print_warning "라즈베리파이가 아닌 시스템에서 실행 중입니다."
    read -p "계속 진행하시겠습니까? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    print_success "라즈베리파이 시스템 확인"
    vcgencmd measure_temp
fi

# 1. 시스템 업데이트
print_step "시스템 패키지 업데이트"
sudo apt update -y
sudo apt upgrade -y

# 2. 필수 시스템 패키지 설치
print_step "필수 시스템 패키지 설치"
SYSTEM_PACKAGES=(
    "python3-pip"
    "python3-venv"
    "python3-dev"
    "python3-picamera2"
    "libcamera-apps"
    "v4l-utils"
    "git"
    "curl"
    "build-essential"
    "cmake"
    "pkg-config"
    "libjpeg-dev"
    "libtiff5-dev"
    "libpng-dev"
    "libavcodec-dev"
    "libavformat-dev"
    "libswscale-dev"
    "libv4l-dev"
    "libxvidcore-dev"
    "libx264-dev"
    "libgtk-3-dev"
    "libatlas-base-dev"
    "gfortran"
    "python3-numpy"
)

for package in "${SYSTEM_PACKAGES[@]}"; do
    if sudo apt install -y "$package"; then
        print_success "설치 완료: $package"
    else
        print_warning "설치 실패: $package (무시하고 계속)"
    fi
done

# 3. uv 설치
print_step "uv 패키지 매니저 설치"
if ! command -v uv &> /dev/null; then
    print_info "uv를 설치합니다..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # PATH에 uv 추가
    export PATH="$HOME/.cargo/bin:$PATH"
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    
    print_success "uv 설치 완료"
else
    print_success "uv가 이미 설치되어 있습니다 ($(uv --version))"
fi

# PATH 업데이트 확인
if ! command -v uv &> /dev/null; then
    print_error "uv가 PATH에 없습니다. 터미널을 재시작하거나 다음 명령어를 실행하세요:"
    echo "source ~/.bashrc"
    exit 1
fi

# 4. Python 가상환경 생성 및 의존성 설치
print_step "Python 환경 구성"
print_info "uv를 사용하여 프로젝트 의존성을 설치합니다..."

# 기존 가상환경 제거 (있는 경우)
if [ -d ".venv" ]; then
    print_warning "기존 가상환경을 제거합니다..."
    rm -rf .venv
fi

# uv를 사용하여 의존성 설치
uv sync

print_success "Python 환경 구성 완료"

# 5. 권한 설정
print_step "사용자 권한 설정"
GROUPS=("video" "dialout" "gpio")

for group in "${GROUPS[@]}"; do
    if getent group "$group" > /dev/null 2>&1; then
        sudo usermod -a -G "$group" "$USER"
        print_success "그룹 추가: $group"
    else
        print_warning "그룹이 존재하지 않습니다: $group"
    fi
done

# 6. 카메라 설정 확인
print_step "라즈베리파이 카메라 설정 확인"
if grep -q "camera_auto_detect=1" /boot/config.txt 2>/dev/null; then
    print_success "카메라 자동 감지 활성화됨"
elif grep -q "start_x=1" /boot/config.txt 2>/dev/null; then
    print_success "카메라 활성화됨 (레거시 설정)"
else
    print_warning "카메라가 활성화되지 않을 수 있습니다."
    print_info "다음 명령어로 카메라를 활성화하세요:"
    echo "sudo raspi-config"
    echo "3 Interface Options → I1 Camera → Yes"
fi

# 7. YOLO 모델 다운로드
print_step "YOLO 모델 확인"
YOLO_MODELS=("yolov11n.pt" "yolov11s.pt")
MODEL_BASE_URL="https://github.com/ultralytics/assets/releases/download/v0.0.0"

for model in "${YOLO_MODELS[@]}"; do
    if [ ! -f "$model" ]; then
        print_info "YOLO 모델 다운로드: $model"
        if wget -q "$MODEL_BASE_URL/$model"; then
            print_success "다운로드 완료: $model"
        else
            print_warning "다운로드 실패: $model"
        fi
    else
        print_success "모델 존재: $model"
    fi
done

# 8. 하드웨어 테스트
print_step "하드웨어 연결 테스트"

# 카메라 테스트
print_info "카메라 테스트 중..."
if timeout 5 libcamera-hello --timeout 1000 >/dev/null 2>&1; then
    print_success "카메라 정상 작동"
else
    print_warning "카메라 테스트 실패 - 연결을 확인하세요"
fi

# 시리얼 포트 확인
print_info "시리얼 포트 확인..."
SERIAL_PORTS=$(ls /dev/tty{USB,ACM,S}* 2>/dev/null || true)
if [ -n "$SERIAL_PORTS" ]; then
    print_success "시리얼 포트 발견:"
    echo "$SERIAL_PORTS"
else
    print_warning "시리얼 포트를 찾을 수 없습니다 - Arduino 연결을 확인하세요"
fi

# 9. 환경 활성화 안내
print_step "설치 완료!"
echo
print_success "모든 설치가 완료되었습니다!"
echo
print_info "사용 방법:"
echo -e "${CYAN}# 가상환경 활성화${NC}"
echo "source .venv/bin/activate"
echo
echo -e "${CYAN}# 또는 uv로 직접 실행${NC}"
echo "uv run python main.py"
echo "uv run python clean_ver/run_system.py"
echo
echo -e "${CYAN}# 클린 버전 (권장)${NC}"
echo "uv run clean-system"
echo "uv run clean-system --headless"
echo "uv run clean-system --test"
echo
print_warning "권한 변경사항을 적용하려면 로그아웃 후 다시 로그인하거나 재부팅하세요."
echo
print_info "문제가 발생하면 다음 명령어로 도움말을 확인하세요:"
echo "uv run clean-system --help"

# 10. 선택적: 자동 시작 설정
echo
read -p "시스템 부팅시 자동 시작을 설정하시겠습니까? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "자동 시작 설정"
    
    # systemd 서비스 파일 생성
    SERVICE_FILE="/etc/systemd/system/toilet-cleaning.service"
    CURRENT_DIR=$(pwd)
    
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Bird Toilet Cleaning System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$HOME/.cargo/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$HOME/.cargo/bin/uv run clean-system --headless
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable toilet-cleaning.service
    
    print_success "자동 시작 설정 완료"
    print_info "서비스 제어 명령어:"
    echo "sudo systemctl start toilet-cleaning    # 시작"
    echo "sudo systemctl stop toilet-cleaning     # 정지"
    echo "sudo systemctl status toilet-cleaning   # 상태 확인"
    echo "sudo systemctl disable toilet-cleaning  # 자동 시작 해제"
fi

print_success "�� 설치가 모두 완료되었습니다!" 