import cv2

# Open the webcam (0 is usually the default camera)
cap = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Capture a single frame
ret, frame = cap.read()

if ret:
    # Save the captured frame
    cv2.imwrite('captured_image.jpg', frame)
    print("Image captured and saved as 'captured_image.jpg'.")
else:
    print("Error: Could not capture image.")

# Release the camera
cap.release()

# Destroy any OpenCV windows
cv2.destroyAllWindows()
