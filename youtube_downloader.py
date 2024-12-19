import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yt_dlp
import os
from datetime import datetime
import threading
import sys
import json
from urllib.request import urlopen
from PIL import Image, ImageTk
from io import BytesIO
import re

class YouTubeMp3DownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube MP3 Downloader")
        self.root.geometry("800x700")
        
        # Initialize variables
        if getattr(sys, 'frozen', False):
            self.output_dir = os.path.dirname(sys.executable)
        else:
            self.output_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.downloads = []
        self.currently_downloading = False
        self.is_dark_mode = False
        self.current_video_info = None
        
        # Load settings
        self.load_settings()
        
        # Create GUI elements
        self.create_widgets()
        
        # Apply theme
        self.apply_theme()
        
    def load_settings(self):
        self.settings_file = 'downloader_settings.json'
        try:
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        except:
            self.settings = {
                'dark_mode': False,
                'last_directory': self.output_dir,
                'quality': '192',
                'auto_playlist': False
            }
    
    def save_settings(self):
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f)
    
    def create_widgets(self):
        # Main frame with padding
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menu Bar
        self.create_menu()
        
        # URL Entry and Preview Button
        url_frame = ttk.Frame(self.main_frame)
        url_frame.pack(fill=tk.X)
        
        ttk.Label(url_frame, text="YouTube URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.preview_button = ttk.Button(url_frame, text="Preview", command=self.preview_video)
        self.preview_button.pack(side=tk.LEFT, padx=5)
        
        # Video Preview Frame
        self.preview_frame = ttk.LabelFrame(self.main_frame, text="Video Information", padding="10")
        self.preview_frame.pack(fill=tk.X, pady=5)
        
        # Thumbnail Label
        self.thumbnail_label = ttk.Label(self.preview_frame)
        self.thumbnail_label.grid(row=0, column=0, rowspan=3, padx=5)
        
        # Video Info Labels
        self.title_label = ttk.Label(self.preview_frame, text="", wraplength=400)
        self.title_label.grid(row=0, column=1, sticky='w', padx=5)
        
        self.duration_label = ttk.Label(self.preview_frame, text="")
        self.duration_label.grid(row=1, column=1, sticky='w', padx=5)
        
        self.channel_label = ttk.Label(self.preview_frame, text="")
        self.channel_label.grid(row=2, column=1, sticky='w', padx=5)
        
        # Options Frame
        options_frame = ttk.LabelFrame(self.main_frame, text="Download Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        # Audio Quality Selection
        ttk.Label(options_frame, text="Audio Quality:").grid(row=0, column=0, padx=5)
        self.quality_var = tk.StringVar(value=self.settings['quality'])
        qualities = ["64", "128", "192", "256", "320"]
        self.quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var, 
                                        values=qualities, width=10)
        self.quality_combo.grid(row=0, column=1)
        ttk.Label(options_frame, text="kbps").grid(row=0, column=2)
        
        # Playlist Options
        self.playlist_var = tk.BooleanVar(value=self.settings['auto_playlist'])
        self.playlist_check = ttk.Checkbutton(options_frame, text="Download entire playlist if URL is playlist",
                                            variable=self.playlist_var)
        self.playlist_check.grid(row=0, column=3, padx=20)
        
        # Output Directory Selection
        ttk.Label(options_frame, text="Output Directory:").grid(row=1, column=0, padx=5, pady=5)
        self.output_label = ttk.Label(options_frame, text=self.output_dir, wraplength=300)
        self.output_label.grid(row=1, column=1, columnspan=2, sticky='w')
        
        ttk.Button(options_frame, text="Change Directory", 
                  command=self.change_directory).grid(row=1, column=3, padx=5)
        
        # Download Button
        self.download_button = ttk.Button(self.main_frame, text="Download", 
                                        command=self.start_download)
        self.download_button.pack(pady=10)
        
        # Progress Frame
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Cancel Button
        self.cancel_button = ttk.Button(progress_frame, text="Cancel", command=self.cancel_download,
                                      state='disabled')
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Status Label
        self.status_label = ttk.Label(self.main_frame, text="Ready")
        self.status_label.pack(pady=5)
        
        # Downloads List
        list_frame = ttk.LabelFrame(self.main_frame, text="Download History", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar and Listbox
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.downloads_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                          width=70, height=10)
        self.downloads_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.downloads_listbox.yview)
        
        # Right-click menu for downloads list
        self.create_context_menu()
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Change Output Directory", command=self.change_directory)
        file_menu.add_command(label="Clear Download History", command=self.clear_history)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Options Menu
        options_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Options", menu=options_menu)
        options_menu.add_checkbutton(label="Dark Mode", command=self.toggle_dark_mode)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Instructions", command=self.show_instructions)
    
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Open File Location", command=self.open_file_location)
        self.context_menu.add_command(label="Copy File Path", command=self.copy_file_path)
        self.context_menu.add_command(label="Remove from List", command=self.remove_from_list)
        
        self.downloads_listbox.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        try:
            index = self.downloads_listbox.nearest(event.y)
            if index >= 0:
                self.downloads_listbox.selection_clear(0, tk.END)
                self.downloads_listbox.selection_set(index)
                self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def preview_video(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        def fetch_info():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    self.current_video_info = info
                    
                    # Update GUI in main thread
                    self.root.after(0, lambda: self.update_preview(info))
            
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Could not fetch video info: {str(e)}"))
        
        # Start preview in thread
        threading.Thread(target=fetch_info, daemon=True).start()
    
    def update_preview(self, info):
        # Update title
        self.title_label.config(text=f"Title: {info.get('title', 'N/A')}")
        
        # Update duration
        duration = info.get('duration')
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            self.duration_label.config(text=f"Duration: {minutes}:{seconds:02d}")
        
        # Update channel
        self.channel_label.config(text=f"Channel: {info.get('uploader', 'N/A')}")
        
        # Update thumbnail
        try:
            thumbnail_url = info.get('thumbnail')
            if thumbnail_url:
                with urlopen(thumbnail_url) as u:
                    raw_data = u.read()
                image = Image.open(BytesIO(raw_data))
                image = image.resize((120, 68), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                self.thumbnail_label.config(image=photo)
                self.thumbnail_label.image = photo
        except:
            self.thumbnail_label.config(text="No thumbnail")
    
    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        self.settings['dark_mode'] = self.is_dark_mode
        self.save_settings()
        self.apply_theme()
    
    def apply_theme(self):
        style = ttk.Style()
        
        if self.is_dark_mode:
            self.root.configure(bg='#2d2d2d')
            style.configure(".", background='#2d2d2d', foreground='white')
            style.configure("TLabel", background='#2d2d2d', foreground='white')
            style.configure("TFrame", background='#2d2d2d')
            style.configure("TLabelframe", background='#2d2d2d', foreground='white')
            style.configure("TLabelframe.Label", background='#2d2d2d', foreground='white')
            self.downloads_listbox.configure(bg='#3d3d3d', fg='white')
        else:
            self.root.configure(bg='#f0f0f0')
            style.configure(".", background='#f0f0f0', foreground='black')
            style.configure("TLabel", background='#f0f0f0', foreground='black')
            style.configure("TFrame", background='#f0f0f0')
            style.configure("TLabelframe", background='#f0f0f0', foreground='black')
            style.configure("TLabelframe.Label", background='#f0f0f0', foreground='black')
            self.downloads_listbox.configure(bg='white', fg='black')
    
    def change_directory(self):
        new_dir = filedialog.askdirectory(initialdir=self.output_dir)
        if new_dir:
            self.output_dir = new_dir
            self.output_label.config(text=self.output_dir)
            self.settings['last_directory'] = new_dir
            self.save_settings()
    
    def start_download(self):
        if self.currently_downloading:
            return
            
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        self.currently_downloading = True
        self.download_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        self.status_label.config(text="Starting download...")
        self.progress_var.set(0)
        
        # Start download in separate thread
        self.download_thread = threading.Thread(target=self.download_thread_func, args=(url,))
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def cancel_download(self):
        if hasattr(self, 'current_process'):
            self.current_process.terminate()
        self.status_label.config(text="Download cancelled")
        self.currently_downloading = False
        self.download_button.config(state='normal')
        self.cancel_button.config(state='disabled')
    
    def download_thread_func(self, url):
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.output_dir, '%(title)s.%(ext)s'),
                'progress_hooks': [self.update_progress],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',           
                    'preferredcodec': 'mp3',
                    'preferredquality': self.quality_var.get(),
                }],
                'ignoreerrors': True,
                'noplaylist': not self.playlist_var.get(),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info.get('_type') == 'playlist' and self.playlist_var.get():
                    total_videos = len(info['entries'])
                    for index, entry in enumerate(info['entries'], 1):
                        if not self.currently_downloading:  # Check if cancelled
                            break
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"Downloading video {index}/{total_videos}"))
                        ydl.download([entry['webpage_url']])
                else:
                    ydl.download([url])
                
                # Add to downloads list
                title = info.get('title', 'Unknown Title')
                download_info = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} - {title}"
                self.downloads.append({
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'title': title,
                    'path': os.path.join(self.output_dir, f"{title}.mp3")
                })
                self.root.after(0, lambda: self.downloads_listbox.insert(0, download_info))
            
            self.root.after(0, lambda: self.status_label.config(text="Download Complete!"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download failed: {str(e)}"))
            self.root.after(0, lambda: self.status_label.config(text="Download Failed"))
        
        finally:
            self.currently_downloading = False
            self.root.after(0, lambda: self.download_button.config(state='normal'))
            self.root.after(0, lambda: self.cancel_button.config(state='disabled'))
            self.root.after(0, lambda: self.progress_var.set(0))
    
    def update_progress(self, d):
        if d['status'] == 'downloading':
            try:
                progress = float(d['_percent_str'].replace('%', ''))
                self.progress_var.set(progress)
                self.status_label.config(
                    text=f"Downloading: {progress:.1f}% (Speed: {d.get('_speed_str', 'N/A')})")
            except:
                pass
        elif d['status'] == 'finished':
            self.status_label.config(text="Converting to MP3...")
            self.progress_var.set(100)
    
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the download history?"):
            self.downloads_listbox.delete(0, tk.END)
            self.downloads = []
    
    def open_file_location(self):
        selection = self.downloads_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.downloads[index]['path']
            folder_path = os.path.dirname(file_path)
            os.startfile(folder_path)
    
    def copy_file_path(self):
        selection = self.downloads_listbox.curselection()
        if selection:
            index = selection[0]
            file_path = self.downloads[index]['path']
            self.root.clipboard_clear()
            self.root.clipboard_append(file_path)
    
    def remove_from_list(self):
        selection = self.downloads_listbox.curselection()
        if selection:
            index = selection[0]
            self.downloads_listbox.delete(index)
            self.downloads.pop(index)
    
    def show_about(self):
        about_text = """YouTube MP3 Downloader
Version 2.0
        
A simple tool to download YouTube videos as MP3 files.
        
Features:
- Video preview
- Playlist support
- Custom output directory
- Multiple quality options
- Dark mode support
        
Created with Python and tkinter

Credit to its solely creator: @GitHub Yujinhmnida
"""
        
        messagebox.showinfo("About", about_text)
    
    def show_instructions(self):
        instructions_text = """How to use:

1. Enter a YouTube URL in the input field
2. Click 'Preview' to see video information
3. Select your preferred audio quality
4. Choose whether to download entire playlist
5. Select output directory if needed
6. Click 'Download' to start

Tips:
- Right-click downloads to see more options
- Use dark mode for night viewing
- You can cancel downloads in progress
- Preview helps verify correct video"""
        
        messagebox.showinfo("Instructions", instructions_text)

def main():
    root = tk.Tk()
    app = YouTubeMp3DownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()