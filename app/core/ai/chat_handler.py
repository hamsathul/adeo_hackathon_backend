# app/core/ai/chat_handler.py
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from openai import api_key
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid
import logging


logger = logging.getLogger("chatbot.ai")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)

class ChatHandler:
    def __init__(self, db: AsyncSession):
        logger.debug("Initializing ChatHandler")
        self.db = db
        
        logger.debug("Setting up AI model...")
        self.model = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", 
            temperature=0.3, 
            top_k=40, 
            top_p=0.8
        )
        
        logger.debug("Creating prompt template...")
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are a helpful assistant for Abu Dhabi government services. "
                "Provide accurate and helpful information about government procedures, "
                "services, and general information about Abu Dhabi."
            ),
            MessagesPlaceholder(variable_name="messages")
        ])
        
        self.chain = self.prompt | self.model
        logger.debug("ChatHandler initialization complete")

    async def handle_message(self, message: str, user_id: str):
        """Handle incoming message and return response"""
        try:
            logger.info(f"Processing message from user {user_id}")
            logger.debug(f"Message content: {message}")
            
            # Create input message
            messages = [HumanMessage(content=message)]
            
            # Generate response
            logger.info("Requesting AI response...")
            response = await self.chain.ainvoke({"messages": messages})
            
            # Extract response content
            response_content = response.content if hasattr(response, 'content') else str(response)
            logger.info("AI response received")
            logger.debug(f"Response content: {response_content}")
            
            return {
                "id": str(uuid.uuid4()),
                "content": response_content,
                "timestamp": datetime.utcnow(),
                "is_bot": True
            }
            
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}", exc_info=True)
            error_message = f"I apologize, but I encountered an error: {str(e)}"
            return {
                "id": str(uuid.uuid4()),
                "content": error_message,
                "timestamp": datetime.utcnow(),
                "is_bot": True
            }