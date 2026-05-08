import streamlit as st
import os
import glob

# Handling MoviePy version differences (v1.x vs v2.x)
try:
    from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
except ImportError:
    from moviepy import ImageClip, concatenate_videoclips, AudioFileClip
import yt_dlp

# --- 1. INITIALIZE STATE ---
if 'audio_path' not in st.session_state:
    st.session_state['audio_path'] = None
if 'yt_error' in st.session_state:
    pass # Keep it for display logic

# --- 2. DEFINE ALL FUNCTIONS ---

def cleanup_temp_files():
    """Removes temporary files and resets memory."""
    files = glob.glob("temp_*") + ["output_video.mp4"]
    for f in files:
        try:
            os.remove(f)
        except:
            pass
    st.session_state['audio_path'] = None
    if 'yt_error' in st.session_state:
        del st.session_state['yt_error']

def download_youtube_audio(url):
    """Downloads only audio from YouTube using reliable browser impersonation."""
    audio_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.google.com/',
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with yt_dlp.YoutubeDL(audio_opts) as ydl:
        ydl.download([url])
    return "temp_audio.mp3"

def handle_youtube_download(url):
    """Callback function to ensure session state persists after button click."""
    try:
        # Clear previous errors
        if 'yt_error' in st.session_state:
            del st.session_state['yt_error']
            
        res_path = download_youtube_audio(url)
        if res_path:
            st.session_state['audio_path'] = res_path
    except Exception as e:
        st.session_state['yt_error'] = str(e)

def create_video(image_files, duplicate_count, fps, audio_path):
    """Processes images and merges with audio using MoviePy 2.0+ syntax."""
    clips = []
    duration_per_image = duplicate_count / fps
    target_resolution = (1280, 720) 

    for idx, img_file in enumerate(image_files):
        temp_img_path = f"temp_img_{idx}.png"
        with open(temp_img_path, "wb") as f:
            f.write(img_file.getbuffer())
        
        # MoviePy 2.0+ uses .with_duration() and .resized()
        clip = ImageClip(temp_img_path).with_duration(duration_per_image)
        clip = clip.resized(target_resolution) 
        clips.append(clip)
    
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.with_fps(fps)
    
    audio_clip = AudioFileClip(audio_path)
    if audio_clip.duration > final_video.duration:
        audio_clip = audio_clip.with_duration(final_video.duration)

    final_clip = final_video.with_audio(audio_clip)
    
    output_filename = "output_video.mp4"
    final_clip.write_videofile(output_filename, codec="libx264", audio_codec="aac")
    return output_filename

# --- 3. STREAMLIT UI LOGIC ---

st.set_page_config(page_title="PragyanAI Video Creator", layout="wide")

# Display logo if it exists
if os.path.exists("PragyanAI_Transperent.png"):
    st.image("PragyanAI_Transperent.png")

st.title("PragyanAI - Multimedia Merger")
st.markdown("Upload multiple images, specify timing, and add audio from a file or YouTube.")

with st.sidebar:
    st.header("Video Settings")
    fps = st.slider("Frames Per Second (FPS)", 1, 60, 24)
    duplicates = st.number_input("Frames per Image", min_value=1, value=48)
    
    if st.button("Clear Cache & Temp Files"):
        cleanup_temp_files()
        st.rerun()

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Images")
    uploaded_images = st.file_uploader("Upload Image Sequence", type=["jpg", "png", "jpeg"], accept_mul
