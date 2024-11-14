from datetime import datetime
from uuid import uuid4
from app.models import department
from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.prompts import ChatPromptTemplate
from langchain_core.documents import Document as LangchainDocument
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from sqlalchemy.orm import Session
from app.models.department import Department
from app.core.config import get_settings
import logging
import json

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self, db: Session):
        settings = get_settings()
        self.db = db
        self.collection_name = "document_store"
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vectorstore = PGVector(
            collection_name=self.collection_name,
            connection=settings.DATABASE_URL,
            embeddings=self.embeddings
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        
        # Initialize JSON parser
        self.json_parser = JsonOutputParser()

    async def _create_chain(self, prompt_template):
        logger.debug("Creating LLM chain with prompt template.")
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = (
            prompt 
            | self.llm 
            | self.json_parser
        )
        return chain

    async def process_document(self, content: str):
        try:
            logger.info("Starting document processing.")
            
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            logger.debug(f"Document split into {len(chunks)} chunks.")
            
            # Create documents with metadata
            docs = [
                LangchainDocument(
                    page_content=chunk,
                    metadata={
                        "id": str(uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                ) for i, chunk in enumerate(chunks)
            ]
            logger.info(f"{len(docs)} documents created with metadata for vector storage.")
            
            # Store in vector database
            self.vectorstore.add_documents(docs)
            logger.info("Documents added to vector database.")
            
            # Analyze each chunk
            analyses = []
            for i, doc in enumerate(docs):
                logger.debug(f"Analyzing chunk {i + 1}/{len(docs)}.")
                analysis = await self._analyze_chunk(doc.page_content)
                analyses.append(analysis)
            
            # Process results
            combined_analysis = await self._combine_analyses(analyses)
            departments = self.fetch_departments()
            
            print(departments)
            logger.info("Fetched departments from the database.")
            
            chain = await self._create_chain("""
				Given these departments and the document analysis, find the most relevant department.
				
				Each department object has the following fields:
					- id
					- code
					- name
					- description
				
				Departments:
				{departments}
				
				Document Analysis:
				{analysis}
				
				Use the departments' code, name, and description to determine the best match.
                SELECTION OF DEPARTMENT IS MANDATORY
				
				Provide the response in JSON format:
					"matched_department_id": "id of best matching department",
					"matched_department_code": "code of best matching department",
					"matched_department_name": "name of best matching department",
					"reasoning": "explanation for the match"
			""")
            department_match = await chain.ainvoke({"departments": departments, "analysis": combined_analysis})
            logger.info("Analysis of all chunks combined successfully.")
            
            # Find similar documents
            similar_docs = self.vectorstore.similarity_search_with_score(
                content, 
                k=3,
                filter={"id": {"$nin": [doc.metadata["id"] for doc in docs]}}
            )
            logger.info(f"Found {len(similar_docs)} similar documents.")

            return {
                "document_ids": [doc.metadata["id"] for doc in docs],
                "mathced_department": department_match,
                "analysis": combined_analysis,                
                "similar_documents": [
                    {
                        "id": doc.metadata["id"],
                        "content": doc.page_content[:200],
                        "score": float(score),  # Convert to float for JSON serialization
                        "metadata": {
                            k: v for k, v in doc.metadata.items() 
                            if k != "embedding"
                        }
                    } for doc, score in similar_docs
                ]
            }

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}", exc_info=True)
            raise

    async def _analyze_chunk(self, text: str):
        logger.debug("Starting analysis of document chunk.")
        chain = await self._create_chain("""
            Analyze this document section and provide a structured analysis.
            
            Document section: {input}
            
            Provide the response in the following JSON format:
            
                "topics": [list of main topics],
                "requirements": [list of key requirements],
                "type": "document type",
                "actions": [list of action items]
            
        """)
        
        result = await chain.ainvoke(text)
        logger.debug("Chunk analysis completed.")
        return result

    async def _combine_analyses(self, analyses):
        logger.debug("Combining analyses of all document chunks.")
        chain = await self._create_chain("""
            Combine these document analyses into one comprehensive summary:
            {input}
            
            Provide the response in the following JSON format:
            
                "main_topics": [list of consolidated topics],
                "key_requirements": [list of all requirements],
                "document_type": "overall document type",
                "action_items": [list of all action items],
                "summary": "comprehensive summary"
            
        """)
        
        result = await chain.ainvoke(json.dumps(analyses, indent=2))
        logger.debug("Combined analysis completed.")
        return result

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.vectorstore.aclose()
            logger.info("Vector store connection closed.")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        
    def fetch_departments(self):
        """Fetch and print department details from the database."""
        try:
            departments = self.db.query(Department).all()
            if departments:
                    formatted_departments = [
						{
							"id": department.id,
							"code": department.code,
							"name": department.name,
							"description": department.description
						} for department in departments
					]
                    logger.info("Departments fetched successfully.")
                    return formatted_departments
            else:
                logger.warning("No departments found in the database.")
        except Exception as e:
            logger.error(f"Failed to fetch departments: {str(e)}", exc_info=True)
