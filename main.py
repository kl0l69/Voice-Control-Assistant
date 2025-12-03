import sounddevice as sd
import numpy as np
import json
import keyboard
from pynput.keyboard import Controller
from gtts import gTTS
import os
import tempfile
import time
from vosk import Model, KaldiRecognizer
import subprocess
import webbrowser

keyboard_controller = Controller()

# تأكد من صحة المسار الخاص بالموديل
MODEL_PATH = r"C:\Users\Hany-Tech\Desktop\Programming\c-vol\model\vosk-model-ar-mgb2-0.4"

print("Loading Vosk model...")
try:
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(False)
    print("Vosk model loaded successfully")
except Exception as e:
    print(f"Error loading Vosk model: {e}")
    exit(1)


def record_audio_fast(max_duration=6, fs=16000, silence_threshold=400, silence_duration=1.0):
    print("Listening...")
    
    frames = []
    silence_frames = 0
    silence_limit = int(silence_duration * fs / 512)
    
    def audio_callback(indata, frames_count, time_info, status):
        nonlocal silence_frames
        volume = np.linalg.norm(indata) * 10
        
        if volume < silence_threshold:
            silence_frames += 1
        else:
            silence_frames = 0
        
        frames.append(indata.copy())
    
    with sd.InputStream(callback=audio_callback, channels=1, samplerate=fs, blocksize=512, dtype=np.int16):
        start_time = time.time()
        
        while True:
            time.sleep(0.05)
            
            if silence_frames > silence_limit and len(frames) > 5:
                break
            
            if time.time() - start_time > max_duration:
                break
    
    audio_data = np.concatenate(frames, axis=0) if frames else np.array([], dtype=np.int16)
    return audio_data


def transcribe_with_vosk(audio_data):
    try:
        audio_bytes = audio_data.tobytes()
        recognizer.AcceptWaveform(audio_bytes)
        result = json.loads(recognizer.FinalResult())
        text = result.get("text", "").strip()
        print(f"Recognized: {text}")
        return textن
    except Exception as e:
        print(f"Error in transcription: {e}")
        return ""


