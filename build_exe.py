import os
import PyInstaller.__main__
import requests
import zipfile
import shutil
from tqdm import tqdm

def download_ffmpeg():
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    print("Downloading ffmpeg...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    zip_path = "ffmpeg.zip"
    with open(zip_path, 'wb') as f, tqdm(
        desc="Downloading",
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = f.write(data)
            pbar.update(size)
    print("Extracting ffmpeg...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith('ffmpeg.exe'):
                zip_ref.extract(file)
                shutil.move(file, 'ffmpeg.exe')
                break
    os.remove(zip_path)
    for item in os.listdir():
        if os.path.isdir(item) and 'ffmpeg' in item.lower():
            shutil.rmtree(item)
    print("ffmpeg.exe ready!")

def build_exe():
    # Check if icon file exists
    icon_path = "icon.ico"
    if not os.path.exists(icon_path):
        print(f"Warning: {icon_path} not found. Default icon will be used.")
        icon_path = None

    download_ffmpeg()
    args = [
        'youtube_downloader.py',
        '--onefile',
        '--windowed',
        '--name=YouTube_MP3_Downloader',
        '--add-binary=ffmpeg.exe;.',
        '--clean',
        '--hidden-import=yt_dlp',
        '--hidden-import=tkinter',
        '--hidden-import=PIL',
    ]

    # Add the icon only if it exists
    if icon_path:
        args.append(f'--icon={icon_path}')
    
    print("Building executable...")
    PyInstaller.__main__.run(args)
    if os.path.exists('ffmpeg.exe'):
        os.remove('ffmpeg.exe')

if __name__ == "__main__":
    os.system('pip install requests tqdm yt-dlp pillow')
    build_exe()
