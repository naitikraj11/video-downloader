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

# Cookies Path Check (Render Secret File ya Local backend/cookies.txt)
SECRET_COOKIE_PATH = "/etc/secrets/cookies.txt"
LOCAL_COOKIE_PATH = os.path.join(CURRENT_DIR, "cookies.txt")

COOKIE_FILE = None
if os.path.exists(SECRET_COOKIE_PATH):
    COOKIE_FILE = SECRET_COOKIE_PATH
elif os.path.exists(LOCAL_COOKIE_PATH):
    COOKIE_FILE = LOCAL_COOKIE_PATH

# Universal YDL Options - YouTube datacenter IP block bypass karne ke liye
COMMON_YDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'ffmpeg_location': FFMPEG_LOCATION,
    # Mobile client spoofing taaki datacenter IP se bhi player response mile
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'ios'],
            'player_skip': ['webpage', 'configs']
        }
    },
    'http_headers': {
        'User-Agent': 'com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip',
        'Accept-Language': 'en-US,en;q=0.9',
    }
}

# Agar cookies file maujood hai to use automatically include karein
if COOKIE_FILE:
    COMMON_YDL_OPTS['cookiefile'] = COOKIE_FILE


def sanitize_filename(name):
    """File name se invalid characters hatane ke liye"""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def get_media_info(url):
    """Video details aur available resolutions fetch karne ke liye"""
    ydl_opts = {
        **COMMON_YDL_OPTS,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
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
            info = ydl.extract_info(url, download=True)
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

            # Original clean title se rename karna taaki download readable ho
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