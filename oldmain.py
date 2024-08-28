import scratchattach as scratch3
from getpass import getpass
import requests
import random
import time
import string
import threading
from datetime import datetime
import os

# Initialize global variables
trials = {}
followed_users = {}
bypass_users = {"LifeCoderBoy", "gsumm719"}
recent_events = {}

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
    
    # Create a unique key for each event based on user and message
    event_key = (event.user, scratch3.Encoding.decode(event.value))

    # Check if this event has been processed recently
    if event_key in recent_events:
        print(f"Duplicate event detected for user {event.user}. Ignoring.")
        return  # Exit if the event is a duplicate
    
    # Record the event in the cache
    recent_events[event_key] = datetime.now()

    if event.var == "input":
        message = scratch3.Encoding.decode(event.value)

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
    for key, timestamp in list(recent_events.items()):
        if (current_time - timestamp).total_seconds() > 60:  # Adjust the time window as needed
            del recent_events[key]

def run_scheduler():
    while True:
        time.sleep(1)

# Start the scheduler in a separate thread
scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# Start handling Scratch events
events.start()
