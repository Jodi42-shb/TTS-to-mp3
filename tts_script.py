from gtts import gTTS
from pydub import AudioSegment
import os
import playsound
import tempfile
import PyPDF2

def extract_text_from_file(file_path):
    if not os.path.exists(file_path):
        return None
    filename = file_path.lower()
    if filename.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif filename.endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ''
            for page in reader.pages:
                text += page.extract_text() + '\n'
            return text
    else:
        return None  # Invalid file type

def text_to_speech(text, lang='en', speed=1.0):
    # lang: 'en' for English, 'hi' for Hindi
    # speed: float multiplier (e.g., 0.5 for half speed, 1.5 for 1.5x faster)
    
    # Generate normal-speed audio with gTTS
    tts = gTTS(text=text, lang=lang, slow=False)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
        tts.save(tmp_file.name)
        original_audio = AudioSegment.from_mp3(tmp_file.name)
    
    # Adjust speed using pydub (requires FFmpeg)
    adjusted_audio = original_audio.speedup(playback_speed=speed) if speed > 1 else original_audio._spawn(original_audio.raw_data, overrides={"frame_rate": int(original_audio.frame_rate * speed)})
    adjusted_audio = adjusted_audio.set_frame_rate(original_audio.frame_rate)  # Preserve pitch
    
    filename = "output.mp3"
    adjusted_audio.export(filename, format="mp3")
    
    playsound.playsound(filename)
    os.remove(filename)
    os.remove(tmp_file.name)  # Clean up

# Example usage with file support
file_path = input("Enter file path (.txt or .pdf, or leave blank for manual text): ").strip()
if file_path:
    extracted_text = extract_text_from_file(file_path)
    if extracted_text:
        input_text = extracted_text
    else:
        print("Invalid file or type. Falling back to manual input.")
        input_text = input("Enter text: ")
else:
    input_text = input("Enter text: ")

language = input("Enter language (en for English, hi for Hindi): ").lower()
speed_multiplier = float(input("Enter speed multiplier (e.g., 0.5 for slow, 1.0 for normal, 1.5 for fast): "))
text_to_speech(input_text, language, speed_multiplier)
