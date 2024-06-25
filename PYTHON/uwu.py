import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import yt_dlp as youtube_dl
from googleapiclient.discovery import build
from pytube import YouTube
from pytube.exceptions import VideoUnavailable
import tkinter.font as tkFont

class YoutubeVideoExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Data Extractor")
        self.api_key = self.load_api_key()

        self.font = tkFont.Font(family="Helvetica", size=12)
        self.answer_font = tkFont.Font(family="Helvetica", size=16, weight="bold")

        self.create_widgets()
        self.show_widgets()

    def create_widgets(self):
        self.api_key_label = tk.Label(self.root, text="ENTER YOUR API KEY:", font=self.font)
        self.api_key_entry = tk.Entry(self.root, font=self.font)
        self.save_api_button = tk.Button(self.root, text="Save API", font=self.font, command=self.save_api_key)
        self.reset_api_button = tk.Button(self.root, text="Reset API", font=self.font, command=self.reset_api_key)

        self.url_label = tk.Label(self.root, text="ENTER YOUTUBE VIDEO URL:", font=self.font)
        self.url_entry = tk.Entry(self.root, font=self.font)
        self.submit_button = tk.Button(self.root, text="Download", font=self.font, command=self.start_process)

        self.highest_check_var = tk.BooleanVar()
        self.highest_check = tk.Checkbutton(self.root, text="Download highest resolution", font=self.font, variable=self.highest_check_var)

        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.step_label = tk.Label(self.root, text="", font=self.font)
        self.result_label = tk.Label(self.root, text="", font=self.font)

        self.quality_buttons_frame = tk.Frame(self.root)
        quality_options = {
            1: "240p",
            2: "360p",
            3: "480p",
            4: "720p",
            5: "1080p",
            6: "2k",
            7: "4k",
            8: "Audio"
        }

        self.quality_buttons = {}
        for option, text in quality_options.items():
            button = tk.Button(self.quality_buttons_frame, text=text, font=self.font, command=lambda o=option: self.set_quality_and_download(o))
            button.pack(side=tk.LEFT, padx=5)
            self.quality_buttons[option] = button

    def show_widgets(self):
        if not self.api_key:
            self.api_key_label.pack(pady=10)
            self.api_key_entry.pack(pady=5)
            self.save_api_button.pack(pady=5)
        else:
            self.url_label.pack(pady=10)
            self.url_entry.pack(pady=5)
            self.highest_check.pack(pady=5)
            self.submit_button.pack(pady=20)
            self.progress.pack(pady=20)
            self.step_label.pack(pady=10)
            self.result_label.pack(pady=10)
            self.quality_buttons_frame.pack(pady=10)

    def hide_widgets(self):
        self.api_key_label.pack_forget()
        self.api_key_entry.pack_forget()
        self.save_api_button.pack_forget()
        self.reset_api_button.pack_forget()
        self.url_label.pack_forget()
        self.url_entry.pack_forget()
        self.highest_check.pack_forget()
        self.submit_button.pack_forget()
        self.progress.pack_forget()
        self.step_label.pack_forget()
        self.result_label.pack_forget()
        self.quality_buttons_frame.pack_forget()

    def save_api_key(self):
        api_key = self.api_key_entry.get().strip()
        if api_key:
            with open('api.txt', 'w') as f:
                f.write(api_key)
            self.api_key = api_key
            self.api_key_entry.delete(0, tk.END)
            self.api_key_entry.pack_forget()
            self.save_api_button.pack_forget()
            self.reset_api_button.pack(pady=5)
            self.show_widgets()

    def reset_api_key(self):
        if os.path.exists('api.txt'):
            os.remove('api.txt')
        self.api_key = None
        self.hide_widgets()
        self.show_widgets()

    def load_api_key(self):
        if os.path.exists('api.txt'):
            with open('api.txt', 'r') as f:
                return f.read().strip()
        return None

    def start_process(self):
        api_key = self.api_key
        video_url = self.url_entry.get().strip()

        if not api_key:
            self.result_label.config(text="[ - ] PLEASE ENTER API KEY.")
            return
        if not video_url:
            self.result_label.config(text="[ - ] PLEASE ENTER YOUTUBE VIDEO URL.")
            return

        try:
            self.progress['maximum'] = 100
            self.result_label.config(text="")
            self.step_label.config(text="")
            self.progress['value'] = 0
            threading.Thread(target=self.text_animation).start()
            self.get_video_details(video_url, api_key)
        except ValueError:
            self.result_label.config(text="[ - ] PLEASE ENTER VALID INPUT.")

    def text_animation(self, for_audio=False):
        if for_audio:
            steps = [
                "PLEASE WAIT ...",
                "DOWNLOADING SONG ...",
                "EXTRACTING SONG DATA ...",
                "EXTRACTING CHANNEL DATA",
                "CALCULATING TIME",
                "SCANNING LOCATION",
                "SUCCESSFULLY EXTRACTED DATA.",
                "SUCCESSFULLY DOWNLOADED SONG/AUDIO"
            ]
        else:
            steps = [
                "PLEASE WAIT ...",
                "DOWNLOADING VIDEO ...",
                "EXTRACTING VIDEO DATA ...",
                "EXTRACTING CHANNEL DATA",
                "CALCULATING TIME",
                "SCANNING LOCATION",
                "SUCCESSFULLY EXTRACTED DATA.",
                "SUCCESSFULLY DOWNLOADED VIDEO",
                "CONVERTING PLEASE WAIT",
                "SAVING VIDEO"
            ]

        step_delay = 0.5
        fade_steps = 5
        progress_increment = 100 / len(steps)

        for i, step in enumerate(steps):
            for fade in range(fade_steps):
                alpha = fade / fade_steps
                fade_color = f'#{int(255 * (1 - alpha)):02x}{int(255 * (1 - alpha)):02x}{int(255 * (1 - alpha)):02x}'
                self.step_label.config(text=step, fg=fade_color)
                self.progress['value'] = int((i + (fade / fade_steps)) * progress_increment)
                self.root.update_idletasks()
                time.sleep(step_delay / fade_steps)
            time.sleep(step_delay)

    def get_video_details(self, video_url, api_key):
        video_id = video_url.split("v=")[-1]
        youtube = build('youtube', 'v3', developerKey=api_key)
        video_response = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        ).execute()

        if not video_response['items']:
            messagebox.showerror("Error", "Invalid video URL or video not found")
            return

        video_details = video_response['items'][0]['snippet']

        title = video_details.get('title', '[not found]')
        description = video_details.get('description', '[not found]')
        channel_id = video_details.get('channelId', '[not found]')
        uploaded_date = video_details.get('publishedAt', '[not found]')
        channel_response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()
        if not channel_response['items']:
            channel_url = '[not found]'
            channel_name = '[not found]'
            country = '[not found]'
        else:
            channel_details = channel_response['items'][0]['snippet']
            channel_url = f"https://www.youtube.com/channel/{channel_id}"
            channel_name = channel_details.get('title', '[not found]')
            country = channel_details.get('country', '[not found]') if 'country' in channel_details else '[not found]'

        with open('FILE.txt', 'w', encoding='utf-8') as f:
            f.write(f"TITLE: {title}\n")
            f.write(f"CHANNEL URL: {channel_url}\n")
            f.write(f"CHANNEL NAME: {channel_name}\n")
            f.write(f"COUNTRY: {country}\n")
            f.write(f"UPLOADED DATE: {uploaded_date}\n")
            f.write(f"VIDEO URL: {video_url}\n")
            f.write(f"DESCRIPTION:\n{description}\n")

        if self.highest_check_var.get():
            self.download_highest_quality(video_url)
        else:
            self.result_label.config(text="Video details extracted. Choose download quality.")

    def set_quality_and_download(self, choice):
        video_url = self.url_entry.get().strip()
        quality_options = {
            1: "worst[height<=240]",
            2: "worst[height<=360]",
            3: "worst[height<=480]",
            4: "best[height<=720]",
            5: "best[height<=1080]",
            6: "best[height<=1440]",
            7: "best[height<=2160]",
            8: "bestaudio"
        }
        quality = quality_options.get(choice)
        if not quality:
            self.result_label.config(text="Invalid choice!")
            return

        ydl_opts = {
            'format': quality,
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }

        is_audio = choice == 8
        threading.Thread(target=self.download_video, args=(video_url, ydl_opts, is_audio)).start()

    def download_highest_quality(self, video_url):
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        }
        threading.Thread(target=self.download_video, args=(video_url, ydl_opts)).start()

    def download_video(self, video_url, ydl_opts, is_audio=False):
        self.step_label.config(text="Downloading video..." if not is_audio else "Downloading audio...")
        try:
            threading.Thread(target=self.text_animation, args=(is_audio,)).start()
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            self.step_label.config(text="Download completed!")
            self.result_label.config(text="Download completed!")
        except Exception as e:
            self.step_label.config(text="Download failed!")
            self.result_label.config(text=str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeVideoExtractor(root)
    root.mainloop()
