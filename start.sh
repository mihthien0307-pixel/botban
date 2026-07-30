#!/bin/bash
echo Started

echo "Zalo APi BOT By Nguyendev, Tommy, Ryan..!"
sleep 1

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed"
    exit 1
fi
echo "Python found!"
python3 --version
echo
if ! command -v pip3 >/dev/null 2>&1; then
    echo "Error: pip3 is not installed"
    exit 1
fi

map_module () {
    case "$1" in
        PIL) echo "pillow" ;;
        cv2) echo "opencv-python" ;;
        Crypto) echo "pycryptodome" ;;
        jwt) echo "pyjwt" ;;
        jose) echo "python-jose" ;;
        bs4) echo "beautifulsoup4" ;;
        yaml) echo "pyyaml" ;;
        dotenv) echo "python-dotenv" ;;
        flask_cors) echo "flask-cors" ;;
        flask_restful) echo "flask-restful" ;;
        flask_socketio) echo "flask-socketio" ;;
        websocket) echo "websocket-client" ;;
        ffmpeg) echo "ffmpeg-python" ;;
        sklearn) echo "scikit-learn" ;;
        telegram) echo "python-telegram-bot" ;;
        telebot) echo "pyTelegramBotAPI" ;;
        MySQLdb) echo "mysqlclient" ;;
        psycopg2) echo "psycopg2-binary" ;;
        soundfile) echo "soundfile" ;;
        moviepy) echo "moviepy" ;;
        imageio) echo "imageio" ;;
        Crypto.Cipher) echo "pycryptodome" ;;
        googlesearch) echo "googlesearch-python" ;;
        dns) echo "dnspython" ;;
        speedtest) echo "speedtest-cli" ;;
        *) echo "$1" ;;
    esac
}

is_builtin () {
    case "$1" in
        os|sys|time|json|math|re|subprocess|threading|asyncio|logging|random|hashlib|hmac|base64|datetime|typing|pathlib|functools|itertools)
            return 0 ;;
        *)
            return 1 ;;
    esac
}

run_with_autoinstall () {
    FILE="$1"
    while true; do
        OUTPUT=$(python "$FILE" 2>&1)
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            break
        fi
        if echo "$OUTPUT" | grep -q "ModuleNotFoundError"; then
            MODULE=$(echo "$OUTPUT" | sed -n "s/.*No module named '\(.*\)'.*/\1/p")

            if [ -z "$MODULE" ]; then
                echo "$OUTPUT"
                exit 1
            fi
            ROOT_MODULE="${MODULE%%.*}"
            if is_builtin "$ROOT_MODULE"; then
                echo "Builtin module error: $ROOT_MODULE"
                echo "$OUTPUT"
                exit 1
            fi
            PKG=$(map_module "$ROOT_MODULE")
            echo "Missing module: $ROOT_MODULE → installing: $PKG"
            pip install "$PKG" || exit 1
            echo
        else
            echo "$OUTPUT"
            exit 1
        fi
    done
}

getOs="$(uname -s 2>/dev/null)"

if [[ "$OS" == "Windows_NT" ]] || [[ "$getOs" =~ (MINGW|MSYS|CYGWIN) ]]; then
    echo "Detected Windows"
    echo "Auto checking & installing missing libraries..."
    pip install --upgrade pip setuptools wheel
    run_with_autoinstall userFlask.py
    run_with_autoinstall adminFlask.py
    run_with_autoinstall main.py
    echo "Opening CMD windows..."
    cmd.exe /c start "User" cmd /k python userFlask.py
    cmd.exe /c start "Admin" cmd /k python adminFlask.py
    cmd.exe /c start "Python" cmd /k python main.py
    exit 0
fi

echo "Detected Linux"
SESSION_NAME="Zalo"
if ! command -v tmux >/dev/null 2>&1; then
    echo "Error: tmux is not installed"
    exit 1
fi
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Tmux session '$SESSION_NAME' already exists."
    echo "Attach with: tmux attach -t $SESSION_NAME"
    exit 0
fi
tmux new-session -d -s "$SESSION_NAME" -n "User"
tmux send-keys -t "$SESSION_NAME:0" "python3 userFlask.py" C-m
tmux new-window -t "$SESSION_NAME" -n "Admin"
tmux send-keys -t "$SESSION_NAME:1" "python3 adminFlask.py" C-m
tmux new-window -t "$SESSION_NAME" -n "Python"
tmux send-keys -t "$SESSION_NAME:2" "python3 main.py" C-m
echo "Attach with: tmux attach -t $SESSION_NAME"