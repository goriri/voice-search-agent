import asyncio
import websockets
import json
import logging
import warnings
import os
from http import HTTPStatus
import http.server
import threading
import base64
from voice_search_agent import BedrockStreamManager

# Configure logging
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore")

DEBUG = False

def debug_print(message):
    """Print only if debug mode is enabled"""
    if DEBUG:
        print(message)

class WebServerHandler(http.server.SimpleHTTPRequestHandler):
    """Handler for serving static files and health check endpoint"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve static files from
        self.static_dir = os.path.join(os.path.dirname(__file__), 'static')
        super().__init__(*args, **kwargs)

    def do_GET(self):
        client_ip = self.client_address[0]
        logger.info(f"Request received from {client_ip} for path: {self.path}")

        if self.path == "/health":
            # Handle health check
            logger.info(f"Responding with 200 OK to health check from {client_ip}")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json.dumps({"status": "healthy"})
            self.wfile.write(response.encode("utf-8"))
            logger.info(f"Health check response sent: {response}")
        else:
            # Serve static files
            if self.path == "/":
                self.path = "/index.html"
            
            try:
                file_path = os.path.join(self.static_dir, self.path.lstrip('/'))
                with open(file_path, 'rb') as f:
                    self.send_response(HTTPStatus.OK)
                    if self.path.endswith('.html'):
                        self.send_header("Content-Type", "text/html")
                    elif self.path.endswith('.js'):
                        self.send_header("Content-Type", "application/javascript")
                    elif self.path.endswith('.css'):
                        self.send_header("Content-Type", "text/css")
                    self.end_headers()
                    self.wfile.write(f.read())
            except FileNotFoundError:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                self.wfile.write(b"File not found")

    def log_message(self, format, *args):
        # Override to use our logger instead
        pass

def start_web_server(host, port):
    """Start the HTTP server for static files."""
    try:
        # Create the server with a socket timeout to prevent hanging
        httpd = http.server.HTTPServer((host, port), WebServerHandler)
        httpd.timeout = 5  # 5 second timeout

        logger.info(f"Starting web server on {host}:{port}")

        # Run the server in a separate thread
        thread = threading.Thread(target=httpd.serve_forever)
        thread.daemon = True  # This ensures the thread will exit when the main program exits
        thread.start()

        logger.info(f"Web server started at http://{host}:{port}")
        logger.info(f"Web server thread is alive: {thread.is_alive()}")

    except Exception as e:
        logger.error(f"Failed to start web server: {e}", exc_info=True)

async def websocket_handler(websocket):
    """Handle WebSocket connections from the frontend."""
    stream_manager = None
    forward_task = None
    
    try:
        # Create a new stream manager for this connection
        stream_manager = BedrockStreamManager(model_id='amazon.nova-sonic-v1:0', region='us-east-1')
        
        # Initialize the Bedrock stream
        await stream_manager.initialize_stream()
        
        # Start a task to forward responses from Bedrock to the WebSocket
        forward_task = asyncio.create_task(forward_responses(websocket, stream_manager))

        async for message in websocket:
            try:
                data = json.loads(message)
                if 'type' in data:
                    if data['type'] == 'audio':
                        # Handle incoming audio data
                        audio_base64 = data['data']
                        audio_bytes = base64.b64decode(audio_base64)
                        stream_manager.add_audio_chunk(audio_bytes)
                    elif data['type'] == 'start':
                        # Start audio streaming session
                        await stream_manager.send_audio_content_start_event()
                    elif data['type'] == 'stop':
                        # End audio streaming session
                        await stream_manager.send_audio_content_end_event()
                        await stream_manager.send_prompt_end_event()
            except json.JSONDecodeError:
                logger.error("Invalid JSON received from WebSocket")
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}")
                if DEBUG:
                    import traceback
                    traceback.print_exc()
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    finally:
        # Clean up
        if stream_manager:
            await stream_manager.close()
        if forward_task:
            forward_task.cancel()
        if websocket:
            await websocket.close()

async def forward_responses(websocket, stream_manager):
    """Forward responses from Bedrock to the WebSocket."""
    try:
        while True:
            # Get next response from the output queue
            response = await stream_manager.output_queue.get()
            
            # Check if it's an audio response
            if 'event' in response and 'audioOutput' in response['event']:
                audio_content = response['event']['audioOutput']['content']
                # Send audio data to client
                await websocket.send(json.dumps({
                    'type': 'audio',
                    'data': audio_content  # Already base64 encoded
                }))
            elif 'event' in response and 'textOutput' in response['event']:
                # Send text response to client
                text_content = response['event']['textOutput']['content']
                await websocket.send(json.dumps({
                    'type': 'text',
                    'data': text_content
                }))
            
    except asyncio.CancelledError:
        # Task was cancelled
        pass
    except Exception as e:
        logger.error(f"Error forwarding responses: {e}")
        if DEBUG:
            import traceback
            traceback.print_exc()

async def main(host, port, http_port):
    """Main function to run the WebSocket server."""
    try:
        # Start HTTP server for static files
        start_web_server(host, http_port)

        # Start WebSocket server
        async with websockets.serve(websocket_handler, host, port):
            logger.info(f"WebSocket server started at ws://{host}:{port}")
            
            # Keep the server running forever
            await asyncio.Future()
    except Exception as ex:
        logger.error("Failed to start servers", exc_info=ex)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Voice Search WebSocket Server')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    DEBUG = args.debug

    host = str(os.getenv("HOST", "localhost"))
    ws_port = int(os.getenv("WS_PORT", "8081"))
    http_port = int(os.getenv("HTTP_PORT", "3000"))

    aws_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")

    if not aws_key_id or not aws_secret:
        logger.error("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are required.")
    else:
        try:
            asyncio.run(main(host, ws_port, http_port))
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()