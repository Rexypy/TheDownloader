import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import sys
import subprocess
from urllib.parse import urlparse
import yt_dlp
import platform
import re

# Set appearance and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class VideoDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("The Downloader")
        self.root.geometry("950x650")  # Small window size
        self.root.minsize(850, 550)    # Minimum size
        self.root.resizable(True, True)
        
        # colors
        self.colors = {
            'bg': '#0f0f0f',
            'fg': '#ffffff',
            'frame_bg': '#1a1a1a',
            'accent': '#540202',
            'secondary': '#14b5aa',
            'success': '#51cf66',
            'error': '#ff5252',
            'warning': '#401115',
            'purple': '#9c88ff',
            'blue': '#74c0fc',
            'pink': '#4f1f1f',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2'
        }
        
        # Root window
        self.root.configure(fg_color=self.colors['bg'])
        
        # Default stuff
        self.file_format = 'mp4'
        self.download_type = 'video'  # 'video' or 'audio'
        self.download_path = os.path.expanduser('~/Downloads')
        self.quiet = False
        self.title_template = '%(title)s'
        self.downloading = False
        self.downloaded_file_path = None

        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            self.ffmpeg_path = os.path.join(bundle_dir, 'ffmpeg.exe')
            self.ffprobe_path = os.path.join(bundle_dir, 'ffprobe.exe')
            if not os.path.exists(self.ffmpeg_path):
                self.ffmpeg_path = None
                self.ffprobe_path = None
        else:
            self.ffmpeg_path = None
            self.ffprobe_path = None
        
        # Scrollable container
        self.create_scrollable_container()
        self.create_download_folder()
        
    def create_scrollable_container(self):
        # Main scrollable container
        self.main_container = ctk.CTkScrollableFrame(self.root, fg_color=self.colors['bg'])
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        self.main_container.columnconfigure(0, weight=1)
        
        # Widgets inside scrollable container
        self.create_widgets()
        
    def create_widgets(self):
        # Title
        title_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        
        title_label = ctk.CTkLabel(title_frame, text="🎬 The Downloader", 
                                  font=("Segoe UI", 24, "bold"), 
                                  text_color=self.colors['accent'])
        title_label.pack()
        
        subtitle_label = ctk.CTkLabel(title_frame, text="Download videos & audio in style", 
                                     font=("Segoe UI", 12), 
                                     text_color=self.colors['secondary'])
        subtitle_label.pack(pady=(5, 0))
        
        # URL input
        url_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color=self.colors['frame_bg'])
        url_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        url_label = ctk.CTkLabel(url_frame, text="Video URL:", 
                                font=("Segoe UI", 12, "bold"),
                                text_color=self.colors['secondary'])
        url_label.pack(anchor="w", padx=20, pady=(15, 5))
        
        url_entry_frame = ctk.CTkFrame(url_frame, fg_color="transparent")
        url_entry_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(url_entry_frame, textvariable=self.url_var, 
                                    font=("Segoe UI", 12), height=40,
                                    fg_color=self.colors['frame_bg'],
                                    border_color=self.colors['accent'],
                                    text_color=self.colors['fg'])
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        clear_btn = ctk.CTkButton(url_entry_frame, text="Clear", 
                                 command=self.clear_url, width=80,
                                 fg_color=self.colors['frame_bg'],
                                 hover_color=self.colors['accent'],
                                 text_color=self.colors['fg'],
                                 border_width=1,  # Black border
                                 border_color="#000000")
        clear_btn.pack(side="right")
        
        #  Download type
        type_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color=self.colors['frame_bg'])
        type_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        type_label = ctk.CTkLabel(type_frame, text="Download Type:", 
                                 font=("Segoe UI", 12, "bold"),
                                 text_color=self.colors['secondary'])
        type_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        radio_frame = ctk.CTkFrame(type_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        self.type_var = ctk.StringVar(value="video")
        
        # NEW: Custom radio buttons without circles - using button-like appearance
        self.video_btn = ctk.CTkButton(radio_frame, text="Video", 
                                      width=100, height=35,
                                      fg_color=self.colors['accent'] if self.type_var.get() == "video" else self.colors['frame_bg'],
                                      hover_color=self.colors['pink'],
                                      text_color=self.colors['fg'],
                                      font=("Segoe UI", 12, "bold" if self.type_var.get() == "video" else "normal"),
                                      command=lambda: self.set_download_type("video"))
        self.video_btn.pack(side="left", padx=(0, 15))
        
        self.audio_btn = ctk.CTkButton(radio_frame, text="Audio Only", 
                                      width=100, height=35,
                                      fg_color=self.colors['accent'] if self.type_var.get() == "audio" else self.colors['frame_bg'],
                                      hover_color=self.colors['pink'],
                                      text_color=self.colors['fg'],
                                      font=("Segoe UI", 12, "bold" if self.type_var.get() == "audio" else "normal"),
                                      command=lambda: self.set_download_type("audio"))
        self.audio_btn.pack(side="left")
        
        # Settings
        settings_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color=self.colors['frame_bg'])
        settings_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        settings_label = ctk.CTkLabel(settings_frame, text="Download Settings:", 
                                     font=("Segoe UI", 12, "bold"),
                                     text_color=self.colors['secondary'])
        settings_label.pack(anchor="w", padx=20, pady=(15, 10))
        
        # Output folder
        folder_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        folder_frame.pack(fill="x", padx=20, pady=10)
        
        folder_label = ctk.CTkLabel(folder_frame, text="Output Folder:", 
                                   font=("Segoe UI", 11),
                                   text_color=self.colors['fg'])
        folder_label.pack(side="left", padx=(0, 15))
        
        self.folder_var = ctk.StringVar(value=self.download_path)
        folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.folder_var, 
                                   state='readonly', height=35,
                                   fg_color=self.colors['frame_bg'],
                                   border_color=self.colors['accent'],
                                   text_color=self.colors['fg'])
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ctk.CTkButton(folder_frame, text="Browse", 
                                   command=self.browse_folder, width=100,
                                   fg_color=self.colors['frame_bg'],
                                   hover_color=self.colors['accent'],
                                   text_color=self.colors['fg'],
                                   border_width=1,  # Black border
                                   border_color="#000000")
        browse_btn.pack(side="right")
        
        # Format and Quality
        format_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        format_frame.pack(fill="x", padx=20, pady=(0, 15))
        
        format_label = ctk.CTkLabel(format_frame, text="Format:", 
                                   font=("Segoe UI", 11),
                                   text_color=self.colors['fg'])
        format_label.pack(side="left", padx=(0, 15))
        
        self.format_var = ctk.StringVar(value=self.file_format)
        self.format_combo = ctk.CTkComboBox(format_frame, variable=self.format_var,
                                          values=['mp4', 'mkv', 'webm', 'avi'], 
                                          width=120, dropdown_fg_color=self.colors['frame_bg'],
                                          button_color=self.colors['accent'],
                                          button_hover_color=self.colors['pink'],
                                          fg_color=self.colors['frame_bg'],
                                          border_color=self.colors['accent'],
                                          text_color=self.colors['fg'],
                                          dropdown_text_color=self.colors['fg'],
                                          dropdown_hover_color=self.colors['accent'])
        self.format_combo.pack(side="left", padx=(0, 30))
        
        quality_label = ctk.CTkLabel(format_frame, text="Quality:", 
                                    font=("Segoe UI", 11),
                                    text_color=self.colors['fg'])
        quality_label.pack(side="left", padx=(0, 15))
        
        self.quality_var = ctk.StringVar(value="Best")
        self.quality_combo = ctk.CTkComboBox(format_frame, variable=self.quality_var,
                                           values=['Best', 'Worst', '1080p', '720p', '480p', '360p'], 
                                           width=120, dropdown_fg_color=self.colors['frame_bg'],
                                           button_color=self.colors['accent'],
                                           button_hover_color=self.colors['pink'],
                                           fg_color=self.colors['frame_bg'],
                                           border_color=self.colors['accent'],
                                           text_color=self.colors['fg'],
                                           dropdown_text_color=self.colors['fg'],
                                           dropdown_hover_color=self.colors['accent'])
        self.quality_combo.pack(side="left")
        
        # Control buttons
        button_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        button_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        
        self.download_btn = ctk.CTkButton(button_frame, text="Download Video", 
                                         command=self.start_download, width=180, height=40,
                                         font=("Segoe UI", 12, "bold"),
                                         fg_color=self.colors['accent'],
                                         hover_color=self.colors['pink'],
                                         text_color=self.colors['bg'])
        self.download_btn.pack(side="left", padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(button_frame, text="Stop", 
                                     command=self.stop_download, 
                                     state='disabled', width=100, height=40,
                                     font=("Segoe UI", 12),
                                     fg_color=self.colors['frame_bg'],
                                     hover_color=self.colors['error'],
                                     text_color=self.colors['fg'])
        self.stop_btn.pack(side="left", padx=(0, 10))
        
        self.info_btn = ctk.CTkButton(button_frame, text="Info", 
                                     command=self.get_video_info, width=100, height=40,
                                     font=("Segoe UI", 12),
                                     fg_color=self.colors['frame_bg'],
                                     hover_color=self.colors['secondary'],
                                     text_color=self.colors['fg'])
        self.info_btn.pack(side="left")
        
        # Progress
        progress_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color=self.colors['frame_bg'])
        progress_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        
        progress_label = ctk.CTkLabel(progress_frame, text="Progress:", 
                                     font=("Segoe UI", 12, "bold"),
                                     text_color=self.colors['secondary'])
        progress_label.pack(anchor="w", padx=20, pady=(15, 5))
        
        self.progress_var = ctk.StringVar(value="Ready to download!")
        self.status_label = ctk.CTkLabel(progress_frame, textvariable=self.progress_var,
                                       font=("Segoe UI", 11),
                                       text_color=self.colors['fg'])
        self.status_label.pack(anchor="w", padx=20, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame, mode='determinate',
                                             height=15, corner_radius=10,
                                             progress_color=self.colors['accent'],
                                             fg_color=self.colors['bg'])
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 15))
        self.progress_bar.set(0)
        
        # Log output
        log_frame = ctk.CTkFrame(self.main_container, corner_radius=10, fg_color=self.colors['frame_bg'])
        log_frame.grid(row=6, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        log_label = ctk.CTkLabel(log_frame, text="Download Log:", 
                                font=("Segoe UI", 12, "bold"),
                                text_color=self.colors['secondary'])
        log_label.pack(anchor="w", padx=20, pady=(15, 5))
        
        # Scrolled text
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, wrap="word",
                                                bg=self.colors['frame_bg'],
                                                fg=self.colors['fg'],
                                                insertbackground=self.colors['accent'],
                                                selectbackground=self.colors['accent'],
                                                selectforeground='white',
                                                font=("Consolas", 10),
                                                relief="flat",
                                                highlightthickness=0)
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        # Clear log button
        clear_log_btn = ctk.CTkButton(log_frame, text="Clear Log", command=self.clear_log,
                                     width=100, height=35,
                                     fg_color=self.colors['frame_bg'],
                                     hover_color=self.colors['warning'],
                                     text_color=self.colors['fg'],
                                     border_width=1,  # Black border
                                     border_color="#000000")
        clear_log_btn.pack(pady=(0, 15))
        
        self.download_process = None
        self.update_format_options()
        
    def set_download_type(self, download_type):
        """Set type + feedback"""
        self.type_var.set(download_type)
        
        # Update button styles
        if download_type == "video":
            self.video_btn.configure(fg_color=self.colors['accent'], font=("Segoe UI", 12, "bold"))
            self.audio_btn.configure(fg_color=self.colors['frame_bg'], font=("Segoe UI", 12, "normal"))
        else:
            self.video_btn.configure(fg_color=self.colors['frame_bg'], font=("Segoe UI", 12, "normal"))
            self.audio_btn.configure(fg_color=self.colors['accent'], font=("Segoe UI", 12, "bold"))
            
        self.on_type_change()
        
    def on_type_change(self):
        """Handle type change"""
        self.download_type = self.type_var.get()
        self.update_format_options()
        
    def update_format_options(self):
        """Update format options"""
        if self.download_type == "audio":
            self.format_combo.configure(values=['mp3', 'wav', 'aac', 'm4a', 'ogg', 'flac'])
            self.format_var.set('mp3')
            self.download_btn.configure(text="Download Audio")
            self.quality_combo.configure(values=['Best', '320k', '256k', '192k', '128k', '96k'])
        else:
            self.format_combo.configure(values=['mp4', 'mkv', 'webm', 'avi'])
            self.format_var.set('mp4')
            self.download_btn.configure(text="Download Video")
            self.quality_combo.configure(values=['Best', 'Worst', '1080p', '720p', '480p', '360p'])
        
        self.quality_var.set('Best')
        
    def create_download_folder(self):
        """Create download folder if doesn't exist"""
        try:
            os.makedirs(self.download_path, exist_ok=True)
            self.log_message("Download folder ready!", "success")
        except Exception as e:
            self.log_message(f"Warning: Could not create download folder: {e}", "warning")
    
    def clear_url(self):
        """Clear URL input"""
        self.url_var.set("")
        self.log_message("URL cleared", "info")
        
    def browse_folder(self):
        """Open folder browser"""
        folder = filedialog.askdirectory(initialdir=self.download_path)
        if folder:
            self.folder_var.set(folder)
            self.download_path = folder
            self.log_message(f"Output folder changed to: {folder}", "info")
            
    def clear_log(self):
        """Clear log text"""
        self.log_text.delete(1.0, "end")
        self.log_message("Log cleared", "info")
        
    def log_message(self, message, msg_type="info"):
        """Add message to log text"""
        timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        
        # timestamp
        self.log_text.insert("end", f"[{timestamp}] ")
        
        # tags
        if not hasattr(self, 'tags_configured'):
            self.log_text.tag_configure("info", foreground=self.colors['blue'])
            self.log_text.tag_configure("success", foreground=self.colors['success'])
            self.log_text.tag_configure("error", foreground=self.colors['error'])
            self.log_text.tag_configure("warning", foreground=self.colors['warning'])
            self.log_text.tag_configure("accent", foreground=self.colors['accent'])
            self.log_text.tag_configure("secondary", foreground=self.colors['secondary'])
            self.log_text.tag_configure("purple", foreground=self.colors['purple'])
            self.tags_configured = True
        
        # add message
        start_pos = self.log_text.index("end-1c")
        self.log_text.insert("end", message + "\n")
        end_pos = self.log_text.index("end-1c")
        self.log_text.tag_add(msg_type, start_pos, end_pos)
        
        self.log_text.see("end")
        self.root.update_idletasks()
        
    def get_format_selector(self):
        """yt-dlp format selector"""
        quality = self.quality_var.get()
        
        if self.download_type == "audio":
            if quality == "Best":
                return 'bestaudio/best'
            elif quality == "320k":
                return 'bestaudio[abr<=320]/best'
            elif quality == "256k":
                return 'bestaudio[abr<=256]/best'
            elif quality == "192k":
                return 'bestaudio[abr<=192]/best'
            elif quality == "128k":
                return 'bestaudio[abr<=128]/best'
            elif quality == "96k":
                return 'bestaudio[abr<=96]/best'
            else:
                return 'bestaudio/best'
        else:
            if quality == "Best":
                return 'bestvideo+bestaudio/best'
            elif quality == "Worst":
                return 'worstvideo+worstaudio/worst'
            elif quality == "1080p":
                return 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            elif quality == "720p":
                return 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == "480p":
                return 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            elif quality == "360p":
                return 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            else:
                return 'bestvideo+bestaudio/best'
                
    def get_video_info(self):
        """video info"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a video URL first!")
            return
            
        self.log_message("Fetching video information...", "accent")
        
        def info_worker():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration_string', 'Unknown')
                    uploader = info.get('uploader', 'Unknown')
                    view_count = info.get('view_count', 0)
                    upload_date = info.get('upload_date', 'Unknown')
                    
                    # view count formatting
                    if view_count:
                        if view_count >= 1000000:
                            view_str = f"{view_count/1000000:.1f}M views"
                        elif view_count >= 1000:
                            view_str = f"{view_count/1000:.1f}K views"
                        else:
                            view_str = f"{view_count} views"
                    else:
                        view_str = "Unknown views"
                    
                    self.root.after(0, lambda: self.log_message(f"Title: {title}", "purple"))
                    self.root.after(0, lambda: self.log_message(f"Duration: {duration}", "secondary"))
                    self.root.after(0, lambda: self.log_message(f"Uploader: {uploader}", "info"))
                    self.root.after(0, lambda: self.log_message(f"{view_str}", "info"))
                    self.root.after(0, lambda: self.log_message(f"Upload Date: {upload_date}", "info"))
                    
            except Exception as e:
                error_msg = f"Failed to get video info: {str(e)}"
                self.root.after(0, lambda: self.log_message(error_msg, "error"))
        
        # Start info fetch
        info_thread = threading.Thread(target=info_worker)
        info_thread.daemon = True
        info_thread.start()
    
    def clean_ansi_codes(self, text):
        """Remove ANSI"""
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_escape.sub('', text)
            
    def download_progress_hook(self, d):
        """Progress hook"""
        if d['status'] == 'downloading':
            try:
                # progress percentage
                if '_percent_str' in d and d['_percent_str'] != 'NA%':
                    clean_percent = self.clean_ansi_codes(d['_percent_str'])
                    percent = float(clean_percent.strip('%')) / 100.0
                    
                    # Update progress bar
                    self.root.after(0, lambda: self.progress_bar.set(percent))
                    
                    # Update status label
                    speed_str = d.get('_speed_str', 'N/A')
                    if speed_str != 'N/A':
                        speed_str = self.clean_ansi_codes(speed_str)
                        
                    eta_str = d.get('_eta_str', 'N/A')
                    if eta_str != 'N/A':
                        eta_str = self.clean_ansi_codes(eta_str)
                        
                    self.root.after(0, lambda: self.progress_var.set(
                        f"Downloading: {int(float(clean_percent.strip('%')))}% | Speed: {speed_str} | ETA: {eta_str}"
                    ))
            except Exception as e:
                # Log the error but don't break
                self.log_message(f"Progress update error: {e}", "warning")
        elif d['status'] == 'finished':
            # Set progress to 100% when download completes
            self.root.after(0, lambda: self.progress_bar.set(1.0))
            
    def dwn_vid(self, video_url):
        """Download video or audio"""
        try:
            # Create download folder if doesn't exist
            os.makedirs(self.download_path, exist_ok=True)
            
            if self.download_type == "audio":
                ydl_opts = {
                    'format': self.get_format_selector(),
                    'outtmpl': os.path.join(self.download_path, self.title_template + '.%(ext)s'),
                    'quiet': self.quiet,
                    'noplaylist': True,
                    'progress_hooks': [self.download_progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': self.format_var.get(),
                        'preferredquality': '320' if self.quality_var.get() == 'Best' else self.quality_var.get().replace('k', ''),
                    }],
                }
                if self.ffmpeg_path and self.ffprobe_path:
                    ydl_opts['ffmpeg_location'] = self.ffmpeg_path
                    ydl_opts['ffprobe_location'] = self.ffprobe_path
            else:
                ydl_opts = {
                    'format': self.get_format_selector(),
                    'outtmpl': os.path.join(self.download_path, self.title_template + '.%(ext)s'),
                    'merge_output_format': self.format_var.get(),
                    'quiet': self.quiet,
                    'noplaylist': True,
                    'progress_hooks': [self.download_progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': self.format_var.get(),
                    }],
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # get video info
                self.log_message("Extracting video information...", "accent")
                info = ydl.extract_info(video_url, download=False)
                title = info.get('title', 'Unknown')
                duration = info.get('duration_string', 'Unknown')
                uploader = info.get('uploader', 'Unknown')
                
                self.log_message(f"Title: {title}", "purple")
                self.log_message(f"Duration: {duration} | Uploader: {uploader}", "secondary")
                
                if self.download_type == "audio":
                    self.log_message("Starting audio download...", "accent")
                else:
                    self.log_message("Starting video download...", "accent")
                
                # download
                result = ydl.download([video_url])
                
                # get the actual file path
                if result == 0:  # Success
                    # find the downloaded file
                    ext = self.format_var.get()
                    filename = f"{title}.{ext}"
                    self.downloaded_file_path = os.path.join(self.download_path, filename)
                    
                    if self.download_type == "audio":
                        self.log_message("Audio download completed successfully!", "success")
                    else:
                        self.log_message("Video download completed successfully!", "success")
                    return True
                else:
                    return False
                
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.log_message(error_msg, "error")
            messagebox.showerror("Download Error", error_msg)
            return False
            
    def show_success_popup(self):
        """Show locator popup"""
        popup = ctk.CTkToplevel(self.root)
        popup.title("Download Complete")
        popup.geometry("600x250")
        popup.transient(self.root)
        popup.grab_set()
        
        # Center
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        popup_width = 600
        popup_height = 250
        x = root_x + (root_width - popup_width) // 2
        y = root_y + (root_height - popup_height) // 2
        
        popup.geometry(f"+{x}+{y}")
        
        # content
        content_frame = ctk.CTkFrame(popup, fg_color=self.colors['frame_bg'])
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # message label
        msg_label = ctk.CTkLabel(content_frame, text="Download completed successfully!", 
                                font=("Segoe UI", 14, "bold"),
                                text_color=self.colors['success'])
        msg_label.pack(pady=(10, 5))
        
        # folder path label
        path_label = ctk.CTkLabel(content_frame, text=f"File saved to:", 
                                 font=("Segoe UI", 12),
                                 text_color=self.colors['fg'])
        path_label.pack(pady=(5, 0))
        
        # clickable folder path
        folder_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        folder_frame.pack(pady=5, fill="x", padx=20)
        
        # truncate path if too long
        display_path = self.downloaded_file_path
        if len(display_path) > 50:
            display_path = "..." + display_path[-47:]
            
        folder_link = ctk.CTkLabel(folder_frame, text=display_path, 
                                  font=("Segoe UI", 11, "underline"),
                                  text_color=self.colors['accent'],
                                  cursor="hand2")
        folder_link.pack()
        folder_link.bind("<Button-1>", lambda e: self.open_file_location(self.downloaded_file_path))
        
        # full path tooltip
        full_path_label = ctk.CTkLabel(folder_frame, text=self.downloaded_file_path, 
                                      font=("Segoe UI", 9),
                                      text_color=self.colors['secondary'])
        full_path_label.pack(pady=(5, 0))
        
        # button frame
        button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        # open folder button
        open_btn = ctk.CTkButton(button_frame, text="Open File Location", 
                                command=lambda: self.open_file_location(self.downloaded_file_path),
                                width=150, height=35,
                                fg_color=self.colors['accent'],
                                hover_color=self.colors['pink'])
        open_btn.pack(side="left", padx=(0, 10))
        
        # close button
        close_btn = ctk.CTkButton(button_frame, text="Close", 
                                 command=popup.destroy,
                                 width=100, height=35,
                                 fg_color=self.colors['frame_bg'],
                                 hover_color=self.colors['secondary'])
        close_btn.pack(side="left")
        
    def open_file_location(self, path):
        """Open file location in file explorer"""
        try:
            if platform.system() == "Windows":
                os.startfile(os.path.dirname(path))
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", os.path.dirname(path)])
            else:  # Linux
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        except Exception as e:
            self.log_message(f"Failed to open file location: {e}", "error")
            messagebox.showerror("Error", f"Could not open file location:\n{str(e)}")
            
    def start_download(self):
        """Start download in separate thread"""
        if self.downloading:
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a video URL first!")
            return
            
        # reset progress bar
        self.progress_bar.set(0)
        
        # update UI for download state
        self.downloading = True
        self.download_btn.configure(state='disabled')
        self.stop_btn.configure(state='normal')
        self.info_btn.configure(state='disabled')
        
        if self.download_type == "audio":
            self.progress_var.set("Downloading audio...")
        else:
            self.progress_var.set("Downloading video...")
            
        # start download in separate thread
        self.download_thread = threading.Thread(target=self.download_worker, args=(url,))
        self.download_thread.daemon = True
        self.download_thread.start()
        
    def download_worker(self, url):
        """Worker function for download thread"""
        try:
            success = self.dwn_vid(url)
            if success:
                if self.download_type == "audio":
                    self.root.after(0, lambda: self.progress_var.set("Audio download completed!"))
                else:
                    self.root.after(0, lambda: self.progress_var.set("Video download completed!"))
                    
                # show success popup
                self.root.after(0, self.show_success_popup)
            else:
                self.root.after(0, lambda: self.progress_var.set("Download failed"))
        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            self.root.after(0, lambda: self.progress_var.set("Download failed"))
            self.root.after(0, lambda: self.log_message(error_msg, "error"))
        finally:
            self.root.after(0, self.reset_ui_after_download)
            
    def stop_download(self):
        """Stop current download"""
        # note: doesn't work :d
        if hasattr(self, 'download_thread') and self.download_thread.is_alive():
            self.log_message("Download stop requested...", "warning")
            self.reset_ui_after_download()
            
    def reset_ui_after_download(self):
        """Reset UI elements after download completion"""
        self.downloading = False
        self.download_btn.configure(state='normal')
        self.stop_btn.configure(state='disabled')
        self.info_btn.configure(state='normal')
        if hasattr(self, 'progress_var') and ("Downloading" in self.progress_var.get() or "failed" in self.progress_var.get()):
            self.progress_var.set("Ready for next download!")


def main():
    """Main function to run the application"""
    root = ctk.CTk()
    
    app = VideoDownloaderGUI(root)
    
    # Add startup messages cause otherwise the log would be empty and ugly 
    app.log_message("Modern Video Downloader started!", "success")
    app.log_message("Tip: You can download from YouTube, TikTok, Instagram, and many more platforms! ;) ", "info")
    app.log_message("Switch to Audio mode to download music files!", "secondary")
    
    root.mainloop()


if __name__ == "__main__":
    main()