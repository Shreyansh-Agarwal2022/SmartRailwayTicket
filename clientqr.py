import socket
import time
import cv2  # OpenCV for image processing
from pyzbar.pyzbar import decode  # To decode QR codes
import RPi.GPIO as GPIO         # Import Raspberry Pi GPIO library
from time import sleep          # Import the sleep function 

red = 16
green = 20
GPIO.setmode(GPIO.BCM)          # Use GPIO pin number
GPIO.setwarnings(False)         # Ignore warnings in our case
GPIO.setup(red, GPIO.OUT)       # red pin
GPIO.setup(green, GPIO.OUT)     # green pin

TRIG_PIN = 23  # GPIO pin for TRIG
ECHO_PIN = 24  # GPIO pin for ECHO

# Set up the pins
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

def measure_distance():
    # Ensure the TRIG pin is low
    GPIO.output(TRIG_PIN, False)
    time.sleep(0.5)  # Let the sensor settle
    
    # Trigger the sensor
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)  # TRIG high for 10 microseconds
    GPIO.output(TRIG_PIN, False)
    
    # Wait for ECHO to go high (start time)
    while GPIO.input(ECHO_PIN) == 0:
        pulse_start = time.time()
    
    # Wait for ECHO to go low (end time)
    while GPIO.input(ECHO_PIN) == 1:
        pulse_end = time.time()
    
    # Calculate the pulse duration
    pulse_duration = pulse_end - pulse_start
    
    # Convert pulse duration to distance in cm
    distance = pulse_duration * 17150  # Sound speed at 34300 cm/s, divided by 2
    distance = round(distance, 2)
    
    return distance

def read_qr_code_from_image(image_path):
    """
    Reads a QR code from the specified image file and returns the decoded data.
    """
    try:
        # Load the image
        image = cv2.imread(image_path)
        
        # Decode the QR code
        decoded_objects = decode(image)
        
        if decoded_objects:
            # Assume the first QR code found is the one we want
            qr_data = decoded_objects[0].data.decode('utf-8')
            print("QR Code data:", qr_data)
            return qr_data
        else:
            print("No QR code found in the image.")
            return None
    except Exception as e:
        print("An error occurred while reading the QR code:", e)
        return None

def send_data_to_server(server_ip, server_port=65432):
    """
    Connects to the server and sends data read from a QR code in an image.
    """
    while True:
        try:
            # Set up client socket and connect
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect((server_ip, server_port))
                print("Connected to server at", server_ip, "on port", server_port)

                while True:
                    # Ask for the QR code image path
                    image_path = input("Enter the path of the QR code image (or 'exit' to quit): ")
                    
                    if image_path.lower() == 'exit':
                        print("Exiting...")
                        return

                    # Read the QR code from the image
                    qr_data = read_qr_code_from_image(image_path)
                    
                    if qr_data is not None:
                        # Send QR data to the server
                        client_socket.sendall(qr_data.encode())
                        print("Sent to server:", qr_data)

                        # Receive server response
                        data = client_socket.recv(1024)
                        if not data:
                            print("Server closed the connection.")
                            break

                        output = data.decode()
                        print("Received from server (Ticket Response):", output)
                        if output == "True":
                            GPIO.output(green, GPIO.HIGH)   # Turn on
                            while True:
                                dist = measure_distance()
                                print(f"Distance: {dist} cm")
                                if dist < 8 or dist > 100:
                                    break
                                sleep(1)  # Wait 1 second before next measurement
                            sleep(1)
                            GPIO.output(green, GPIO.LOW)    # Turn off
                            print("Person Passed")
                        else:
                            GPIO.output(red, GPIO.HIGH)     # Turn on
                            sleep(3)
                            GPIO.output(red, GPIO.LOW)      # Turn off

                    else:
                        print("No QR code data to send.")
                        GPIO.output(red, GPIO.HIGH)     # Turn on
                        sleep(1)
                        GPIO.output(red, GPIO.LOW)      # Turn off

        except ConnectionRefusedError:
            print("Could not connect to server. Retrying in 5 seconds...")
            time.sleep(5)  # Wait before trying to reconnect
        except socket.gaierror:
            print("Invalid server IP address format.")
            break
        except Exception as e:
            print("An error occurred:", e)
            break

if __name__ == "__main__":
    SERVER_IP = input("Enter the server IP address: ")
    send_data_to_server(SERVER_IP)

