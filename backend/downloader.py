import os
import glob
import shutil
import re
import yt_dlp

# Folder paths configuration
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(CURRENT_DIR, 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# FFmpeg Auto-detection (Linux container system path pehle check karega, fir local windows path)
SYSTEM_FFMPEG = shutil.which("ffmpeg")
FFMPEG_LOCATION = SYSTEM_FFMPEG if SYSTEM_FFMPEG else CURRENT_DIR

# Cookies Path Check (Render Secret File, Local backend/cookies.txt, ya Root cookies.txt)
SECRET_COOKIE_PATH = "/etc/secrets/cookies.txt"
LOCAL_COOKIE_PATH = os.path.join(CURRENT_DIR, "cookies.txt")
ROOT_COOKIE_PATH = os.path.join(os.path.dirname(CURRENT_DIR), "cookies.txt")

COOKIE_FILE = None
if os.path.exists(SECRET_COOKIE_PATH):
    COOKIE_FILE = SECRET_COOKIE_PATH
elif os.path.exists(LOCAL_COOKIE_PATH):
    COOKIE_FILE = LOCAL_COOKIE_PATH
elif os.path.exists(ROOT_COOKIE_PATH):
    COOKIE_FILE = ROOT_COOKIE_PATH

# Debug Log - Render console me confirm karne ke liye
if COOKIE_FILE:
    print(f"[NJ-LOG] Cookie file found at: {COOKIE_FILE} (Size: {os.path.getsize(COOKIE_FILE)} bytes)")
else:
    print("[NJ-LOG] WARNING: No cookies.txt found in any path!")

# Universal YDL Options
COMMON_YDL_OPTS = {
    'quiet': False,               # Debugging ke liye full output
    'no_warnings': False,
    'noplaylist': True,           # Mix/Playlist pages ko fetch karna block karein
    'ffmpeg_location': FFMPEG_LOCATION,
    'extractor_args': {
        'youtube': {
            'player_client': ['mweb', 'android', 'web'],
            'player_skip': ['configs']
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

# Cookie load karein agar file mili ho
if COOKIE_FILE:
    COMMON_YDL_OPTS['cookiefile'] = COOKIE_FILE


def clean_youtube_url(url):
    """Playlist aur Mix parameters (&list=, &index=) hatakar pure single video URL nikalna"""
    if "youtube.com" in url or "youtu.be" in url:
        if "watch?v=" in url:
            match = re.search(r'v=([a-zA-Z0-9_-]{11})', url)
            if match:
                return f"https://www.youtube.com/watch?v={match.group(1)}"
        elif "youtu.be/" in url:
            match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
            if match:
                return f"https://www.youtube.com/watch?v={match.group(1)}"
    return url


def sanitize_filename(name):
    """File name se invalid characters hatane ke liye"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def get_media_info(url):
    """Video details aur available resolutions fetch karne ke liye"""
    clean_url = clean_youtube_url(url)
    
    # Analyze click hote hi ye logs me print hoga
    print("="*40, flush=True)
    print(f"[NJ-LOG] Analyze clicked for URL: {clean_url}", flush=True)
    print(f"[NJ-LOG] Resolved COOKIE_FILE path: {COOKIE_FILE}", flush=True)
    if COOKIE_FILE and os.path.exists(COOKIE_FILE):
        print(f"[NJ-LOG] Cookie file FOUND! Size: {os.path.getsize(COOKIE_FILE)} bytes", flush=True)
    else:
        print("[NJ-LOG] ERROR: Cookie file NOT FOUND in container!", flush=True)
    print("="*40, flush=True)

    ydl_opts = {
        **COMMON_YDL_OPTS,
        'skip_download': True,
    }
    # ... baki function ka code waisa hi rahega

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if 'entries' in info:
                info = info['entries'][0]

            formats = info.get('formats', [])
            available_qualities = set()
            options = []

            # Sabhi available video resolutions categorize karna
            for f in formats:
                height = f.get('height')
                vcodec = f.get('vcodec')

                if height and vcodec != 'none':
                    h = int(height)
                    target = None
                    if h >= 1080 and 1080 not in available_qualities:
                        target = 1080
                    elif 720 <= h < 1080 and 720 not in available_qualities:
                        target = 720
                    elif 480 <= h < 720 and 480 not in available_qualities:
                        target = 480
                    elif 360 <= h < 480 and 360 not in available_qualities:
                        target = 360

                    if target:
                        available_qualities.add(target)
                        options.append({
                            'label': f"{target}p HD (Video + Audio)",
                            'format_id': f"bestvideo[height<={target}]+bestaudio/best[height<={target}]/best",
                            'type': 'video',
                            'order': target
                        })

            # High to low resolution sort karein
            options.sort(key=lambda x: x['order'], reverse=True)

            # Fallback agar direct height metadata na mile (Instagram Reels / Facebook ke liye)
            if not options:
                options.append({
                    'label': "Best Available Quality (Video + Audio)",
                    'format_id': "bestvideo+bestaudio/best",
                    'type': 'video',
                    'order': 9999
                })

            # Audio-only extraction option
            options.append({
                'label': "Audio Only (MP3)",
                'format_id': "bestaudio/best",
                'type': 'audio',
                'order': 0
            })

            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration_string', ''),
                "options": options
            }
    except Exception as e:
        return {"success": False, "error": str(e)}


def download_selected_format(url, format_id, media_type):
    """Selected format download karke audio ke sath merge karne ke liye"""
    clean_url = clean_youtube_url(url)

    # Purane temporary downloads clean up karein
    for f in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
        try:
            os.remove(f)
        except Exception:
            pass

    out_template = os.path.join(DOWNLOAD_DIR, '%(id)s.%(ext)s')

    ydl_opts = {
        **COMMON_YDL_OPTS,
        'format': format_id,
        'outtmpl': out_template,
    }

    if media_type == 'audio':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=True)
            if 'entries' in info:
                info = info['entries'][0]

            video_id = info.get('id')
            raw_title = info.get('title', 'download')
            clean_title = sanitize_filename(raw_title)

            ext = 'mp3' if media_type == 'audio' else 'mp4'
            source_file = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

            # Fallback check agar extension thoda alag format me download ho
            if not os.path.exists(source_file):
                matches = glob.glob(os.path.join(DOWNLOAD_DIR, f"{video_id}.*"))
                if matches:
                    source_file = matches[0]
                    ext = source_file.split('.')[-1]

            # Original clean title se rename karna
            target_filename = f"{clean_title[:60]}.{ext}"
            target_file_path = os.path.join(DOWNLOAD_DIR, target_filename)

            if os.path.exists(source_file):
                os.replace(source_file, target_file_path)
            else:
                target_filename = os.path.basename(source_file)

            return {
                "success": True,
                "file_name": target_filename,
                "title": raw_title
            }
    except Exception as e:
        return {"success": False, "error": str(e)}