#!/бин/баш
bold=$(tput bold)
normal=$(tput sgr0)
green=$(tput setaf 2)
red=$(tput setaf 1)
SOURCE=${BASH_SOURCE[0]}
while [ -h "$ИСТОЧНИК" ]; do
  DIR=$( cd -P "$(имя каталога "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$ИСТОЧНИК")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE
done
SCRIPT_DIR=$( cd -P "$(имя каталога "$SOURCE" )" >/dev/null 2>&1 && pwd )
APPNAME="inkypi"
INSTALL_PATH="/usr/local/$APPNAME"
BINPATH="/usr/local/bin"
VENV_PATH="$INSTALL_PATH/venv_$APPNAME"
APT_REQUIREMENTS_FILE="$SCRIPT_DIR/debian-requirements.txt"
PIP_REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
echo_success() {
  echo -e "$1 [\e[32m\xE2\x9C\x94\e[0m]"
}
echo_error() {
  echo -e "$1 [\e[31m\xE2\x9C\x98\e[0m]\n"
}
setup_zramswap_service() {
  echo "Включение и запуск службы zramswap."
  sudo apt-get install -y zram-tools > /dev/null
  echo -e "SOMETHING=zstd\nPERCENT=60" | sudo tee /etc/default/zramswap > /dev/null
  sudo systemctl enable --now zramswap
}
setup_earlyoom_service() {
  echo "Включение и запуск услуги Earlyoom."
  sudo apt-get install -y earlyoom > /dev/null
  sudo systemctl enable --now earlyoom
}
get_os_version() {
  echo "$(lsb_release -ср)"
}
if [ "$EUID" -ne 0 ]; then
  echo_error "ОШИБКА: Для этого сценария требуются права root. Пожалуйста, запустите его с помощью sudo."
  exit 1
fi
apt-get update -y > /dev/null &
if [ -f "$APT_REQUIREMENTS_FILE" ]; then
  echo "Установка системных зависимостей... "
  xargs -a "$APT_REQUIREMENTS_FILE" sudo apt-get install -y > /dev/null && echo_success "Установленные системные зависимости."
else
  echo_error "ОШИБКА: файл системных зависимостей $APT_REQUIREMENTS_FILE не найден!"
  exit 1
fi
if [[ $(get_os_version) = "12" ]] ; then
  echo "Версия ОС Bookworm – настройка zramswap"
  setup_zramswap_service
else
  echo "Версия ОС не Bookworm — настройка zramswap пропускается."
fi
setup_earlyoom_service
if [ ! -d "$VENV_PATH" ]; then
  echo_error "ОШИБКА: Виртуальная среда не найдена в $VENV_PATH. Сначала запустите сценарий установки."
  exit 1
fi
source "$VENV_PATH/bin/активировать"
echo "Обновление пипа..."
$VENV_PATH/bin/python -m pip install --upgrade pip setuptools wheel > /dev/null && echo_success "Pip успешно обновлен."
if [ -f "$PIP_REQUIREMENTS_FILE" ]; then
  echo "Обновление зависимостей Python..."
  $VENV_PATH/bin/python -m pip install --upgrade -r "$PIP_REQUIREMENTS_FILE" -qq > /dev/null && echo_success "Зависимости успешно обновлены."
else
  echo_error "ОШИБКА: файл требований $PIP_REQUIREMENTS_FILE не найден!"
  exit 1
fi
echo "Обновление исполняемого файла в ${BINPATH}/$APPNAME"
cp $SCRIPT_DIR/inkypi $BINPATH/
sudo chmod +x $BINPATH/$APPNAME
echo "Обновите файлы JS и CSS."
bash $SCRIPT_DIR/update_vendors.sh
echo "Перезапуск службы $APPNAME."
sudo systemctl daemon-reload
sudo systemctl restart $APPNAME.service
echo_success "Обновление завершено."