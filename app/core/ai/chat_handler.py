# app/core/ai/chat_handler.py
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from openai import api_key
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import logging
import asyncio
from app.core.config import get_settings

settings=get_settings()

logger = logging.getLogger("chatbot.ai")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

class ChatHandler:
    def __init__(self, db: Session):
        logger.debug("Initializing ChatHandler")
        self.db = db
        
        logger.debug("Setting up AI model...")
        # self.model = ChatGoogleGenerativeAI(
        #     model="gemini-1.5-pro", 
        #     temperature=0.3, 
        #     top_k=40, 
        #     top_p=0.8,
        #     streaming=True
        # )
        # self.model = ChatOpenAI(
		# 	model="tiiuae/falcon-11b",
		# 	api_key=settings.AI71_API_KEY,
		# 	base_url=settings.AI71_BASE_URL,
		# 	streaming=True,
		# )
        self.model = ChatGroq(
			model="llama-3.1-70b-versatile",
			streaming=True,
		)
        
        logger.debug("Creating prompt template...")
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a helpful assistant for Abu Dhabi government executive office. your name is rashid.you will greet the user only once in the conversation. "
                " you will provide accurate and helpful information. your task is to assist the user in finding the information they need. "
                "be polite and professional in your responses."
            ),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.prompt | self.model
        logger.debug("ChatHandler initialization complete")

    async def handle_message_stream(self, message: str, user_id: str):
        """Handle incoming message and stream response"""
        try:
            logger.info(f"Processing message from user {user_id}")
            logger.debug(f"Message content: {message}")
            
            # Create input message
            messages = [HumanMessage(content=message)]
            
            # Generate streaming response
            logger.info("Starting AI response stream...")
            message_id = str(uuid.uuid4())
            timestamp = datetime.utcnow()
            
            async for chunk in self.chain.astream({"messages": messages}):
                chunk_content = chunk.content if hasattr(chunk, 'content') else str(chunk)
                yield {
                    "id": message_id,
                    "content": chunk_content,
                    "timestamp": timestamp,
                    "is_bot": True,
                    "is_complete": False
                }
            
            # Send completion message
            yield {
                "id": message_id,
                "content": "",
                "timestamp": timestamp,
                "is_bot": True,
                "is_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}", exc_info=True)
            error_message = f"I apologize, but I encountered an error: {str(e)}"
            yield {
                "id": str(uuid.uuid4()),
                "content": error_message,
                "timestamp": datetime.utcnow(),
                "is_bot": True,
                "is_complete": True
            }