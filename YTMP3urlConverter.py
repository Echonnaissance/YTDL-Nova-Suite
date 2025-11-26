import subprocess
import os
import sys
import threading
import re
import glob
import json
import urllib.request
from io import BytesIO
from tkinter import Tk, Label, Entry, Button, messagebox, StringVar, Text, Scrollbar, Frame, Checkbutton, BooleanVar, DoubleVar, Toplevel, Canvas
from tkinter import ttk
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def get_base_path():
    """Get the base path for the application (works for both script and exe)"""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.abspath(__file__))


class YouTubeDownloader:
    def __init__(self):
        # Set paths to essential tools using base path
        base_path = get_base_path()
        self.FFMPEG_PATH = os.path.join(base_path, "ffmpeg.exe")
        self.YTDLP_PATH = os.path.join(base_path, "yt-dlp.exe")
        self.CONFIG_FILE = os.path.join(base_path, "config.json")

        # Check if tools are available
        self.ytdlp_available = os.path.isfile(self.YTDLP_PATH)
        self.ffmpeg_available = os.path.isfile(self.FFMPEG_PATH)

        # Load settings
        self.settings = self.load_settings()

        # Batch processing state
        self.batch_urls = []
        self.current_batch_index = 0

        self.setup_gui()

    def load_settings(self):
        """Load settings from config file"""
        defaults = {
            "dark_mode": False,
            "embed_thumbnails": True,
            "batch_mode": False
        }

        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    return {**defaults, **json.load(f)}
        except:
            pass
        return defaults

    def save_settings(self):
        """Save settings to config file"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def setup_gui(self):
        """Initialize the graphical user interface"""
        self.root = Tk()
        self.root.title("YouTube Downloader")
        self.root.geometry("800x500")
        self.root.resizable(False, False)

        # Modern styling
        style = ttk.Style()
        style.theme_use('clam')  # Use clam theme as base for customization

        # Configure progress bar style
        style.configure("Modern.Horizontal.TProgressbar",
                        troughcolor='#e9ecef',
                        background='#0d6efd',
                        borderwidth=0,
                        thickness=20)

        # Variables
        self.progress_var = DoubleVar()
        self.progress_var.set(0.0)
        self.status_var = StringVar()
        self.status_var.set("Ready - Enter YouTube URL(s)")
        self.show_console = BooleanVar()
        self.show_console.set(False)
        self.dark_mode = BooleanVar()
        self.dark_mode.set(self.settings.get("dark_mode", False))
        self.embed_thumbnails = BooleanVar()
        self.embed_thumbnails.set(self.settings.get("embed_thumbnails", True))
        self.batch_mode = BooleanVar()
        self.batch_mode.set(self.settings.get("batch_mode", False))

        # Modern color schemes
        self.light_colors = {
            "bg": "#f8f9fa",
            "fg": "#212529",
            "secondary_fg": "#6c757d",
            "status_bg": "#e9ecef",
            "button_util": "#6c757d",
            "console_bg": "#212529",
            "console_fg": "#39ff14",
            "entry_bg": "#ffffff",
            "border": "#dee2e6",
            "accent": "#0d6efd"
        }

        self.dark_colors = {
            "bg": "#1a1d23",
            "fg": "#e9ecef",
            "secondary_fg": "#adb5bd",
            "status_bg": "#212529",
            "button_util": "#495057",
            "console_bg": "#0d1117",
            "console_fg": "#39ff14",
            "entry_bg": "#2d333b",
            "border": "#373e47",
            "accent": "#58a6ff"
        }

        self.create_main_interface()
        self.create_console_section()
        self.apply_theme()
        self.toggle_batch_mode()  # Set initial mode

        # Check tool availability
        if not self.ytdlp_available:
            self.status_var.set("ERROR: yt-dlp.exe not found!")
            messagebox.showerror("Tool Missing",
                                 "yt-dlp.exe not found at specified path.\n"
                                 "Please download from: https://github.com/yt-dlp/yt-dlp/releases")

        if not PIL_AVAILABLE:
            messagebox.showwarning("PIL Not Found",
                                   "Pillow (PIL) library not found.\n"
                                   "Thumbnails in playlist preview won't display.\n\n"
                                   "Install with: pip install Pillow")

    def get_colors(self):
        """Get current color scheme based on dark mode setting"""
        return self.dark_colors if self.dark_mode.get() else self.light_colors

    def apply_theme(self):
        """Apply the current theme to all widgets"""
        colors = self.get_colors()

        # Update progress bar style for current theme
        style = ttk.Style()
        style.configure("Modern.Horizontal.TProgressbar",
                        troughcolor=colors["status_bg"],
                        background=colors["accent"],
                        borderwidth=0,
                        thickness=20)

        # Root window
        self.root.configure(bg=colors["bg"])

        # Main container
        self.main_container.configure(bg=colors["bg"])

        # Header
        self.header.configure(bg=colors["bg"], fg=colors["fg"])

        # URL frame and components with modern borders
        self.url_frame.configure(bg=colors["bg"])
        self.url_label.configure(bg=colors["bg"], fg=colors["secondary_fg"])
        self.url_entry.configure(bg=colors["entry_bg"], fg=colors["fg"],
                                 insertbackground=colors["fg"],
                                 highlightbackground=colors["border"],
                                 highlightcolor=colors["accent"])

        # Batch text area with modern borders
        self.batch_text.configure(bg=colors["entry_bg"], fg=colors["fg"],
                                  insertbackground=colors["fg"],
                                  highlightbackground=colors["border"],
                                  highlightcolor=colors["accent"])

        # Mode toggle
        self.mode_frame.configure(bg=colors["bg"])
        self.batch_mode_check.configure(bg=colors["bg"], fg=colors["fg"],
                                        activebackground=colors["bg"],
                                        selectcolor=colors["bg"])

        # Button container
        self.button_container.configure(bg=colors["bg"])

        # Progress frame
        self.progress_frame.configure(bg=colors["bg"])

        # Status label
        self.status_label.configure(bg=colors["status_bg"], fg=colors["fg"])

        # Controls frame
        self.controls_frame.configure(bg=colors["bg"])
        self.console_check.configure(bg=colors["bg"], fg=colors["fg"],
                                     activebackground=colors["bg"],
                                     selectcolor=colors["bg"])
        self.dark_mode_check.configure(bg=colors["bg"], fg=colors["fg"],
                                       activebackground=colors["bg"],
                                       selectcolor=colors["bg"])

        # Options frame
        self.options_frame.configure(bg=colors["bg"])
        self.thumbnail_check.configure(bg=colors["bg"], fg=colors["fg"],
                                       activebackground=colors["bg"],
                                       selectcolor=colors["bg"])

        # Utility buttons
        self.format_btn.configure(bg=colors["button_util"])
        self.clean_btn.configure(bg=colors["button_util"])
        self.update_btn.configure(bg=colors["button_util"])
        self.preview_btn.configure(bg=colors["button_util"])

        # Console frame with modern styling
        self.console_frame.configure(bg=colors["bg"])
        self.console_label.configure(bg=colors["bg"], fg=colors["fg"])
        self.console_text.configure(
            bg=colors["console_bg"], fg=colors["console_fg"],
            highlightbackground=colors["border"],
            highlightcolor=colors["accent"])
        self.clear_console_btn.configure(bg=colors["button_util"])

    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.settings["dark_mode"] = self.dark_mode.get()
        self.save_settings()
        self.apply_theme()

    def toggle_batch_mode(self):
        """Toggle between single URL and batch URLs mode"""
        self.settings["batch_mode"] = self.batch_mode.get()
        self.save_settings()

        if self.batch_mode.get():
            # Hide single URL entry
            self.url_entry.pack_forget()
            # Show batch text area
            self.batch_text.pack(fill='both', expand=True, pady=(0, 5))
            self.batch_scroll.pack(side='right', fill='y')
            self.url_label.configure(
                text="Video or Playlist URLs (one per line):")
        else:
            # Hide batch text area
            self.batch_text.pack_forget()
            self.batch_scroll.pack_forget()
            # Show single URL entry
            self.url_entry.pack(fill='x', ipady=6)
            self.url_label.configure(text="Video or Playlist URL:")

    def create_main_interface(self):
        """Create the main control panel"""
        self.main_container = Frame(self.root)
        self.main_container.pack(fill='both', expand=True, padx=25, pady=20)

        # Modern Header with icon
        self.header = Label(self.main_container, text="🎬 YouTube Downloader",
                            font=("Segoe UI", 20, "bold"))
        self.header.pack(pady=(0, 20))

        # Mode toggle
        self.mode_frame = Frame(self.main_container)
        self.mode_frame.pack(fill='x', pady=(0, 10))

        self.batch_mode_check = Checkbutton(self.mode_frame,
                                            text="📋 Batch Mode (multiple URLs)",
                                            variable=self.batch_mode,
                                            command=self.toggle_batch_mode,
                                            font=("Segoe UI", 9, "bold"))
        self.batch_mode_check.pack(side='left')

        # URL Input Section
        self.url_frame = Frame(self.main_container)
        self.url_frame.pack(fill='both', expand=True, pady=(0, 10))

        self.url_label = Label(self.url_frame, text="Video or Playlist URL:",
                               font=("Segoe UI", 10))
        self.url_label.pack(anchor='w', pady=(0, 5))

        # Single URL entry with modern styling
        self.url_entry = Entry(self.url_frame, width=60, font=("Segoe UI", 11),
                               relief="flat", bd=0, highlightthickness=2)
        self.url_entry.bind('<Return>', lambda e: self.download_video())

        # Batch URLs text area (with scrollbar)
        batch_container = Frame(self.url_frame)

        self.batch_scroll = Scrollbar(batch_container)
        self.batch_text = Text(batch_container, height=6, width=60,
                               font=("Segoe UI", 11), relief="flat", bd=0,
                               wrap='none', yscrollcommand=self.batch_scroll.set,
                               highlightthickness=2)
        self.batch_scroll.config(command=self.batch_text.yview)

        batch_container.pack(fill='both', expand=True)
        self.batch_text.pack(side='left', fill='both', expand=True)

        # Download Buttons Section
        self.button_container = Frame(self.main_container)
        self.button_container.pack(fill='x', pady=(0, 8))

        # Modern Video Download Button
        self.video_btn = Button(self.button_container,
                                text="📹 Download Video",
                                command=self.download_video,
                                bg="#0d6efd", fg="white",
                                font=("Segoe UI", 11, "bold"),
                                relief="flat", cursor="hand2", bd=0,
                                activebackground="#0b5ed7",
                                activeforeground="white")
        self.video_btn.pack(side='left', fill='both',
                            expand=True, padx=(0, 8), ipady=12)
        self.video_btn.bind(
            "<Enter>", lambda e: self.video_btn.config(bg="#0b5ed7"))
        self.video_btn.bind(
            "<Leave>", lambda e: self.video_btn.config(bg="#0d6efd"))

        # Modern Audio Download Button
        self.audio_btn = Button(self.button_container,
                                text="🎵 Download Audio",
                                command=self.download_audio,
                                bg="#198754", fg="white",
                                font=("Segoe UI", 11, "bold"),
                                relief="flat", cursor="hand2", bd=0,
                                activebackground="#157347",
                                activeforeground="white")
        self.audio_btn.pack(side='left', fill='both',
                            expand=True, padx=(8, 0), ipady=12)
        self.audio_btn.bind(
            "<Enter>", lambda e: self.audio_btn.config(bg="#157347"))
        self.audio_btn.bind(
            "<Leave>", lambda e: self.audio_btn.config(bg="#198754"))

        # Options Section
        self.options_frame = Frame(self.main_container)
        self.options_frame.pack(fill='x', pady=(0, 8))

        self.thumbnail_check = Checkbutton(self.options_frame,
                                           text="🖼️ Embed thumbnails in audio",
                                           variable=self.embed_thumbnails,
                                           command=self.save_thumbnail_setting,
                                           font=("Segoe UI", 9))
        self.thumbnail_check.pack(side='left')

        # Modern Progress Section
        self.progress_frame = Frame(self.main_container)
        self.progress_frame.pack(fill='x', pady=(0, 12))

        self.progress_bar = ttk.Progressbar(self.progress_frame,
                                            variable=self.progress_var,
                                            maximum=100,
                                            mode='determinate',
                                            style="Modern.Horizontal.TProgressbar")
        self.progress_bar.pack(fill='x', pady=(0, 8))

        # Modern Status Display
        self.status_label = Label(self.main_container, textvariable=self.status_var,
                                  relief="flat", anchor="w",
                                  font=("Segoe UI", 10), padx=15, pady=10)
        self.status_label.pack(fill='x')

        # Bottom controls
        self.controls_frame = Frame(self.main_container)
        self.controls_frame.pack(fill='x', pady=(8, 0))

        self.console_check = Checkbutton(self.controls_frame, text="Console",
                                         variable=self.show_console,
                                         command=self.toggle_console,
                                         font=("Segoe UI", 8))
        self.console_check.pack(side='left')

        self.dark_mode_check = Checkbutton(self.controls_frame, text="🌙 Dark",
                                           variable=self.dark_mode,
                                           command=self.toggle_dark_mode,
                                           font=("Segoe UI", 8))
        self.dark_mode_check.pack(side='left', padx=(10, 0))

        self.preview_btn = Button(self.controls_frame, text="📋 Preview Playlist",
                                  command=self.preview_playlist,
                                  fg="white",
                                  font=("Segoe UI", 8),
                                  relief="flat", cursor="hand2",
                                  padx=8, pady=3)
        self.preview_btn.pack(side='right', padx=(5, 0))

        self.update_btn = Button(self.controls_frame, text="Update",
                                 command=self.update_ytdlp,
                                 fg="white",
                                 font=("Segoe UI", 8),
                                 relief="flat", cursor="hand2",
                                 padx=8, pady=3)
        self.update_btn.pack(side='right', padx=(5, 0))

        self.format_btn = Button(self.controls_frame, text="Formats",
                                 command=self.check_formats,
                                 fg="white",
                                 font=("Segoe UI", 8),
                                 relief="flat", cursor="hand2",
                                 padx=8, pady=3)
        self.format_btn.pack(side='right', padx=(5, 0))

        self.clean_btn = Button(self.controls_frame, text="Clean",
                                command=self.cleanup_temp_files,
                                fg="white",
                                font=("Segoe UI", 8),
                                relief="flat", cursor="hand2",
                                padx=8, pady=3)
        self.clean_btn.pack(side='right')

    def save_thumbnail_setting(self):
        """Save thumbnail embedding preference"""
        self.settings["embed_thumbnails"] = self.embed_thumbnails.get()
        self.save_settings()

    def create_console_section(self):
        """Create the modern console output section (hidden by default)"""
        self.console_frame = Frame(self.root)

        self.console_label = Label(self.console_frame, text="💻 Console Output",
                                   font=("Segoe UI", 11, "bold"))
        self.console_label.pack(anchor='w', pady=(5, 8))

        console_text_frame = Frame(self.console_frame)
        console_text_frame.pack(fill='both', expand=True, pady=(0, 8))

        self.console_text = Text(console_text_frame, height=12, state='disabled',
                                 wrap='word', font=("Consolas", 10),
                                 relief="flat", bd=0, highlightthickness=2)
        scrollbar = Scrollbar(console_text_frame,
                              command=self.console_text.yview)
        self.console_text.config(yscrollcommand=scrollbar.set)

        self.console_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.clear_console_btn = Button(self.console_frame, text="Clear Console",
                                        command=self.clear_console,
                                        fg="white",
                                        font=("Segoe UI", 8),
                                        relief="flat", cursor="hand2",
                                        padx=10, pady=4)
        self.clear_console_btn.pack(anchor='e')

    def toggle_console(self):
        """Show or hide the console output section"""
        if self.show_console.get():
            self.console_frame.pack(
                fill='both', expand=True, padx=20, pady=(0, 15))
            self.root.geometry("700x770")
        else:
            self.console_frame.pack_forget()
            self.root.geometry("700x450")

    def log_to_console(self, text):
        """Add text to the console output"""
        self.console_text.config(state='normal')
        self.console_text.insert('end', text)
        self.console_text.see('end')
        self.console_text.config(state='disabled')
        self.root.update_idletasks()

    def clear_console(self):
        """Clear the console output"""
        self.console_text.config(state='normal')
        self.console_text.delete('1.0', 'end')
        self.console_text.config(state='disabled')

    def parse_progress(self, line):
        """Extract and update progress information from yt-dlp output"""
        # Check for playlist progress
        playlist_match = re.search(
            r'\[download\] Downloading item (\d+) of (\d+)', line)
        if playlist_match:
            current = playlist_match.group(1)
            total = playlist_match.group(2)
            self.status_var.set(
                f"Processing playlist: {current} of {total} videos")
            return

        if "[download]" in line and "%" in line:
            try:
                percent_match = re.search(r'(\d+\.?\d*)%', line)
                if percent_match:
                    percent = float(percent_match.group(1))
                    self.progress_var.set(percent)

                if "ETA" in line:
                    eta_match = re.search(r'ETA (\d+:\d+)', line)
                    speed_match = re.search(r'at ([\d.]+\w+/s)', line)
                    if eta_match and speed_match:
                        batch_info = ""
                        if self.batch_urls and len(self.batch_urls) > 1:
                            batch_info = f"[{self.current_batch_index + 1}/{len(self.batch_urls)}] "
                        self.status_var.set(
                            f"{batch_info}Downloading... {speed_match.group(1)} - ETA {eta_match.group(1)}")
            except:
                pass
        elif "Merging formats" in line:
            self.progress_var.set(90)
            self.status_var.set("Merging video and audio...")
        elif "Embedding thumbnail" in line:
            self.status_var.set("Embedding thumbnail...")

    def run_ytdlp_command(self, cmd):
        """Execute yt-dlp command with real-time output processing"""
        if not self.ytdlp_available:
            messagebox.showerror("yt-dlp Missing", "yt-dlp.exe not found!")
            return False

        try:
            self.log_to_console(f"Executing: {' '.join(cmd)}\n{'='*60}\n")

            process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True,
                                       universal_newlines=True, bufsize=1)

            while True:
                if process.stdout is None:
                    break
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    self.log_to_console(line + "\n")
                    self.parse_progress(line)

            return_code = process.poll()
            success = (return_code == 0)

            if success:
                self.progress_var.set(100.0)
            else:
                self.log_to_console(
                    f"Process exited with code: {return_code}\n")

            return success

        except Exception as e:
            error_msg = f"Error executing command: {e}"
            self.log_to_console(error_msg + "\n")
            self.status_var.set(f"Error: {e}")
            messagebox.showerror("Execution Error", error_msg)
            return False

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_patterns = ["*.f*.mp4", "*.f*.m4a", "*.f*.webm", "*.part"]
        cleaned_count = 0

        for pattern in temp_patterns:
            for temp_file in glob.glob(pattern):
                try:
                    os.remove(temp_file)
                    cleaned_count += 1
                    self.log_to_console(f"Cleaned: {temp_file}\n")
                except:
                    pass

        if cleaned_count > 0:
            messagebox.showinfo(
                "Cleanup", f"Cleaned {cleaned_count} temporary files")
        else:
            messagebox.showinfo("Cleanup", "No temporary files found")

    def check_formats(self):
        """Check available formats for the current URL"""
        url = self.url_entry.get().strip() if not self.batch_mode.get() else ""
        if not url:
            messagebox.showwarning(
                "Input Error", "Please enter a YouTube URL first (disable batch mode)")
            return

        if not self.show_console.get():
            self.show_console.set(True)
            self.toggle_console()

        self.clear_console()
        self.status_var.set("Checking available formats...")

        def check_thread():
            cmd = [self.YTDLP_PATH, "-F", url]

            try:
                self.log_to_console(f"Checking formats for: {url}\n")
                self.log_to_console("=" * 70 + "\n")

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    self.log_to_console("AVAILABLE FORMATS:\n")
                    self.log_to_console("=" * 70 + "\n")
                    self.log_to_console(result.stdout + "\n")

                    if result.stderr:
                        self.log_to_console("\nADDITIONAL INFO:\n")
                        self.log_to_console(result.stderr + "\n")

                    self.status_var.set("Format check completed!")
                else:
                    self.log_to_console("ERROR checking formats:\n")
                    self.log_to_console(result.stderr + "\n")
                    self.status_var.set("Format check failed!")

                self.progress_var.set(100.0)

            except subprocess.TimeoutExpired:
                self.log_to_console(
                    "Format check timed out after 30 seconds\n")
                self.status_var.set("Format check timed out!")
            except Exception as e:
                self.log_to_console(f"Error checking formats: {e}\n")
                self.status_var.set(f"Error: {e}")

        thread = threading.Thread(target=check_thread)
        thread.daemon = True
        thread.start()

    def update_ytdlp(self):
        """Update yt-dlp to the latest version"""
        self.status_var.set("Checking for updates...")

        def update_thread():
            try:
                # Get current version
                try:
                    current_version = subprocess.run([self.YTDLP_PATH, "--version"],
                                                     capture_output=True, text=True, timeout=10)
                    current = current_version.stdout.strip()
                except:
                    current = "Unknown"

                self.log_to_console(f"Current version: {current}\n")
                self.log_to_console("Checking for latest version...\n")

                # Get latest release info from GitHub
                api_url = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
                with urllib.request.urlopen(api_url, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    latest = data['tag_name']

                self.log_to_console(f"Latest version: {latest}\n")

                if current == latest:
                    self.status_var.set(f"Already up to date ({current})")
                    messagebox.showinfo(
                        "Up to Date", f"yt-dlp is already at the latest version ({current})")
                    return

                # Download latest version
                self.status_var.set(f"Updating from {current} to {latest}...")
                self.log_to_console("Downloading latest version...\n")

                download_url = f"https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
                temp_path = self.YTDLP_PATH + ".new"

                urllib.request.urlretrieve(download_url, temp_path)

                # Replace old version
                backup_path = self.YTDLP_PATH + ".old"
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.rename(self.YTDLP_PATH, backup_path)
                os.rename(temp_path, self.YTDLP_PATH)

                self.log_to_console("Update completed successfully!\n")
                self.status_var.set(f"Updated to {latest}")
                messagebox.showinfo("Update Complete",
                                    f"yt-dlp updated successfully!\n\n{current} → {latest}")

            except Exception as e:
                error_msg = f"Update failed: {e}"
                self.log_to_console(error_msg + "\n")
                self.status_var.set("Update failed")
                messagebox.showerror("Update Failed", error_msg)

        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()

    def preview_playlist(self):
        """Preview and select videos from a playlist"""
        url = self.url_entry.get().strip() if not self.batch_mode.get() else ""
        if not url:
            messagebox.showwarning(
                "Input Error", "Please enter a playlist URL (disable batch mode)")
            return

        # Check if it's likely a playlist URL
        if "list=" not in url:
            messagebox.showwarning("Not a Playlist",
                                   "This doesn't appear to be a playlist URL.\n"
                                   "Playlist URLs contain 'list=' parameter.")
            return

        self.status_var.set("Fetching playlist information...")
        self.progress_var.set(0)

        def fetch_playlist():
            try:
                # Fetch playlist metadata
                cmd = [self.YTDLP_PATH, "--flat-playlist", "--dump-json", url]

                self.log_to_console(f"Fetching playlist: {url}\n")

                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=60)

                if result.returncode != 0:
                    self.status_var.set("Failed to fetch playlist")
                    messagebox.showerror("Playlist Error",
                                         f"Failed to fetch playlist information:\n{result.stderr}")
                    return

                # Parse JSON lines
                videos = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            video_data = json.loads(line)
                            videos.append({
                                'id': video_data.get('id', ''),
                                'title': video_data.get('title', 'Unknown'),
                                'duration': video_data.get('duration', 0),
                                'url': video_data.get('url', ''),
                                'thumbnail': video_data.get('thumbnail', video_data.get('thumbnails', [{}])[-1].get('url', ''))
                            })
                        except json.JSONDecodeError:
                            continue

                if not videos:
                    self.status_var.set("No videos found in playlist")
                    messagebox.showwarning(
                        "Empty Playlist", "No videos found in this playlist")
                    return

                self.status_var.set(f"Found {len(videos)} videos")

                # Show playlist preview window
                self.root.after(
                    0, lambda: self.show_playlist_preview(videos, url))

            except subprocess.TimeoutExpired:
                self.status_var.set("Playlist fetch timed out")
                messagebox.showerror(
                    "Timeout", "Fetching playlist information timed out")
            except Exception as e:
                self.status_var.set("Error fetching playlist")
                messagebox.showerror("Error", f"Error fetching playlist: {e}")
                self.log_to_console(f"Playlist fetch error: {e}\n")

        thread = threading.Thread(target=fetch_playlist)
        thread.daemon = True
        thread.start()

    def show_playlist_preview(self, videos, playlist_url):
        """Show playlist preview window with video selection"""
        preview_window = Toplevel(self.root)
        preview_window.title(f"Playlist Preview - {len(videos)} videos")
        preview_window.geometry("900x600")

        colors = self.get_colors()
        preview_window.configure(bg=colors["bg"])

        # Header
        header_frame = Frame(preview_window, bg=colors["bg"])
        header_frame.pack(fill='x', padx=15, pady=10)

        Label(header_frame, text=f"📋 Playlist Preview ({len(videos)} videos)",
              font=("Segoe UI", 14, "bold"), bg=colors["bg"], fg=colors["fg"]).pack(side='left')

        # Configuration controls (videos per tab and sorting)
        config_frame = Frame(preview_window, bg=colors["bg"])
        config_frame.pack(fill='x', padx=15, pady=(0, 10))

        Label(config_frame, text="Videos per tab:", font=("Segoe UI", 9),
              bg=colors["bg"], fg=colors["fg"]).pack(side='left', padx=(0, 5))

        videos_per_tab_var = StringVar(value="100")
        videos_per_tab_combo = ttk.Combobox(config_frame, textvariable=videos_per_tab_var,
                                            values=["50", "100",
                                                    "150", "200", "All"],
                                            state="readonly", width=8)
        videos_per_tab_combo.pack(side='left', padx=(0, 15))

        Label(config_frame, text="Sort by:", font=("Segoe UI", 9),
              bg=colors["bg"], fg=colors["fg"]).pack(side='left', padx=(0, 5))

        sort_by_var = StringVar(value="Default")
        sort_by_combo = ttk.Combobox(config_frame, textvariable=sort_by_var,
                                     values=["Default", "Name (A-Z)", "Name (Z-A)",
                                             "Duration (Short-Long)", "Duration (Long-Short)"],
                                     state="readonly", width=20)
        sort_by_combo.pack(side='left', padx=(0, 10))

        # Selection controls
        controls_frame = Frame(preview_window, bg=colors["bg"])
        controls_frame.pack(fill='x', padx=15, pady=(0, 10))

        def select_all():
            for var in video_vars:
                var.set(True)

        def deselect_all():
            for var in video_vars:
                var.set(False)

        Button(controls_frame, text="✓ Select All", command=select_all,
               bg="#4CAF50", fg="white", font=("Segoe UI", 9),
               relief="flat", cursor="hand2", padx=10, pady=5).pack(side='left', padx=5)

        Button(controls_frame, text="✗ Deselect All", command=deselect_all,
               bg="#F44336", fg="white", font=("Segoe UI", 9),
               relief="flat", cursor="hand2", padx=10, pady=5).pack(side='left', padx=5)

        selected_count = StringVar()
        selected_count.set(f"{len(videos)} selected")
        Label(controls_frame, textvariable=selected_count,
              font=("Segoe UI", 9), bg=colors["bg"], fg=colors["secondary_fg"]).pack(side='right', padx=10)

        # Container for notebook (will be recreated when settings change)
        notebook_container = Frame(preview_window, bg=colors["bg"])
        notebook_container.pack(
            fill='both', expand=True, padx=15, pady=(0, 10))

        # Variables to store current state
        video_vars = []
        video_data_list = []
        current_notebook = None

        # Function to create/recreate the notebook with current settings
        def create_notebook():
            nonlocal video_vars, video_data_list, current_notebook

            # Destroy existing notebook if it exists
            if current_notebook:
                current_notebook.destroy()

            # Reset variables
            video_vars = []
            video_data_list = []

            # Get current settings
            per_tab_str = videos_per_tab_var.get()
            videos_per_tab = len(
                videos) if per_tab_str == "All" else int(per_tab_str)
            sort_by = sort_by_var.get()

            # Sort videos based on selection
            sorted_videos = videos.copy()
            if sort_by == "Name (A-Z)":
                sorted_videos.sort(key=lambda v: v['title'].lower())
            elif sort_by == "Name (Z-A)":
                sorted_videos.sort(
                    key=lambda v: v['title'].lower(), reverse=True)
            elif sort_by == "Duration (Short-Long)":
                sorted_videos.sort(key=lambda v: v['duration'] or 0)
            elif sort_by == "Duration (Long-Short)":
                sorted_videos.sort(
                    key=lambda v: v['duration'] or 0, reverse=True)

            # Create new notebook
            current_notebook = ttk.Notebook(notebook_container)
            current_notebook.pack(fill='both', expand=True)

            # Split videos into tabs
            for tab_index in range(0, len(sorted_videos), videos_per_tab):
                tab_videos = sorted_videos[tab_index:tab_index +
                                           videos_per_tab]

                # Create tab
                tab_frame = Frame(current_notebook, bg=colors["bg"])
                current_notebook.add(
                    tab_frame, text=f"Videos {tab_index + 1}-{min(tab_index + videos_per_tab, len(sorted_videos))}")

                # Canvas and scrollbar for tab
                canvas = Canvas(
                    tab_frame, bg=colors["bg"], highlightthickness=0)
                scrollbar = Scrollbar(
                    tab_frame, orient="vertical", command=canvas.yview)
                scrollable_frame = Frame(canvas, bg=colors["bg"])

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
                )

                canvas.create_window(
                    (0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                # Create mousewheel handler for this canvas
                def _on_mousewheel(event, canvas_ref=canvas):
                    canvas_ref.yview_scroll(int(-1*(event.delta/120)), "units")

                # Helper to bind mousewheel to a widget
                def _bind_mousewheel(widget):
                    widget.bind("<MouseWheel>", _on_mousewheel)

                # Bind mousewheel to canvas and scrollable frame
                _bind_mousewheel(canvas)
                _bind_mousewheel(scrollable_frame)
                _bind_mousewheel(tab_frame)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                # Add videos to this tab
                for idx, video in enumerate(tab_videos):
                    video_frame = Frame(
                        scrollable_frame, bg=colors["entry_bg"], relief="solid", bd=1)
                    video_frame.pack(fill='x', padx=5, pady=3)
                    _bind_mousewheel(video_frame)  # Bind to each video frame

                    var = BooleanVar(value=True)
                    video_vars.append(var)
                    video_data_list.append(video)

                    def update_count(*args):
                        count = sum(1 for v in video_vars if v.get())
                        selected_count.set(f"{count} selected")

                    var.trace_add("write", update_count)

                    # Checkbox
                    cb = Checkbutton(video_frame, variable=var, bg=colors["entry_bg"],
                                     activebackground=colors["entry_bg"], selectcolor=colors["entry_bg"])
                    cb.pack(side='left', padx=5)
                    _bind_mousewheel(cb)

                    # Thumbnail placeholder (will load async) - much larger, no fixed size
                    thumb_label = Label(video_frame, text="⏳", bg=colors["entry_bg"],
                                        font=("Segoe UI", 48), relief="sunken")
                    thumb_label.pack(side='left', padx=8, pady=5)
                    _bind_mousewheel(thumb_label)

                    # Video info
                    info_frame = Frame(video_frame, bg=colors["entry_bg"])
                    info_frame.pack(side='left', fill='x',
                                    expand=True, padx=5, pady=5)
                    _bind_mousewheel(info_frame)

                    duration_str = f"{int(video['duration'] // 60)}:{int(video['duration'] % 60):02d}" if video['duration'] else "?"

                    title_text = video['title'][:80] + \
                        "..." if len(video['title']) > 80 else video['title']
                    title_label = Label(info_frame, text=title_text, font=("Segoe UI", 9, "bold"),
                                        bg=colors["entry_bg"], fg=colors["fg"], anchor='w')
                    title_label.pack(fill='x')
                    _bind_mousewheel(title_label)

                    duration_label = Label(info_frame, text=f"⏱️ {duration_str}", font=("Segoe UI", 8),
                                           bg=colors["entry_bg"], fg=colors["secondary_fg"], anchor='w')
                    duration_label.pack(fill='x')
                    _bind_mousewheel(duration_label)

                    # Load thumbnail async
                    if PIL_AVAILABLE and video['thumbnail']:
                        def load_thumb(url, label):
                            try:
                                with urllib.request.urlopen(url, timeout=5) as response:
                                    img_data = response.read()
                                    img = Image.open(           # type: ignore
                                        BytesIO(img_data))  # type:ignore
                                    # Much larger thumbnail to fill the box
                                    img.thumbnail((320, 180))
                                    photo = ImageTk.PhotoImage(         # type: ignore
                                        img)  # type:ignore
                                    label.configure(
                                        image=photo, text="", font=("Segoe UI", 9))
                                    label.image = photo  # Keep reference
                            except:
                                label.configure(
                                    text="❌", font=("Segoe UI", 48))

                        threading.Thread(target=load_thumb, args=(
                            video['thumbnail'], thumb_label), daemon=True).start()
                    else:
                        thumb_label.configure(text="📹")

        # Bind combo boxes to recreate notebook when settings change
        def on_settings_change(event=None):
            create_notebook()

        videos_per_tab_combo.bind("<<ComboboxSelected>>", on_settings_change)
        sort_by_combo.bind("<<ComboboxSelected>>", on_settings_change)

        # Create initial notebook
        create_notebook()

        # Download buttons
        button_frame = Frame(preview_window, bg=colors["bg"])
        button_frame.pack(fill='x', padx=15, pady=(0, 15))

        def download_selected_video():
            selected_videos = [video_data_list[i]
                               for i, var in enumerate(video_vars) if var.get()]
            if not selected_videos:
                messagebox.showwarning(
                    "No Selection", "Please select at least one video")
                return
            preview_window.destroy()
            self.download_selected_videos(selected_videos, is_audio=False)

        def download_selected_audio():
            selected_videos = [video_data_list[i]
                               for i, var in enumerate(video_vars) if var.get()]
            if not selected_videos:
                messagebox.showwarning(
                    "No Selection", "Please select at least one video")
                return
            preview_window.destroy()
            self.download_selected_videos(selected_videos, is_audio=True)

        Button(button_frame, text="📹 Download Selected as Video",
               command=download_selected_video,
               bg="#2196F3", fg="white", font=("Segoe UI", 11, "bold"),
               relief="flat", cursor="hand2", padx=20, pady=10).pack(side='left', expand=True, fill='x', padx=5)

        Button(button_frame, text="🎵 Download Selected as Audio",
               command=download_selected_audio,
               bg="#4CAF50", fg="white", font=("Segoe UI", 11, "bold"),
               relief="flat", cursor="hand2", padx=20, pady=10).pack(side='left', expand=True, fill='x', padx=5)

    def download_selected_videos(self, videos, is_audio=False):
        """Download selected videos from playlist"""
        urls = [f"https://youtube.com/watch?v={v['id']}" for v in videos]
        self.batch_urls = urls

        if is_audio:
            self.status_var.set(f"Downloading {len(urls)} audio files...")
            self.process_download_batch(urls, is_audio=True)
        else:
            self.status_var.set(f"Downloading {len(urls)} videos...")
            self.process_download_batch(urls, is_audio=False)

    def process_download_batch(self, urls, is_audio=False):
        """Process batch download for selected videos"""
        self.video_btn.config(state="disabled")
        self.audio_btn.config(state="disabled")

        def download_thread():
            try:
                if is_audio:
                    self.process_batch_download(
                        urls, self.download_single_audio_direct)
                else:
                    self.process_batch_download(
                        urls, self.download_single_video_direct)
                self.cleanup_temp_files()
            except Exception as e:
                self.log_to_console(f"Batch download error: {e}\n")
                messagebox.showerror("Error", f"Batch download failed: {e}")
            finally:
                self.video_btn.config(state="normal")
                self.audio_btn.config(state="normal")

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    def download_single_video_direct(self, url):
        """Download a single video (for batch processing)"""
        try:
            cmd = [
                self.YTDLP_PATH,
                "-o", "%(title)s.%(ext)s",
                "--ffmpeg-location", self.FFMPEG_PATH,
                "-f", "bestvideo+bestaudio/best",
                "--merge-output-format", "mp4",
                url
            ]
            return self.run_ytdlp_command(cmd)
        except Exception as e:
            self.log_to_console(f"Error: {e}\n")
            return False

    def download_single_audio_direct(self, url):
        """Download audio from a single URL (for batch processing)"""
        try:
            cmd = [
                self.YTDLP_PATH,
                "-o", "%(title)s.%(ext)s",
                "--ffmpeg-location", self.FFMPEG_PATH,
                "-f", "bestaudio",
                "--extract-audio",
                "--audio-format", "m4a",
            ]
            if self.embed_thumbnails.get():
                cmd.extend(["--embed-thumbnail"])
            cmd.append(url)
            return self.run_ytdlp_command(cmd)
        except Exception as e:
            self.log_to_console(f"Error: {e}\n")
            return False

    def get_urls(self):
        """Get URLs based on current mode (single or batch)"""
        if self.batch_mode.get():
            # Get all lines from batch text area
            text_content = self.batch_text.get("1.0", "end-1c")
            urls = [line.strip()
                    for line in text_content.split('\n') if line.strip()]
            return urls
        else:
            # Get single URL from entry
            url = self.url_entry.get().strip()
            return [url] if url else []

    def process_batch_download(self, urls, download_func):
        """Process multiple URLs sequentially"""
        self.batch_urls = urls
        total = len(urls)

        for index, url in enumerate(urls):
            self.current_batch_index = index
            self.status_var.set(f"Processing {index + 1} of {total}...")
            self.progress_var.set(0.0)

            success = download_func(url)

            if not success:
                response = messagebox.askyesno("Download Failed",
                                               f"Failed to download:\n{url}\n\n"
                                               f"Continue with remaining {total - index - 1} URLs?")
                if not response:
                    break

        # Reset batch state
        self.batch_urls = []
        self.current_batch_index = 0
        self.status_var.set(f"Batch complete! Processed {total} URLs")
        messagebox.showinfo(
            "Batch Complete", f"Finished processing {total} URLs")

    def download_video(self):
        """Download video with best quality (video + audio)"""
        urls = self.get_urls()
        if not urls:
            messagebox.showwarning(
                "Input Error", "Please enter at least one YouTube URL")
            return

        if not self.ytdlp_available:
            messagebox.showerror("Tool Missing", "yt-dlp is not available!")
            return

        self.progress_var.set(0.0)
        self.video_btn.config(state="disabled")
        self.audio_btn.config(state="disabled")

        def download_thread():
            try:
                if len(urls) == 1:
                    # Single URL
                    self.status_var.set("Starting video download...")
                    success = self.download_single_video_direct(urls[0])
                    if success:
                        messagebox.showinfo(
                            "Success", "Video downloaded successfully!")
                        self.cleanup_temp_files()
                    else:
                        messagebox.showerror(
                            "Failed", "Video download failed. Check console for details.")
                else:
                    # Batch mode
                    self.process_batch_download(
                        urls, self.download_single_video_direct)
                    self.cleanup_temp_files()

            except Exception as e:
                self.log_to_console(f"Unexpected error: {e}\n")
                messagebox.showerror(
                    "Error", f"An unexpected error occurred: {e}")
            finally:
                self.video_btn.config(state="normal")
                self.audio_btn.config(state="normal")

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    def download_audio(self):
        """Download audio only (best quality)"""
        urls = self.get_urls()
        if not urls:
            messagebox.showwarning(
                "Input Error", "Please enter at least one YouTube URL")
            return

        if not self.ytdlp_available:
            messagebox.showerror("Tool Missing", "yt-dlp is not available!")
            return

        self.progress_var.set(0.0)
        self.video_btn.config(state="disabled")
        self.audio_btn.config(state="disabled")

        def download_thread():
            try:
                if len(urls) == 1:
                    # Single URL
                    self.status_var.set("Starting audio download...")
                    success = self.download_single_audio_direct(urls[0])
                    if success:
                        messagebox.showinfo(
                            "Success", "Audio downloaded successfully!")
                        self.cleanup_temp_files()
                    else:
                        messagebox.showerror(
                            "Failed", "Audio download failed. Check console for details.")
                else:
                    # Batch mode
                    self.process_batch_download(
                        urls, self.download_single_audio_direct)
                    self.cleanup_temp_files()

            except Exception as e:
                self.log_to_console(f"Unexpected error: {e}\n")
                messagebox.showerror(
                    "Error", f"An unexpected error occurred: {e}")
            finally:
                self.video_btn.config(state="normal")
                self.audio_btn.config(state="normal")

        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()

    def run(self):
        """Start the application"""
        self.root.mainloop()


# Launch the application
if __name__ == "__main__":
    app = YouTubeDownloader()
    app.run()
