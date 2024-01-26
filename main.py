from icrawler.builtin import BingImageCrawler
import moviepy.editor as mpy
from moviepy.editor import *
from moviepy.video.fx.all import crop
import os
from flask import Flask, request
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips
import shutil
from mutagen.mp3 import MP3
import base64
from PIL import Image
import pyrebase
import requests
import json
from elevenlabslib import *
import speech_recognition as sr
import pysrt
from pydub import AudioSegment

webhook_url = 'WEBHOOK HERE'

user = ElevenLabsUser("API_KEY")

config = {
    "apiKey": "",
    "authDomain": "",
    "projectId": "",
    "storageBucket": "",
    "messagingSenderId": "",
    "appId": "",
    "measurementId": "",
    "serviceAccount": "serviceAccount.json",
    "databaseURL": ""
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()

# logo = Image.open("aladin.png")
# logo = Image.open("aladin.png").convert("RGBA")
logo = Image.open("aladin.png").convert("RGBA")

logo_width = 350
logo_height = int(logo_width * logo.size[1] / logo.size[0])
logo = logo.resize((logo_width, logo_height))

result = Image.new("RGBA", logo.size, (0, 0, 0, 0))

position = (250, 150)
top_position = (0, 0)
logo_width = 150
logo_height = int(logo_width * logo.size[1] / logo.size[0])
# logo = logo.resize((logo_width, logo_height))
top_image = Image.open("bar.png")
twidth, theight = top_image.size

new_height = int(theight * 0.2)
top_image = top_image.resize((twidth, new_height))

app = Flask(__name__)
directory_path = './'
folders = []


def scale_image(image, output_width, output_height):
    width, height = image.size
    output_ratio = output_width / output_height
    input_ratio = width / height

    if input_ratio > output_ratio:
        # Crop the width
        crop_width = int(height * output_ratio)
        crop_height = height
        left = (width - crop_width) // 2
        top = 0
        right = left + crop_width
        bottom = crop_height
    else:
        # Crop the height
        crop_width = width
        crop_height = int(width / output_ratio)
        left = 0
        top = (height - crop_height) // 2
        right = crop_width
        bottom = top + crop_height

    cropped_image = image.crop((left, top, right, bottom))
    return cropped_image.resize((output_width, output_height))


def scale_video(video):
    width, height = video.size
    output_width = 1080
    output_height = 1920 // 2  # Top 50% of the screen
    scaled_video = video.fx(crop, x_center=width / 2, y_center=height / 2, width=output_width, height=output_height)
    return scaled_video


def combine_videos(video1, video2):
    output_width = 1080
    output_height = 1920

    empty_video = ColorClip(size=(output_width, output_height), color=(0, 0, 0))

    # Calculate the position of the clips in the output video
    video1_position = (0, 0)  # Top-left corner
    video2_position = (0, output_height // 2)  # Bottom-left corner

    # Scale the second video to fill the bottom half of the output
    video2 = video2.resize((output_width, output_height // 2))

    combined_video = CompositeVideoClip(
        [empty_video, video1.set_position(video1_position), video2.set_position(video2_position)])

    return combined_video


def calculate_total_folders():
    fold = []
    for folder_name in os.listdir(directory_path):
        folder_path = os.path.join(directory_path, folder_name)
        if folder_name == ".git":
            continue  # skip the .git folder
        if os.path.isdir(folder_path):
            fold.append(folder_name)
    return fold


def add_logos(_folders):
    for i, folder in enumerate(_folders):
        try:
            img_path = "./{}/000001.jpg".format(i)
            img = Image.open(img_path)
            scaled_image = scale_image(img, 1080, 1920 // 2)
            result = Image.new("RGBA", scaled_image.size, (0, 0, 0, 0))
            result.paste(logo, (300, 100), mask=logo)
            scaled_image.paste(result, (0, 0), result)

            # img.paste(logo, position)
            scaled_image.paste(top_image, top_position)

            hght, wdth = scaled_image.size
            bot_position = (0, scaled_image.height - top_image.height)
            scaled_image.paste(top_image, bot_position)
            scaled_image.save("./{}/000001.jpg".format(i))
        except Exception as e:
            print(e)


def resize_images(_folders):
    # cc = calculate_total_folders()

    for i, folder in enumerate(_folders):
        try:
            img_path = "./{}/000001.jpg".format(i)
            img = Image.open(img_path)
            output_width = 1080
            output_height = 1920
            output_ratio = output_width / output_height
            width, height = img.size
            input_ratio = width / height
            if input_ratio > output_ratio:
                # Crop the width
                crop_width = int(height * output_ratio)
                crop_height = height
                left = (width - crop_width) // 2
                top = 0
                right = left + crop_width
                bottom = crop_height
            else:
                # Crop the height
                crop_width = width
                crop_height = int(width / output_ratio)
                left = 0
                top = (height - crop_height) // 2
                right = crop_width
                bottom = top + crop_height

            cropped_image = img.crop((left, top, right, bottom))

            # Resize the image to the output size
            resized_image = cropped_image.resize((output_width, output_height))

            resized_image.save("./{}/000001.jpg".format(i))
        except Exception as e:
            print(e)


def clean_folders():
    for folder_name in os.listdir(directory_path):
        folder_path = os.path.join(directory_path, folder_name)
        if os.path.isdir(folder_path) and folder_name != '.git':
            print("Deleting folder and all its contents")
            shutil.rmtree(folder_path)
    return True


def make_reel(kws, name, aud):
    folders = []
    print("Fetching Images")
    x = 0
    for i in kws:
        google_crawler = BingImageCrawler(storage={'root_dir': str(x)})
        google_crawler.crawl(keyword=i, max_num=1, min_size=(500, 500))
        x += 1
    folders = calculate_total_folders()

    resize_images(folders)
    add_logos(folders)

    print("Total Found Images: " + str(len(folders)))
    img = []
    for i, folder in enumerate(folders):
        img_path = "./{}/000001.jpg".format(i)
        img.append(img_path)
    print(img)
    file_path = aud

    # Calculate the duration of each image clip
    audio = AudioFileClip(file_path)
    clip_duration = audio.duration / len(img)

    # Create the image clips
    clips = [ImageClip(m).set_duration(clip_duration if i != (len(img) - 1) else audio.duration - clip_duration * i)
             for i, m in enumerate(img)]

    # Scale the input video (Video 1) to take up 50% of the space
    video1 = concatenate_videoclips(clips, method="compose")
    video1_scaled = scale_video(video1)

    # Read the provided video (reel.mp4) and scale it to take up the remaining 50% of the space
    video2 = VideoFileClip("reel.mp4")
    video2_scaled = scale_video(video2)

    # Combine both scaled videos into a single output video
    combined_video = combine_videos(video1_scaled, video2_scaled)

    # Set the duration of each clip
    for clip in clips:
        clip.duration = clip_duration

    # Convert audio to AAC format with a lower bitrate
    audio.write_audiofile("output.aac", codec="aac", bitrate="128k")

    # Re-import the converted audio
    audio = AudioFileClip("output.aac")
    # Set the duration of the audio clip
    combined_video.duration = audio.duration

    # Add the audio to the combined video
    combined_video.audio = audio

    (w, h) = combined_video.size
    print(combined_video.duration)
    # Write the video using H.264 codec and AAC audio codec
    combined_video.write_videofile(name + ".mp4", fps=24, codec="libx264", audio_codec="aac")

    storage.child(name + ".mp4").put(name + ".mp4")
    url = storage.child(name + ".mp4").get_url(None)
    data = {
        'content': url
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(webhook_url, data=json.dumps(data), headers=headers)

    print(response.status_code)
    print(url)

    return True


def create_video(text, voice):
    voice = user.get_voices_by_name(voice)[0]
    audio = voice.generate_audio_bytes(text)

    with open("output.mp3", "wb") as f:
        f.write(audio)


@app.route('/')
def hello():
    return "Reels API!"


@app.route('/api/upload', methods=['POST'])
def upload():
    # audio_data = request.json['audio'] # assuming the audio data is in a JSON object with key 'audio'

    # audio_binary = base64.b64decode(audio_data)
    # with open('audio.wav', 'wb') as f:
    #     f.write(audio_binary)
    # return 'Audio saved successfully'
    file = request.files['file']
    filename = file.filename
    file.save(filename)
    return 'File saved successfully'


@app.route('/api/reel', methods=['POST'])
def handle_post_request():
    folders = []
    data = request.json
    print("Removing Directories")
    try:
        clean_folders()
    except Exception as e:
        print("An error occurred")
    create_video(data["text"], data["voice"])
    make_reel(data["keywords"], data["name"], data["audio"])
    print(data)
    return "Success!"


if __name__ == '__main__':
    # print(fold)
    # resize_images()
    app.run()