def extract_command_from_text(text):
    text = text.lower().strip()
    
    commands = {
        # Volume controls
        "volume_up": ["رفع الصوت", "صوت اعلى", "صوت أعلى", "زود الصوت", "volume up", "increase volume"],
        "volume_down": ["خفض الصوت", "صوت اقل", "صوت أقل", "قلل الصوت", "volume down", "decrease volume"],
        "volume_max": ["صوت عالي جدا", "اقصى صوت", "صوت كامل", "max volume", "full volume"],
        "volume_min": ["صوت واطي جدا", "اقل صوت", "volume minimum"],
        "mute": ["كتم", "اسكت", "صامت", "mute", "silence"],
        
        # Brightness controls
        "brightness_up": ["رفع السطوع", "سطوع اعلى", "سطوع أعلى", "زود السطوع", "brightness up"],
        "brightness_down": ["خفض السطوع", "سطوع اقل", "سطوع أقل", "قلل السطوع", "brightness down"],
        "brightness_max": ["سطوع كامل", "اقصى سطوع", "max brightness"],
        "brightness_min": ["اقل سطوع", "سطوع واطي", "min brightness"],
        
        # Keyboard light
        "keyboard_light_up": ["رفع اضاءة الكيبورد", "زود الاضاءة", "keyboard light up"],
        "keyboard_light_down": ["خفض اضاءة الكيبورد", "قلل الاضاءة", "keyboard light down"],
        
        # YouTube Specific Controls (نNEW)
        "yt_play_pause": ["شغل الفيديو", "وقف الفيديو", "استئناف الفيديو", "play video", "pause video"],
        "yt_forward": ["قدم الفيديو", "مشي الفيديو", "video forward", "skip forward"],
        "yt_rewind": ["رجع الفيديو", "اخر الفيديو", "video rewind", "go back"],
        "yt_fullscreen": ["شاشة كاملة", "ملء الشاشة", "fullscreen"],
        "yt_theater": ["وضع المسرح", "theater mode"],
        "yt_next": ["الفيديو التالي", "next video"],
        "yt_prev": ["الفيديو السابق", "previous video"],
        "yt_caption": ["ترجمة الفيديو", "captions"],

        # Applications
        "open_chrome": ["افتح كروم", " كروم", "chrome", "متصفح", "open chrome"],
        "open_youtube": ["افتح يوتيوب", "شغل يوتيوب", "youtube", "يوتيوب", "open youtube"],
        "open_facebook": ["افتح فيسبوك", "facebook", "فيس", "open facebook"],
        "open_instagram": ["افتح انستقرام", "instagram", "انستغرام","انستا"و "open instagram"],
        "open_x": ["افتح اكس", "x", "اكس", "open x"],
        "open_whatsapp": ["افتح واتساب", "whatsapp", "واتساب", "open whatsapp"],
        "open_notepad": ["افتح المفكرة", "notepad", "مفكرة", "open notepad"],
        "open_calculator": ["افتح الالة الحاسبة", "calculator", "حاسبة", "open calculator"],
        "open_settings": ["افتح الاعدادات", "settings", "اعدادات", "open settings"],
        "open_explorer": ["افتح المستكشف", "explorer", "مستكشف", "file explorer"],
        "open_spotify": ["افتح سبوتيفاي", "spotify", "open spotify"],
        "open_vscode": ["افتح فيجوال كود", "vscode", "visual studio code"],
        
        # Search
        "google_search": ["ابحث في جوجل", "بحث جوجل", "google search", "search google"],
        "youtube_search": ["ابحث في يوتيوب", "بحث يوتيوب", "youtube search"],
        
        # System controls
        "shutdown": ["اطفي الجهاز", "shutdown", "اغلاق"],
        "restart": ["اعادة تشغيل", "restart", "ريستارت"],
        "sleep": ["وضع السكون", "sleep", "سليب"],
        "lock_screen": ["قفل الشاشة", "lock screen", "قفل"],
        
        # Window controls
        "minimize_window": ["تصغير النافذة", "minimize", "صغر"],
        "maximize_window": ["تكبير النافذة", "maximize", "كبر"],
        "close_window": ["اغلق النافذة", "close window", "اغلق"],
        "new_tab": ["تاب جديد", "new tab", "فتح تاب"],
        "close_tab": ["اغلق التاب", "close tab", "اقفل التاب"],
        "switch_tab": ["غير التاب", "switch tab", "تاب تاني"],
        
        # Media controls (Global)
        "play_pause": ["شغل", "وقف", "play", "pause", "ايقاف"],
        "next_track": ["التالي", "next", "next track"],
        "previous_track": ["السابق", "previous", "previous track"],
        
        # Screenshots
        "screenshot": ["لقطة شاشة", "screenshot", "صورة الشاشة"],
        "snipping_tool": ["اداة القص", "snipping tool"],
        
        # Taskbar
        "task_manager": ["مدير المهام", "task manager"],
        "show_desktop": ["اظهر سطح المكتب", "show desktop", "سطح المكتب"],
    }
    
    for command, keywords in commands.items():
        for keyword in keywords:
            if keyword in text:
                return command
    
    return "none"


