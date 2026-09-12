#!/bin/bash
#
# Скрипт установки systemd user services для AI Breadboard
#
# Использование:
#   bash systemd/install.sh
#   bash systemd/install.sh --enable
#   bash systemd/install.sh --all
#

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Определить директорию скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# systemd пользовательская директория
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   AI Breadboard systemd User Services Installer${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Проверить что мы на Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}ERROR: systemd user services supported only on Linux${NC}"
    exit 1
fi

# Проверить что директория .service файлов существует
if [ ! -d "$SCRIPT_DIR" ]; then
    echo -e "${RED}ERROR: systemd directory not found: $SCRIPT_DIR${NC}"
    exit 1
fi

# Создать ~/.config/systemd/user если её нет
echo -e "${YELLOW}[1/3] Creating systemd user directory...${NC}"
mkdir -p "$SYSTEMD_USER_DIR"
echo -e "${GREEN}✓ Directory created: $SYSTEMD_USER_DIR${NC}"
echo ""

# Копировать .service файлы
echo -e "${YELLOW}[2/3] Installing .service files...${NC}"
for service_file in "$SCRIPT_DIR"/*.service; do
    if [ -f "$service_file" ]; then
        service_name=$(basename "$service_file")
        target="$SYSTEMD_USER_DIR/$service_name"
        
        # Заменить пути в файле на реальные пути проекта
        sed "s|%h/AI-Breadboard|$PROJECT_ROOT|g" "$service_file" > "$target"
        chmod 644 "$target"
        echo -e "${GREEN}✓ Installed: $service_name${NC}"
    fi
done
echo ""

# Перезагрузить systemd daemon
echo -e "${YELLOW}[3/3] Reloading systemd daemon...${NC}"
systemctl --user daemon-reload
echo -e "${GREEN}✓ systemd daemon reloaded${NC}"
echo ""

# Показать установленные сервисы
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Installed Services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
systemctl --user list-unit-files | grep ai-breadboard || echo "No services found"
echo ""

# Обработать параметры
if [ "$1" == "--enable" ]; then
    echo -e "${YELLOW}Enabling auto-start for all services...${NC}"
    systemctl --user enable ai-breadboard-server.service
    systemctl --user enable ai-breadboard-mcp-langchain.service
    systemctl --user enable ai-breadboard-mcp-gemini.service
    echo -e "${GREEN}✓ All services enabled for auto-start${NC}"
    echo ""
elif [ "$1" == "--all" ] || [ "$1" == "--start" ]; then
    echo -e "${YELLOW}Starting all services...${NC}"
    systemctl --user start ai-breadboard-server.service
    systemctl --user start ai-breadboard-mcp-langchain.service
    systemctl --user start ai-breadboard-mcp-gemini.service
    echo -e "${GREEN}✓ All services started${NC}"
    echo ""
    
    # Показать статус
    echo -e "${BLUE}Service Status:${NC}"
    systemctl --user status ai-breadboard-server.service || true
    echo ""
fi

# Показать информацию о том как использовать
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Next Steps${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "To manage services, use:"
echo -e "  ${YELLOW}systemctl --user start ai-breadboard-server.service${NC}"
echo -e "  ${YELLOW}systemctl --user status ai-breadboard-server.service${NC}"
echo -e "  ${YELLOW}systemctl --user stop ai-breadboard-server.service${NC}"
echo -e "  ${YELLOW}systemctl --user enable ai-breadboard-server.service${NC}"
echo ""
echo -e "To view logs:"
echo -e "  ${YELLOW}journalctl --user -u ai-breadboard-server.service -f${NC}"
echo ""
echo -e "To enable all services for auto-start:"
echo -e "  ${YELLOW}systemctl --user enable ai-breadboard-*.service${NC}"
echo ""
echo -e "For more info, see: ${YELLOW}systemd/README.md${NC}"
echo ""

echo -e "${GREEN}✓ Installation complete!${NC}"
