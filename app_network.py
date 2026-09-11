from flask import Flask, request, send_file, render_template_string
from gtts import gTTS
from pydub import AudioSegment
import io
import tempfile
import PyPDF2
import os  # Ensures file cleanup works
import socket
import subprocess

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB

def extract_text_from_file(file):
    filename = file.filename.lower()
    if filename.endswith('.txt'):
        return file.read().decode('utf-8')
    elif filename.endswith('.pdf'):
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text() + '\n'
        return text
    else:
        return None  # Invalid file type

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        text = request.form.get('text', '')
        file = request.files.get('file')
        
        if file and file.filename:
            extracted = extract_text_from_file(file)
            if extracted:
                text = extracted
            else:
                return "Invalid file type. Please upload .txt or .pdf.", 400
        
        if not text:
            return "Please provide text or upload a file.", 400
        
        lang = request.form['lang']
        speed = float(request.form.get('speed', 1.0))  # Default to 1.0
        
        # Generate normal-speed audio with gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            original_audio = AudioSegment.from_mp3(tmp_file.name)
        
        # Adjust speed using pydub
        adjusted_audio = original_audio.speedup(playback_speed=speed) if speed > 1 else original_audio._spawn(original_audio.raw_data, overrides={"frame_rate": int(original_audio.frame_rate * speed)})
        adjusted_audio = adjusted_audio.set_frame_rate(original_audio.frame_rate)
        
        audio_buffer = io.BytesIO()
        adjusted_audio.export(audio_buffer, format="mp3")
        audio_buffer.seek(0)
        
        os.remove(tmp_file.name)  # Clean up – this line now works with the import
        return send_file(audio_buffer, mimetype='audio/mp3', as_attachment=True, download_name='output.mp3')
    
    # Updated HTML form with file upload
    return render_template_string('''
    <form method="post" enctype="multipart/form-data">
        <label>Text (or leave blank if uploading a file):</label><br>
        <textarea name="text" rows="4" cols="50"></textarea><br>
        <label>Upload File (.txt or .pdf):</label><br>
        <input type="file" name="file"><br>
        <label>Language:</label><br>
        <select name="lang">
            <option value="en">English</option>
            <option value="hi">Hindi</option>
        </select><br>
        <label>Speed Multiplier (e.g., 0.5 for slow, 1.5 for fast):</label><br>
        <input type="number" name="speed" step="0.1" value="1.0" min="0.5" max="2.0"><br>
        <input type="submit" value="Generate Audio">
    </form>
    ''')

def get_network_urls(port=5000):
    urls = []

    # Show IPv4 addresses assigned to this machine (LAN/Wi-Fi, etc.).
    try:
        hostname = socket.gethostname()
        for addr in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = addr[4][0]
            if ip != '127.0.0.1':
                url = f'http://{ip}:{port}'
                if url not in urls:
                    urls.append(url)
    except socket.gaierror:
        pass

    # Add the Tailscale IPv4 address when Tailscale is available.
    try:
        output = subprocess.check_output(
            ['tailscale', 'ip', '-4'],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for ip in output.splitlines():
            ip = ip.strip()
            if ip:
                url = f'http://{ip}:{port}'
                if url not in urls:
                    urls.append(url)
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    return urls


if __name__ == '__main__':
    port = 5000

    print(f'Local:     http://127.0.0.1:{port}')
    for url in get_network_urls(port):
        ip = url.split('//', 1)[1].split(':', 1)[0]
        label = 'Tailscale' if ip.startswith('100.') else 'LAN'
        print(f'{label}:  {url}')

    print(f'Listening on 0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