def execute_command(cmd):
    print(f"Executing: {cmd}")
    
    try:
        # Volume controls
        if cmd == "volume_up":
            for _ in range(2):
                keyboard.press_and_release("volume up")
        elif cmd == "volume_down":
            for _ in range(2):
                keyboard.press_and_release("volume down")
        elif cmd == "volume_max":
            for _ in range(20):
                keyboard.press_and_release("volume up")
        elif cmd == "volume_min":
            for _ in range(20):
                keyboard.press_and_release("volume down")
        elif cmd == "mute":
            keyboard.press_and_release("volume mute")
        
        # Brightness controls
        elif cmd == "brightness_up":
            for _ in range(3):
                keyboard.press_and_release("brightness up")
        elif cmd == "brightness_down":
            for _ in range(3):
                keyboard.press_and_release("brightness down")
        elif cmd == "brightness_max":
            for _ in range(15):
                keyboard.press_and_release("brightness up")
        elif cmd == "brightness_min":
            for _ in range(15):
                keyboard.press_and_release("brightness down")
        
        # Keyboard light
        elif cmd == "keyboard_light_up":
            keyboard_controller.press("f12")
            keyboard_controller.release("f12")
        elif cmd == "keyboard_light_down":
            keyboard_controller.press("f11")
            keyboard_controller.release("f11")
            
        # --- YouTube Controls (Executed via Keyboard Shortcuts) ---
        elif cmd == "yt_play_pause":
            keyboard.press_and_release("k") # K works for Play/Pause on YouTube
        elif cmd == "yt_forward":
            for _ in range(2):
                keyboard.press_and_release("l") # L forwards 10 seconds
        elif cmd == "yt_rewind":
            for _ in range(2):
                keyboard.press_and_release("j") # J rewinds 10 seconds
        elif cmd == "yt_fullscreen":
            keyboard.press_and_release("f") # F for Fullscreen
        elif cmd == "yt_theater":
            keyboard.press_and_release("t") # T for Theater mode
        elif cmd == "yt_next":
            keyboard.press_and_release("shift+n") # Next video
        elif cmd == "yt_prev":
            keyboard.press_and_release("shift+p") # Previous video
        elif cmd == "yt_caption":
            keyboard.press_and_release("c") # Toggle captions
        
        # Applications
        elif cmd == "open_chrome":
            subprocess.Popen("start chrome", shell=True)
        elif cmd == "open_youtube":
            webbrowser.open("https://youtube.com")
        elif cmd == "open_facebook":
            webbrowser.open("https://facebook.com")
        elif cmd == "open_instagram":
            webbrowser.open("https://instagram.com")
        elif cmd == "open_x":
            webbrowser.open("https://x.com")
        elif cmd == "open_whatsapp":
            webbrowser.open("https://web.whatsapp.com")
        elif cmd == "open_notepad":
            subprocess.Popen("notepad.exe")
        elif cmd == "open_calculator":
            subprocess.Popen("calc.exe")
        elif cmd == "open_settings":
            subprocess.Popen("start ms-settings:", shell=True)
        elif cmd == "open_explorer":
            subprocess.Popen("explorer.exe")
        elif cmd == "open_spotify":
            subprocess.Popen("start spotify:", shell=True)
        elif cmd == "open_vscode":
            subprocess.Popen("code")
        
        # Search
        elif cmd == "google_search":
            webbrowser.open("https://google.com")
        elif cmd == "youtube_search":
            webbrowser.open("https://youtube.com")
        
        # System controls
        elif cmd == "shutdown":
            os.system("shutdown /s /t 5")
        elif cmd == "restart":
            os.system("shutdown /r /t 5")
        elif cmd == "sleep":
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        elif cmd == "lock_screen":
            keyboard.press_and_release("win+l")
        
        # Window controls
        elif cmd == "minimize_window":
            keyboard.press_and_release("win+down")
        elif cmd == "maximize_window":
            keyboard.press_and_release("win+up")
        elif cmd == "close_window":
            keyboard.press_and_release("alt+f4")
        elif cmd == "new_tab":
            keyboard.press_and_release("ctrl+t")
        elif cmd == "close_tab":
            keyboard.press_and_release("ctrl+w")
        elif cmd == "switch_tab":
            keyboard.press_and_release("ctrl+tab")
        
        # Media controls (Global)
        elif cmd == "play_pause":
            keyboard.press_and_release("play/pause media")
        elif cmd == "next_track":
            keyboard.press_and_release("next track")
        elif cmd == "previous_track":
            keyboard.press_and_release("previous track")
        
        # Screenshots
        elif cmd == "screenshot":
            keyboard.press_and_release("win+shift+s")
        elif cmd == "snipping_tool":
            subprocess.Popen("snippingtool.exe")
        
        # Taskbar
        elif cmd == "task_manager":
            keyboard.press_and_release("ctrl+shift+esc")
        elif cmd == "show_desktop":
            keyboard.press_and_release("win+d")
        
        else:
            print("Unknown command")
            return False
        
        return True
        
    except Exception as e:
        print(f"Error executing command: {e}")
        return False


def speak_fast(text):
    try:
        tts = gTTS(text=text, lang='ar', slow=False)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        temp_file.close()
        tts.save(temp_file.name)
        os.system(f'start /min wmplayer "{temp_file.name}"')
        time.sleep(1.5)
        try:
            os.unlink(temp_file.name)
        except:
            pass
    except Exception as e:
        print(f"Error in speech: {e}")


def main():
    print("=" * 60)
    print("Voice Assistant Ready - Fast Mode (+YouTube)")
    print("=" * 60)
    print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            audio_data = record_audio_fast()
            
            if len(audio_data) == 0:
                continue
            
            text = transcribe_with_vosk(audio_data)
            
            if not text:
                continue
            
            cmd = extract_command_from_text(text)
            print(f"Command: {cmd}")
            
            if cmd != "none":
                success = execute_command(cmd)
                if success:
                    speak_fast("تم")
            else:
                print("No command detected")
            
            print("-" * 60)

    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()


