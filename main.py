import scratchattach as scratch3
import random
import time
import string
import logging
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from g4f.client import Client

client = Client()

# Configure logging
logging.basicConfig(filename='neuron.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize global variables
trials = {}
followed_users = {}
bypass_users = {"LifeCoderBoy", "gsumm719"}

def gen_7_digit():
    return ''.join(random.choice(string.digits) for _ in range(7))

psw = os.getenv('SECRET')
msgs = [{"id":"rpxT3Os","content":"You are Neuron, an assistant to talk with the group. You are NEURON, not SOME OTHER USER; DO NOT act like you are someone else, your role is the assistant. DO NOT make large responses.", "role":"user"}]

# Setup synchronous environment
executor = ThreadPoolExecutor()

def run_in_executor(func, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(executor, func, *args)

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
        run_in_executor(conn.set_var, f"res{i}", scratch3.Encoding.encode(chunk))
    return chunks

def handle_response(response, prefix):
    response_text = response.split("$@$")[2] if "$@$" in response else response
    if len(response_text) < 1020:
        run_in_executor(conn.set_var, "done", "0")
        split_string(f"Neuron{prefix}: {response_text}")
        run_in_executor(conn.set_var, "done", "1")
    else:
        logging.info("Response too long, splitting into chunks")
        run_in_executor(conn.set_var, "done", "0")
        split_string(f"Neuron{prefix}: {response_text[:len(response_text)//2]}")
        run_in_executor(conn.set_var, "done", "1")
        time.sleep(2)
        run_in_executor(conn.set_var, "done", "0")
        split_string(response_text[len(response_text)//2:])
        run_in_executor(conn.set_var, "done", "1")
    time.sleep(0.5)

def reset_counts():
    global trials, followed_users
    trials = {}
    followed_users = {}
    logging.info("Message counts have been reset.")

def parse_command(command):
    parts = command.split()
    if len(parts) < 3:
        return "Invalid command format. Use /upgrade user <username> <bypass|neuron-followed> or /downgrade user <username> <neuron-unfollowed|neuron-followed>."

    action = parts[0]
    user = parts[2]
    status = parts[3]
    if action == "/reset":
        if parts[1] == "all":
            reset_counts()
            global msgs
            msgs = []
        elif parts[1] == "usage":
            reset_counts()
        elif parts[1] == "messages":
            msgs = []

    if action == "/upgrade" and status == "bypass":
        bypass_users.add(user)
        logging.info(f"User {user} added to bypass list.")
        return f"User {user} has been upgraded to bypass list."
    
    if action == "/downgrade":
        if status == "neuron-unfollowed":
            followed_users.pop(user, None)
            bypass_users.remove(user)
            logging.info(f"User {user} downgraded to neuron-unfollowed.")
            return f"User {user} has been downgraded to neuron-unfollowed."
        elif status == "neuron-followed":
            followed_users[user] = 0
            bypass_users.remove(user)
            logging.info(f"User {user} downgraded to neuron-followed.")
            return f"User {user} has been downgraded to neuron-followed."
    
    return "Invalid command or status."

async def post_to_blackbox(msgs):
    try:
        chat_completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=msgs,
        )
        print("----------SENDING!----------------")
        return chat_completion.choices[0].message.content or ""
    except Exception as e:
        logging.error(f"Failed to get response from blackbox: {e}")
        return "Error processing request."

async def on_set(event):
    user = scratch3.get_user(event.user)
    is_following = user.is_following("LifeCoderBoy")
    
    if event.var == "input":
        message = scratch3.Encoding.decode(event.value)
        
        if message.startswith("/"):
            response_message = parse_command(message)
            run_in_executor(conn.set_var, "done", "0")
            split_string(response_message)
            run_in_executor(conn.set_var, "done", "1")
            logging.info(f"Command executed: {message} - Response: {response_message}")
            return

        run_in_executor(conn.set_var, "done", "0")
        split_string(f"{event.user}: {message}")
        time.sleep(1)
        run_in_executor(conn.set_var, "done", "1")
        
        msgs.append({"id": "rpxT3OX", "content": f"{event.user} says: {message}", "role": "user"})
        print("----------OVER HERE----------------")
        response = await post_to_blackbox(msgs)
        print("----------CAME UP TILL HERE----------------")
        if user.username in bypass_users:
            logging.info(f"{event.user} bypassed the limit.")
            handle_response(response, " PRO")
        elif is_following:
            if user not in followed_users:
                followed_users[user] = 0

            if followed_users[user] < 15:
                followed_users[user] += 1
                handle_response(response, "")
            else:
                logging.info(f"{event.user} reached message limit.")
                run_in_executor(conn.set_var, "done", "0")
                split_string(f"{event.user} has reached the limit for Neuron. You can use Neuron again when your limit resets tomorrow. Or, get Neuron PRO (See the instructions). Other people can continue to use Neuron")
                run_in_executor(conn.set_var, "done", "1")
                time.sleep(0.5)
        else:
            if event.user not in trials:
                trials[event.user] = 0

            if trials[event.user] < 1 or event.user == "LifeCoderBoy":
                logging.info(f"{event.user} used a free trial.")
                trials[event.user] += 1
                handle_response(response, " (Free Trial)")
            else:
                logging.info(f"{event.user} exceeded trial limit.")
                run_in_executor(conn.set_var, "done", "0")
                split_string(f"{event.user} has used their Neuron trial. Follow @LifeCoderBoy to send up to 15 messages/day (You'll automatically be able to use Neuron again when you've followed). Other people can continue to use Neuron")
                run_in_executor(conn.set_var, "done", "1")
                time.sleep(0.5)

async def main():
    try:
        # Start handling Scratch events
        await events.start()
    except KeyboardInterrupt:
        logging.info("Event handling interrupted.")
    finally:
        logging.info("Stopping event handling...")
        await events.stop()
        logging.info("Event handling stopped.")

if __name__ == "__main__":
    asyncio.run(main())
