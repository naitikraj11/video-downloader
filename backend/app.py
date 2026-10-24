import os
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from downloader import get_media_info, download_selected_format, DOWNLOAD_DIR

FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

app = Flask(__name__, static_folder=FRONTEND_DIR)
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(FRONTEND_DIR, path)

# 1. Info & Qualities fetch karna
@app.route('/api/info', methods=['POST'])
def fetch_info():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    if not url:
        return jsonify({"success": False, "error": "URL is required"}), 400

    result = get_media_info(url)
    return jsonify(result), (200 if result["success"] else 500)

# 2. Chosen quality download & merge karna
@app.route('/api/process', methods=['POST'])
def process_video():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    format_id = data.get('format_id')
    media_type = data.get('type', 'video')

    if not url or not format_id:
        return jsonify({"success": False, "error": "Missing parameters"}), 400

    result = download_selected_format(url, format_id, media_type)
    return jsonify(result), (200 if result["success"] else 500)

# 3. Direct browser stream trigger karna
@app.route('/api/download/<filename>')
def serve_file(filename):
    file_path = os.path.join(DOWNLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return "File not found", 404

    return send_file(file_path, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    print("NJ Downloader is running at: http://localhost:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)