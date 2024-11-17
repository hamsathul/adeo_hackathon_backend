# tests/test_minimal.py
import asyncio
import socketio
import logging
from datetime import datetime, UTC
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("chatbot.test")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

# Disable other loggers
logging.getLogger('engineio').setLevel(logging.ERROR)
logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

class ChatTester:
    def __init__(self):
        self.sio = socketio.AsyncClient(logger=False)
        self.setup_event_handlers()
        self.responses_received = 0
        self.test_complete = asyncio.Event()
        self.connected = asyncio.Event()
        self.authenticated = asyncio.Event()

    def setup_event_handlers(self):
        @self.sio.event
        async def connect():
            logger.info("Connected to chat server")
            self.connected.set()

        @self.sio.event
        async def connect_error(data):
            logger.error(f"Connection error: {data}")
            self.test_complete.set()

        @self.sio.event
        async def disconnect():
            logger.info("Disconnected from chat server")
            self.connected.clear()
            self.authenticated.clear()

        @self.sio.event
        async def auth_response(data):
            if data.get('status') == 'authenticated':
                logger.info(f"Authentication successful for user {data.get('user_id')}")
                self.authenticated.set()
            else:
                logger.error(f"Authentication failed: {data}")
                self.test_complete.set()

        @self.sio.event
        async def message_received(data):
            logger.info(f"Message received: {json.dumps(data, indent=2)}")
            if data.get('type') == 'user_message':
                logger.info("User message acknowledged by server")
            elif data.get('type') == 'ai_message':
                logger.info("-" * 50)
                logger.info("AI Response received:")
                logger.info(f"Content: {data['message']['content']}")
                logger.info(f"Timestamp: {data['message']['timestamp']}")
                logger.info("-" * 50)
                self.responses_received += 1
                if self.responses_received >= self.expected_responses:
                    self.test_complete.set()

        @self.sio.event
        async def error(data):
            logger.error(f"Server error: {data.get('message', 'Unknown error')}")
            self.test_complete.set()

    async def authenticate(self, user_id: int = 1):
        """Authenticate with the server"""
        try:
            logger.info(f"Authenticating user {user_id}")
            await self.sio.emit('authenticate', {
                'user_id': user_id
            })
            # Wait for authentication response
            try:
                await asyncio.wait_for(self.authenticated.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.error("Authentication timeout")
                self.test_complete.set()
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            self.test_complete.set()

    async def send_test_message(self):
        """Send a test message to the chat server"""
        try:
            # Wait for connection before sending messages
            await self.connected.wait()
            
            # Authenticate first
            await self.authenticate(user_id=1)

            # Only proceed if authenticated
            if not self.authenticated.is_set():
                logger.error("Not authenticated, skipping messages")
                return

            test_messages = [
                "What can you tell me about Abu Dhabi?",
                "What services does the Abu Dhabi government provide?",
                "How can I renew my Emirates ID?"
            ]
            
            self.expected_responses = len(test_messages)
            
            for message in test_messages:
                if not self.connected.is_set():
                    logger.error("Connection lost, stopping messages")
                    break
                    
                logger.info(f"Sending test message: {message}")
                await self.sio.emit('chat_message', {
                    'content': message,
                    'user_id': 1,  # Use integer ID
                    'timestamp': datetime.now(UTC).isoformat()
                })
                # Add small delay between messages
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error sending test message: {str(e)}", exc_info=True)
            self.test_complete.set()

    async def run_test(self):
        """Run the chat test"""
        try:
            logger.info("Starting chat test")
            await self.sio.connect(
                'http://localhost:8000',
                transports=['websocket'],
                socketio_path='socket.io',
                wait_timeout=10
            )
            
            # Start sending messages
            await self.send_test_message()
            
            # Wait for test completion or timeout
            try:
                await asyncio.wait_for(self.test_complete.wait(), timeout=30)
            except asyncio.TimeoutError:
                logger.warning("Test timed out waiting for responses")
            
        except Exception as e:
            logger.error(f"Test error: {str(e)}", exc_info=True)
        finally:
            if self.sio.connected:
                await self.sio.disconnect()
            logger.info(f"Test completed. Received {self.responses_received} responses")

async def run_chat_tests():
    """Run multiple test scenarios"""
    test_scenarios = [
        ChatTester(),
    ]
    
    for scenario in test_scenarios:
        await scenario.run_test()
        await asyncio.sleep(2)

def main():
    """Main entry point for running tests"""
    try:
        asyncio.run(run_chat_tests())
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()