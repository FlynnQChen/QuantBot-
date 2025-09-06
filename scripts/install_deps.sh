#!/bin/bash 
# CryptoTrader 前端依赖安装脚本
# 版本: 2.1.0 
# 功能: 自动安装项目所需的所有依赖和环境配置
 
set -euo pipefail
 
# 颜色定义 
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color 
 
# 配置参数 
NODE_VERSION="16.14.0"
NPM_VERSION="8.3.1"
PNPM_VERSION="7.0.0"
YARN_VERSION="1.22.17"
PYTHON_VERSION="3.8"
CHROME_VERSION="latest"
PROJECT_DIR=$(pwd)
FRONTEND_DIR="$PROJECT_DIR/frontend"
LOG_FILE="$PROJECT_DIR/install.log" 
PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
 
# 初始化日志
echo "=== CryptoTrader 依赖安装日志 ===" > "$LOG_FILE"
echo "开始时间: $(date)" >> "$LOG_FILE"
echo "系统: $PLATFORM $ARCH" >> "$LOG_FILE"
 
# 工具函数
log() {
    local level=$1 
    local message=$2 
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    
    case $level in 
        "INFO") echo -e "${BLUE}[INFO]${NC} $message" ;;
        "SUCCESS") echo -e "${GREEN}[✓]${NC} $message" ;;
        "WARNING") echo -e "${YELLOW}[!]${NC} $message" ;;
        "ERROR") echo -e "${RED}[✗]${NC} $message" ;;
    esac 
    
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}
 
check_command() {
    if ! command -v $1 &> /dev/null; then
        log ERROR "必需的命令 $1 未安装"
        return 1
    fi 
    return 0
}
 
install_node() {
    log INFO "正在安装 Node.js  $NODE_VERSION..."
    
    if [[ "$PLATFORM" == "linux" ]]; then 
        curl -fsSL https://deb.nodesource.com/setup_16.x  | sudo -E bash - >> "$LOG_FILE" 2>&1
        sudo apt-get install -y nodejs >> "$LOG_FILE" 2>&1
    elif [[ "$PLATFORM" == "darwin" ]]; then
        brew install node@16 >> "$LOG_FILE" 2>&1
    else 
        log ERROR "不支持的操作系统: $PLATFORM"
        exit 1 
    fi
    
    # 验证安装 
    if ! command -v node &> /dev/null; then 
        log ERROR "Node.js  安装失败"
        exit 1
    fi 
    
    log SUCCESS "Node.js  安装完成"
}
 
install_python() {
    log INFO "正在安装 Python $PYTHON_VERSION..."
    
    if [[ "$PLATFORM" == "linux" ]]; then 
        sudo apt-get install -y python3 python3-pip python3-venv >> "$LOG_FILE" 2>&1 
    elif [[ "$PLATFORM" == "darwin" ]]; then 
        brew install python >> "$LOG_FILE" 2>&1
    else 
        log WARNING "不支持的操作系统: $PLATFORM - 请手动安装 Python"
        return
    fi
    
    log SUCCESS "Python 安装完成"
}
 
install_chrome() {
    log INFO "正在安装 Chrome..."
    
    if [[ "$PLATFORM" == "linux" ]]; then 
        wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb  >> "$LOG_FILE" 2>&1
        sudo apt-get install -y ./google-chrome-stable_current_amd64.deb  >> "$LOG_FILE" 2>&1
        rm google-chrome-stable_current_amd64.deb 
    elif [[ "$PLATFORM" == "darwin" ]]; then 
        brew install --cask google-chrome >> "$LOG_FILE" 2>&1
    else
        log WARNING "不支持的操作系统: $PLATFORM - 请手动安装 Chrome"
        return 
    fi
    
    log SUCCESS "Chrome 安装完成"
}
 
setup_node_env() {
    log INFO "配置 Node.js  环境..."
    
    # 设置 npm 全局安装路径 
    mkdir -p ~/.npm-global
    npm config set prefix '~/.npm-global' >> "$LOG_FILE" 2>&1 
    
    # 更新 npm 
    npm install -g npm@$NPM_VERSION >> "$LOG_FILE" 2>&1 
    
    # 安装包管理器
    npm install -g pnpm@$PNPM_VERSION yarn@$YARN_VERSION >> "$LOG_FILE" 2>&1
    
    # 添加到 PATH 
    if ! grep -q "npm-global" ~/.bashrc; then 
        echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
    fi 
    if ! grep -q "npm-global" ~/.zshrc; then
        echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc 
    fi
    
    source ~/.bashrc 
    
    log SUCCESS "Node.js  环境配置完成"
}
 
install_frontend_deps() {
    log INFO "安装前端依赖..."
    cd "$FRONTEND_DIR"
    
    # 清理旧依赖 
    rm -rf node_modules package-lock.json  yarn.lock  pnpm-lock.yaml  
    
    # 使用 pnpm 安装
    pnpm install --frozen-lockfile >> "$LOG_FILE" 2>&1
    
    # 检查安装结果 
    if [ $? -ne 0 ]; then 
        log ERROR "前端依赖安装失败"
        exit 1
    fi
    
    log SUCCESS "前端依赖安装完成"
}
 
setup_husky() {
    log INFO "配置 Git Hooks..."
    cd "$FRONTEND_DIR"
    
    pnpm run prepare >> "$LOG_FILE" 2>&1
    
    if [ $? -ne 0 ]; then
        log WARNING "Git Hooks 配置失败"
    else
        log SUCCESS "Git Hooks 配置完成"
    fi
}
 
verify_installations() {
    log INFO "验证安装..."
    
    declare -A commands=(
        ["node"]="$NODE_VERSION"
        ["npm"]="$NPM_VERSION"
        ["pnpm"]="$PNPM_VERSION"
        ["yarn"]="$YARN_VERSION"
        ["python3"]="$PYTHON_VERSION"
    )
    
    for cmd in "${!commands[@]}"; do 
        if ! command -v $cmd &> /dev/null; then 
            log WARNING "$cmd 未安装"
            continue
        fi
        
        version=$($cmd --version 2>&1)
        log SUCCESS "$cmd 已安装 - 版本: $version"
    done 
    
    log SUCCESS "验证完成"
}
 
# 主执行流程
main() {
    log INFO "开始 CryptoTrader 依赖安装"
    log INFO "项目目录: $PROJECT_DIR"
    
    # 检查系统工具 
    log INFO "检查系统工具..."
    check_command curl || exit 1 
    check_command git || exit 1
    
    # 安装基础依赖 
    if ! command -v node &> /dev/null || [[ $(node --version | cut -d'v' -f2) != "$NODE_VERSION"* ]]; then 
        install_node 
    else
        log INFO "Node.js  已安装"
    fi
    
    setup_node_env 
    
    if ! command -v python3 &> /dev/null; then
        install_python 
    else
        log INFO "Python 已安装"
    fi
    
    # 安装 Chrome (用于测试)
    if [[ "$PLATFORM" == "linux" ]] || [[ "$PLATFORM" == "darwin" ]]; then 
        install_chrome
    fi 
    
    # 安装前端依赖
    install_frontend_deps 
    
    # 配置 Git Hooks
    setup_husky 
    
    # 验证安装 
    verify_installations 
    
    log SUCCESS "所有依赖安装完成!"
    log INFO "详细日志请查看: $LOG_FILE"
    
    echo -e "\n${GREEN}安装成功!${NC}"
    echo -e "请运行以下命令启动开发服务器:"
    echo -e "  cd frontend && pnpm dev\n"
}
 
# 执行主函数 
main 