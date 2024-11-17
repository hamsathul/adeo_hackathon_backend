# tests/test_websocket.py
import asyncio
import socketio
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_chat():
    # Initialize client with specific Engine.IO version
    sio = socketio.AsyncClient(
        logger=True,
        engineio_logger=True,
        ssl_verify=False
    )
    
    @sio.event
    async def connect():
        logger.info("Connected!")
        await sio.emit('message', {'data': 'Hello server!'})
        
    @sio.event
    async def connect_error(error):
        logger.error(f"Connection error: {error}")
        
    @sio.event
    async def disconnect():
        logger.info("Disconnected!")
        
    @sio.on('response')
    async def on_response(data):
        logger.info(f"Received response: {data}")
        
    @sio.on('error')
    async def on_error(data):
        logger.error(f"Received error: {data}")

    url = 'http://localhost:8000'
    
    try:
        logger.info(f"Attempting to connect to {url}/ws")
        await sio.connect(
            f'{url}/ws',
            socketio_path='socket.io',
            transports=['websocket'],
            wait_timeout=10,
            auth=None,
            headers={
                'Accept': '*/*',
            },
            engineio_path='socket.io'
        )
        
        if sio.connected:
            logger.info("Successfully connected!")
            
            # Send test message
            await sio.emit('message', {'text': 'Test message'})
            
            # Wait for response
            await asyncio.sleep(3)
        else:
            logger.error("Failed to connect")
            
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
    finally:
        if sio.connected:
            await sio.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(test_chat())
    except KeyboardInterrupt:
        logger.info("Test stopped by user")
    except Exception as e:
        logger.error(f"Test failed: {e}")