import scratchattach as scratch3
from getpass import getpass
import requests
import random
import time
import string
import threading
from datetime import datetime
import os
from PIL import Image, ImageSequence
import requests
from io import BytesIO
import colorsys




# Initialize global variables
trials = {}
followed_users = {}
bypass_users = {"LifeCoderBoy", "gsumm719"}


def gen_7_digit():
    return ''.join(random.choice(string.digits) for _ in range(7))

# Retrieve secret password from environment variable
psw = os.getenv("SECRET")

# Initialize messages
msgs = [{"id": "rpxT3Os", "content": "You are Neuron, an assistant to talk with the group. You are NEURON, not SOME OTHER USER; DO NOT act like you are someone else, your role is the assistant. DO NOT make large responses.", "role": "user"}]

# Login and connect to Scratch
session = scratch3.login("LifeCoderBoy", psw)
conn = session.connect_cloud(1053091510)
events = scratch3.CloudEvents(1053091510)


def list_to_string(lst, num_digits=2):
    """Convert a list of numbers to a string with padded digits."""
    return ''.join(f"{int(round(num)):0{num_digits}d}" for num in lst)

def url_to_image(url):
    """Download an image from a URL and return it as a PIL Image object."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        return image
    except requests.RequestException as e:
        print(f"Error downloading image: {e}")
        return None
    except IOError as e:
        print(f"Error opening image: {e}")
        return None

def rgb_to_hsb(r, g, b):
    """Convert RGB values to HSB (Hue, Saturation, Brightness)."""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Convert hue to degrees [0, 360]
    h = h * 360
    
    # Convert saturation and brightness to percentage [0, 100]
    s = s * 100
    v = v * 100
    
    return h, s, v

def process_image(url, downsample_factor=4):
    """Process the image by downsampling and converting colors to HSB."""
    image = url_to_image(url)
    if image is None:
        return None, None, None

    # Check if the image is animated (GIF or APNG)
    if getattr(image, "is_animated", False):
        # For GIFs, ImageSequence.Iterator provides all frames
        frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
    else:
        # Check for APNG (APNGs can be identified via their frame count)
        frames = [image]
        try:
            # APNGs have more than one frame, but PIL doesn't always handle this well
            # so we use the frame count as a hint (Pillow >= 8.0.0)
            if image.n_frames > 1:
                frames = [Image.open(BytesIO(requests.get(url).content).convert('RGBA').getframe(i))
                          for i in range(image.n_frames)]
        except AttributeError:
            pass

    # Process only the last frame
    last_frame = frames[-1].convert('RGB')

    # Get original image dimensions
    width, height = last_frame.size
    
    # Calculate new dimensions for downsampling
    new_width = width // downsample_factor
    new_height = height // downsample_factor
    
    # Resize the image to reduce resolution
    last_frame = last_frame.resize((new_width, new_height), Image.LANCZOS)
    
    # Get new image dimensions
    width, height = last_frame.size

    # Initialize lists to store HSB values
    hue = []
    saturation = []
    brightness = []
    
    for y in range(height):
        for x in range(width):
            r, g, b = last_frame.getpixel((x, y))
            h, s, v = rgb_to_hsb(r, g, b)
            hue.append(h)
            saturation.append(s)
            brightness.append(v)
    
    # Convert lists to strings with padding for two digits
    hue_str = list_to_string(hue)
    saturation_str = list_to_string(saturation)
    brightness_str = list_to_string(brightness)
    
    return hue_str, saturation_str, brightness_str
    
def split_num(s):
    n = len(s)
    chunk_size = n // 7
    remaining_chars = n % 7
    chunks = []

    for i in range(7):  # Iterate from 0 to 6 to handle res1 to res7
        start = i * chunk_size
        end = start + chunk_size
        if i == 6:  # last chunk, add remaining chars
            end += remaining_chars
        chunk = s[start:end]
        chunks.append(chunk)
        conn.set_var(f"res{i + 1}", int(chunk))  # Set res1 to res7
    return chunks


def split_string(s):
    n = len(s)
    chunk_size = n // 8
    remaining_chars = n % 8
    chunks = []

    for i in range(8):
        start = i * chunk_size
        end = start + chunk_size
        if i == 7:  # last chunk, add remaining chars
            end += remaining_chars
        chunk = s[start:end]
        chunks.append(chunk)
        conn.set_var(f"res{i}", scratch3.Encoding.encode(chunk))
    return chunks

def post_to_blackbox(msgs):
    url = "https://www.blackbox.ai/api/chat"
    data = {"messages": msgs, "id": "rpxT3OX", "previewToken": "null", "userId": "ff285bac-c02e-43a2-9036-3965ed4e9119", "codeModelMode": True, "agentMode": {}, "trendingAgentMode": {}, "isMicMode": False, "isChromeExt": False, "githubToken": "null", "clickedAnswer2": False, "clickedAnswer3": False, "clickedForceWebSearch": False, "visitFromDelta": "null", "webSearchMode": False}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)

    # Retry if response contains "Sources:"
    if "Sources:" in response.text:
        response = requests.post(url, json=data, headers=headers)

    return response
    # global client
    # print(client)
    # chat_completion = client.chat.completions.create(
    #     model="gpt-4o-mini",
    #     messages=msgs,
    # )
    
    # return chat_completion.choices[0].message.content

def handle_response(response, prefix):
    response_text = response.text.split("$@$")[-1]
    if len(response_text) < 1020:
        print("Regular Response")
        conn.set_var("done", "0")
        split_string(f"Neuron{prefix}: {response_text}")
        conn.set_var("done", "1")
    else:
        print("Irregular Response")
        print("Response too long, splitting into chunks")
        conn.set_var("done", "0")
        split_string(f"Neuron{prefix}: {response_text[:len(response_text)//2]}")
        conn.set_var("done", "1")
        time.sleep(2)
        conn.set_var("done", "0")
        split_string(response_text[len(response_text)//2:])
        conn.set_var("done", "1")
    time.sleep(0.5)

@events.event
def on_set(event):
    user = scratch3.get_user(event.user)
    is_following = user.is_following("LifeCoderBoy")

    if event.var == "input":
        message = scratch3.Encoding.decode(event.value)
        if message.startswith("PFPRequest"):
            requester = scratch3.get_user(event.user)
            url = requester.icon_url
            h, s, b = process_image(url, downsample_factor=3)
            conn.set_var("res0", 523252)
            split_num(h[:1792])
            time.sleep(1)
            conn.set_var("done", "1")
            time.sleep(1)
            split_num(s[:1792])
            time.sleep(1)
            conn.set_var("done", "1")
            time.sleep(1)
            split_num(b[:1792])
            time.sleep(1)
            conn.set_var("done", "1")
            return
        
        conn.set_var("done", "0")
        split_string(f"{event.user}: {message}")
        time.sleep(1)
        conn.set_var("done", "1")
        
        msgs.append({"id": "rpxT3OX", "content": f"{event.user} says: {message}", "role": "user"})
        response = post_to_blackbox(msgs)
        print("Request from " + user.username)
        if user.username in bypass_users:
            print("Bypass: " + user.username)
            handle_response(response, " PRO")
            print("Done with " + user.username + "'s request")
        elif is_following:
            if user not in followed_users:
                followed_users[user] = 0

            if followed_users[user] < 15:
                followed_users[user] += 1
                handle_response(response, "")
            else:
                print(f"{event.user} reached message limit.")
                conn.set_var("done", "0")
                split_string(f"{event.user} has reached the limit for Neuron. You can use Neuron again when your limit resets tomorrow. Or, get Neuron PRO (See the instructions). Other people can continue to use Neuron")
                conn.set_var("done", "1")
                time.sleep(0.5)
        else:
            if event.user not in trials:
                trials[event.user] = 0

            if trials[event.user] < 1 or event.user == "LifeCoderBoy":
                print(f"{event.user} used a free trial.")
                trials[event.user] += 1
                handle_response(response, " (Free Trial)")
            else:
                print(f"{event.user} exceeded trial limit.")
                conn.set_var("done", "0")
                split_string(f"{event.user} has used their Neuron trial. Follow @LifeCoderBoy to send up to 15 messages/day (You'll automatically be able to use Neuron again when you've followed). Other people can continue to use Neuron")
                conn.set_var("done", "1")
                time.sleep(0.5)

    # Clean up old entries in the cache
    current_time = datetime.now()


def run_scheduler():
    while True:
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# Start handling Scratch events
events.start()
