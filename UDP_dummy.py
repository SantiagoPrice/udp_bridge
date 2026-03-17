import socket

# Configuration
HOST = "192.168.1.151"  # Target IP address
PORT = 5005         # Target port

# Binary message to send
message = b'\x01\x02\x03\x04\xFF\xFE\xFD\xFC'

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

try:
    # Send the binary message
    sent = sock.sendto(message, (HOST, PORT))
    print(f"Sent {sent} bytes to {HOST}:{PORT}")
    print(f"Message (hex): {message.hex()}")
finally:
    sock.close()