import pyautogui
from datetime import datetime

# Define the file name with a timestamp
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
filename = f'screenshot_{timestamp}.png'

# Take the screenshot
screenshot = pyautogui.screenshot()

# Save the screenshot
screenshot.save(filename)

print(f'Screenshot saved as {filename}')
