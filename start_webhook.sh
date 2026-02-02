#!/bin/bash

# GitHub Webhook服务器 - 使用ngrok内网穿透
# 这个脚本会启动webhook服务器并使用ngrok创建公网访问地址

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GitHub Webhook服务器启动脚本 ===${NC}"
echo ""

# 检查ngrok是否安装
if ! command -v ngrok &> /dev/null; then
    echo -e "${RED}ngrok未安装，正在下载...${NC}"
    
    # 检测系统架构
    ARCH=$(uname -m)
    if [ "$ARCH" = "x86_64" ]; then
        NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz"
    elif [ "$ARCH" = "aarch64" ]; then
        NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm64.tgz"
    else
        echo -e "${RED}不支持的架构: $ARCH${NC}"
        exit 1
    fi
    
    # 下载ngrok
    wget -q $NGROK_URL -O ngrok.tgz
    tar -xzf ngrok.tgz
    rm ngrok.tgz
    
    echo -e "${GREEN}ngrok安装完成${NC}"
fi

# 启动webhook服务器
echo -e "${YELLOW}启动webhook服务器...${NC}"
python3 webhook.py &
WEBHOOK_PID=$!

# 等待服务器启动
sleep 3

# 启动ngrok
echo -e "${YELLOW}启动ngrok内网穿透...${NC}"
./ngrok http 5000 &
NGROK_PID=$!

# 等待ngrok启动
sleep 5

# 获取ngrok公网地址
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok\.free\.app' | head -n 1)

if [ -z "$NGROK_URL" ]; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o 'https://[^"]*\.ngrok\.io' | head -n 1)
fi

if [ -z "$NGROK_URL" ]; then
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
fi

echo ""
echo -e "${GREEN}=== 启动成功 ===${NC}"
echo -e "${GREEN}Webhook服务器运行在: http://localhost:5000/webhook${NC}"
echo -e "${GREEN}ngrok公网地址: ${NGROK_URL}/webhook${NC}"
echo ""
echo -e "${YELLOW}在GitHub中配置webhook：${NC}"
echo -e "1. 进入仓库 → Settings → Webhooks → Add webhook"
echo -e "2. Payload URL: ${NGROK_URL}/webhook"
echo -e "3. Content type: application/json"
echo -e "4. Secret: your-secret-key"
echo -e "5. 选择事件: Push events 和 Pull requests"
echo ""
echo -e "${YELLOW}按Ctrl+C停止所有服务${NC}"

# 等待用户中断
trap "echo -e '${YELLOW}正在停止服务...${NC}'; kill $WEBHOOK_PID $NGROK_PID 2>/dev/null; echo -e '${GREEN}服务已停止${NC}'; exit 0" INT

wait
