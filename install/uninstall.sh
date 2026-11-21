#!/бин/баш
bold=$(tput bold)
normal=$(tput sgr0)
red=$(tput setaf 1)
green=$(tput setaf 2)
APPNAME="inkypi"
INSTALL_PATH="/usr/local/$APPNAME"
BINPATH="/usr/local/bin"
VENV_PATH="$INSTALL_PATH/venv_$APPNAME"
SERVICE_FILE="/etc/systemd/system/$APPNAME.service"
CONFIG_DIR="$INSTALL_PATH/src/config"
echo_success() {
  echo -e "$1 [\e[32m\xE2\x9C\x94\e[0m]"
}
echo_override() {
  echo -e "\r$1"
}
echo_header() {
  echo -e "${bold}$1${normal}"
}
echo_error() {
  echo -e "${red}$1${normal} [\e[31m\xE2\x9C\x98\e[0m]\n"
}
check_permissions() {
  if [ "$EUID" -ne 0 ]; then
    echo_error "ОШИБКА: Для удаления требуются права root. Пожалуйста, запустите его с помощью sudo."
    exit 1
  fi
}
stop_service() {
  echo "Остановка службы $APPNAME"
  if /usr/bin/systemctl is-active --quiet "$APPNAME.service"
  then
    /usr/bin/systemctl stop "$APPNAME.service"
    echo_success "\tСервис успешно остановлен."
  else
    echo_success "\tСервис не запущен."
  fi
}
disable_service() {
  echo "Отключение службы $APPNAME"
  if [ -f "$SERVICE_FILE" ]; then
    /usr/bin/systemctl disable "$APPNAME.service"
    rm -f "$SERVICE_FILE"
    /usr/bin/systemctl daemon-reload
    echo_success "\tСервис отключен и удален."
  else
    echo_success "\tСервисный файл не существует. Нечего удалять."
  fi
}
remove_files() {
  echo "Удаление файлов приложения"
  if [ -f "$CONFIG_DIR/device.json" ]; then
    rm "$CONFIG_DIR/device.json"
    echo_success "\tУдален файл device.json."
  else
    echo_success "\tdevice.json не существует в $CONFIG_DIR"
  fi
  if [ -f "$CONFIG_DIR/plugins.json" ]; then
    rm "$CONFIG_DIR/plugins.json"
    echo_success "\tУдален плагин.json."
  else
    echo_success "\tplugins.json не существует в $CONFIG_DIR"
  fi
  if [ -d "$INSTALL_PATH" ]; then
    rm -rf "$INSTALL_PATH"
    echo_success "\tУстановочный каталог $INSTALL_PATH удален."
  else
    echo_success "\tКаталог установки $INSTALL_PATH не существует."
  fi
  if [ -f "$BINPATH/$APPNAME" ]; then
    rm -f "$BINPATH/$APPNAME"
    echo_success "\tИсполняемый файл $BINPATH/$APPNAME удален."
  else
    echo_success "\tИсполняемый файл $BINPATH/$APPNAME не существует."
  fi
}
confirm_uninstall() {
  echo -e "${bold}Вы уверены, что хотите удалить $APPNAME? (да/нет): ${normal}"
  read -r confirmation
  if [[ "$подтверждение" != "y" && "$подтверждение" != "Y" ]]; then
    echo_error "Удаление отменено."
    exit 1
  fi
}
check_permissions
confirm_uninstall
stop_service
disable_service
remove_files
echo_success "Удаление завершено."
echo_header "Все компоненты $APPNAME были удалены."