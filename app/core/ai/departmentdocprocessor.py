from crewai import Agent, Crew, Task, Process
from langchain_postgres import PGVector
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from langchain_core.output_parsers import JsonOutputParser
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
import logging
import json
from app.core.config import get_settings
from app.models.department import Department

logger = logging.getLogger(__name__)


def clean_json_output(output: str) -> str:
    """Clean JSON output by removing markdown and code block markers"""
    try:
        # Remove markdown code block markers and other common artifacts
        cleaned = output.replace("```json", "")
        cleaned = cleaned.replace("```jsonc", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()

        # Validate that it's proper JSON by parsing it
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON after cleaning: {cleaned}")


class DepartmentDocumentProcessor:
    """CrewAI-based document processing system"""

    def __init__(self, db: Session, content: str):
        """Initialize the crew with database session and document content"""
        self.db = db
        self.content = content
        settings = get_settings()

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro", temperature=0.3, top_k=40, top_p=0.8
        )

        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self.vectorstore = PGVector(
            collection_name="document_store",
            connection=settings.DATABASE_URL,
            embeddings=self.embeddings,
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, chunk_overlap=200
        )

        self.json_parser = JsonOutputParser()

    def fetch_departments(self):
        """Fetch departments from the database"""
        try:
            departments = self.db.query(Department).all()
            logger.info(f"Found {len(departments)} departments")

            if departments:
                formatted_departments = [
                    {
                        "id": department.id,
                        "code": department.code,
                        "name": department.name,
                        "description": department.description,
                    }
                    for department in departments
                ]
                return formatted_departments
            else:
                logger.warning("No departments found in database")
                return []

        except Exception as e:
            logger.error(f"Failed to fetch departments: {str(e)}", exc_info=True)
            raise ValueError(f"Error fetching departments: {str(e)}")

    def create_document_processor(self) -> Agent:
        """Create document processing agent"""
        return Agent(
            role="Document Analysis Specialist",
            goal="Analyze and classify document content while maintaining context",
            backstory="""Expert in document analysis with strong understanding of various document types 
            and structures. Specializes in extracting key information and classifying content.""",
            tools=[],
            verbose=True,
            llm=self.llm,
        )

    def create_content_analyzer(self) -> Agent:
        """Create content analysis agent"""
        return Agent(
            role="Content Analysis Expert",
            goal="Analyze document content and extract key information",
            backstory="""Experienced analyst skilled in identifying topics, requirements, 
            relationships, and key points across various document types.""",
            tools=[],
            verbose=True,
            llm=self.llm,
        )

    def create_department_matcher(self) -> Agent:
        """Create department matching agent"""
        return Agent(
            role="Department Alignment Specialist",
            goal="Match document content with relevant departments based on subject matter",
            backstory="""Expert in organizational structure and department functions. 
            Skilled at analyzing content and identifying departmental relevance.""",
            tools=[],
            verbose=True,
            llm=self.llm,
        )

    def create_document_task(self, chunks: list, docs: list) -> Task:
        """Create initial document classification and structure analysis task"""
        return Task(
            description="""First, identify the type of document from the content. Then analyze its structure and content accordingly.
            
            Document Content:
            {content}
            
            1. First, determine the document type (e.g., CV/Resume, Technical Document, Project Proposal, Policy Document, etc.)
            2. Then analyze the structure and content based on the identified type
            
            IMPORTANT: Return ONLY the JSON object, no markdown formatting or comments.
            
            Return EXACTLY this structure:
            {
                "document_classification": {
                    "type": "identified document type",
                    "confidence": "confidence score between 0-1",
                    "indicators": ["list of key indicators that helped identify the document type"]
                },
                "structure_analysis": {
                    "total_sections": number,
                    "main_sections": ["list of main sections found"],
                    "document_format": "description of document format and structure"
                },
                "content_overview": {
                    "main_theme": "overall theme or purpose",
                    "key_points": ["list of key points"],
                    "audience": "intended audience of the document"
                },
                "preparation_notes": [
                    "list of notes about document preparation and special considerations for further analysis"
                ]
            }""",
            agent=self.create_document_processor(),
            expected_output="Pure JSON object with no markdown",
            context=[
                {
                    "role": "user",
                    "content": json.dumps([doc.page_content for doc in docs], indent=2),
                    "description": "Initial document analysis",
                    "expected_output": "Plain JSON object with no markdown",
                }
            ],
        )

    def create_analysis_task(self) -> Task:
        """Create adaptive content analysis task based on document type"""
        return Task(
            description=f"""Analyze the following document content based on its type and structure:
            {self.content}
            
            IMPORTANT: Return ONLY the JSON object, no markdown formatting or comments.
            
            Return EXACTLY this structure:
            {{
                "main_topics": [
                    "list of primary topics or subjects covered in the document"
                ],
                "key_components": [
                    "list of essential elements, requirements, or specifications found"
                ],
                "critical_points": [
                    "list of important points, findings, or decisions"
                ],
                "relationships": [
                    "list of connections between different parts of the document"
                ],
                "action_items": [
                    "list of required actions or next steps identified"
                ],
                "summary": "detailed summary of the entire document's content and purpose"
            }}""",
            agent=self.create_content_analyzer(),
            expected_output="Pure JSON object with no markdown",
            context=[
                {
                    "role": "user",
                    "content": self.content,
                    "description": "Detailed content analysis",
                    "expected_output": "Plain JSON object with no markdown",
                }
            ],
        )

    def create_matching_task(self, departments: list, analysis_result: str) -> Task:
        """Create intelligent department matching task"""
        return Task(
            description=f"""Based on the document analysis, identify the two most relevant departments 
            that should be involved with this document.
            
            Document Analysis:
            {analysis_result}
            
            Available Departments:
            {json.dumps(departments, indent=2)}
            
            REQUIREMENTS:
            1. Select TWO different departments most relevant to the document content
            2. Consider primary subject matter and secondary impacts
            3. Think about both immediate relevance and long-term implications
            4. Consider cross-departmental collaboration needs
            5. IMPORTANT: Return ONLY the JSON object, no markdown formatting or comments
            
            Return EXACTLY this structure with no additional text or formatting:
            {{
                "matched_departments": [
                    {{
                        "id": <primary department id>,
                        "code": "<primary department code>",
                        "name": "<primary department name>",
                        "reasoning": "<detailed explanation of primary relevance and responsibilities>"
                    }},
                    {{
                        "id": <secondary department id>,
                        "code": "<secondary department code>",
                        "name": "<secondary department name>",
                        "reasoning": "<detailed explanation of secondary relevance and support role>"
                    }}
                ],
                "collaboration_notes": "notes on how the departments should collaborate on this"
            }}""",
            agent=self.create_department_matcher(),
            expected_output="Pure JSON object with no markdown",
            context=[
                {
                    "role": "user",
                    "content": json.dumps(
                        {"analysis": analysis_result, "departments": departments},
                        indent=2,
                    ),
                    "description": "Department matching analysis",
                    "expected_output": "Plain JSON object with no markdown",
                }
            ],
        )

    async def process(self) -> dict:
        """Process document and return results"""
        try:
            logger.info("=========== Starting Document Processing ===========")

            # Split text and create documents
            chunks = self.text_splitter.split_text(self.content)
            logger.info(f"Text Splitting Results: {len(chunks)} chunks")

            docs = [
                LangchainDocument(
                    page_content=chunk,
                    metadata={
                        "id": str(uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    },
                )
                for i, chunk in enumerate(chunks)
            ]

            # Store in vector database
            logger.info("Storing documents in vector database...")
            self.vectorstore.add_documents(docs)
            logger.info("Vector storage complete")

            # Fetch departments
            departments = self.fetch_departments()
            if not departments:
                raise ValueError("No departments found in database")

            logger.info(f"Fetched {len(departments)} departments")

            try:
                # Execute document processing
                logger.info("Starting document analysis...")
                initial_crew = Crew(
                    agents=[self.create_document_processor()],
                    tasks=[self.create_document_task(chunks, docs)],
                    process=Process.sequential,
                    verbose=2,
                )
                doc_result = initial_crew.kickoff()
                logger.info("Initial document analysis completed")

                # Execute content analysis
                logger.info("Starting detailed content analysis...")
                analysis_crew = Crew(
                    agents=[self.create_content_analyzer()],
                    tasks=[self.create_analysis_task()],
                    process=Process.sequential,
                    verbose=2,
                )
                analysis_result = analysis_crew.kickoff()
                logger.info("Content analysis completed")

                # Process analysis result
                analysis_data = (
                    analysis_result[0]
                    if isinstance(analysis_result, list)
                    else analysis_result
                )
                if not analysis_data:
                    raise ValueError("No analysis results produced")

                # Execute department matching
                logger.info("Starting department matching...")
                matching_crew = Crew(
                    agents=[self.create_department_matcher()],
                    tasks=[
                        self.create_matching_task(
                            departments, json.dumps(analysis_data, indent=2)
                        )
                    ],
                    process=Process.sequential,
                    verbose=2,
                )
                matching_result = matching_crew.kickoff()
                logger.info("Department matching completed")

                # Process matching results
                if not matching_result:
                    raise ValueError("No department matching results produced")

                try:
                    # Get the raw matching result
                    department_match = (
                        matching_result[0]
                        if isinstance(matching_result, list)
                        else matching_result
                    )

                    # Log the raw output for debugging
                    logger.debug(f"Raw department matching output: {department_match}")

                    # Clean and parse the output
                    if isinstance(department_match, dict):
                        clean_match = department_match
                    else:
                        clean_match = json.loads(clean_json_output(department_match))

                    logger.debug(
                        f"Cleaned department match: {json.dumps(clean_match, indent=2)}"
                    )

                    # Validate the structure
                    if "matched_departments" not in clean_match:
                        raise ValueError("Invalid department matching format")

                    matched_deps = clean_match["matched_departments"]
                    if len(matched_deps) < 2:
                        raise ValueError(f"Not enough departments matched")

                    # Find similar documents
                    logger.info("Searching for similar documents...")
                    try:
                        similar_docs = self.vectorstore.similarity_search_with_score(
                            self.content,
                            k=3,
                            filter={"id": {"$nin": [doc.metadata["id"] for doc in docs]}},
                        )
                        logger.info(f"Found {len(similar_docs)} similar documents")
                    except Exception as search_error:
                        logger.warning(
                            f"Error during similarity search: {str(search_error)}"
                        )
                        similar_docs = []  # Set empty list if search fails

                    # Format similar documents
                    similar_docs_formatted = []
                    for doc, score in similar_docs:
                        try:
                            similar_docs_formatted.append(
                                {
                                    "id": doc.metadata["id"],
                                    "content": doc.page_content[:200],
                                    "score": float(score),
                                    "metadata": {
                                        k: v
                                        for k, v in doc.metadata.items()
                                        if k != "embedding"
                                    },
                                }
                            )
                        except Exception as format_error:
                            logger.warning(
                                f"Error formatting similar doc: {str(format_error)}"
                            )
                            continue

                    # Compile final results
                    result = {
                        "document_ids": [doc.metadata["id"] for doc in docs],
                        "document_analysis": (
                            clean_json_output(doc_result[0] if isinstance(doc_result, list) else doc_result),
                        ),
                        "content_analysis": clean_json_output(analysis_result[0] if isinstance(analysis_result, list) else analysis_result),
                        "department_matching": clean_match,
                        "similar_documents": similar_docs_formatted,
                        "processing_metadata": {
                            "total_chunks": len(chunks),
                            "timestamp": datetime.utcnow().isoformat(),
                            "departments_analyzed": len(departments),
                        },
                    }

                    logger.info("=========== Processing Complete ===========")
                    return result

                except json.JSONDecodeError as je:
                    logger.error(f"JSON parsing error: {str(je)}")
                    logger.error(f"Problematic content: {department_match}")
                    raise ValueError(
                        f"Failed to parse department matching result: {str(je)}"
                    )

            except Exception as e:
                logger.error(f"Error during crew execution: {str(e)}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}", exc_info=True)
            raise

    async def cleanup(self):
        """Cleanup resources"""
        try:
            logger.info("Cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")