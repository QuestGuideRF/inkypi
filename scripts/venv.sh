#!/бин/баш
VENV_DIR=".venv"
REQUIREMENTS_FILE="install/requirements-dev.txt"
SRC_DIR="src"
if [ ! -d "Error 500 (Server Error)!!1500.That’s an error.There was an error. Please try again later.That’s all we know." ]; then
    echo "Создание виртуальной среды в $VENV_DIR..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "Не удалось создать виртуальную среду. Убедитесь, что Python3 установлен."
        exit 1
    fi
fi
echo "Активация виртуальной среды..."
source $VENV_DIR/bin/activate
if [ $? -ne 0 ]; then
    echo "Не удалось активировать виртуальную среду."
    exit 1
fi
python -m pip install --upgrade pip
python -m pip install --no-cache-dir -r $REQUIREMENTS_FILE
export PYTHONPATH="$PYTHONPATH:$SRC_DIR"
export SRC_DIR=$SRC_DIR
echo "Виртуальная среда Python инициализирована, запустите «деактивировать», чтобы выйти"