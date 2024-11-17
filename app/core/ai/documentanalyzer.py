from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument
from datetime import datetime
from uuid import uuid4
import logging
import json

logger = logging.getLogger(__name__)

def clean_json_output(output: str) -> str:
    """Clean JSON output by removing markdown and code block markers"""
    try:
        cleaned = output.replace("```json", "")
        cleaned = cleaned.replace("```jsonc", "")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.strip()
        json.loads(cleaned)
        return cleaned
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON after cleaning: {cleaned}")

class DocumentAnalyzer:
    """Document analysis system with RAG capabilities"""

    def __init__(self, content: str, database_url: str, openai_api_key: str):
        """Initialize the analyzer with document content and necessary configurations"""
        self.content = content
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.3,
            top_k=40,
            top_p=0.8
        )

        # Initialize embeddings and vector store
        self.embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        self.vectorstore = PGVector(
            collection_name="document_store",
            connection=database_url,
            embeddings=self.embeddings,
        )

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )

    async def store_document(self) -> list:
        """Split and store document in vector database"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(self.content)
            logger.info(f"Split document into {len(chunks)} chunks")

            # Create documents with metadata
            docs = [
                LangchainDocument(
                    page_content=chunk,
                    metadata={
                        "id": str(uuid4()),
                        "timestamp": datetime.utcnow().isoformat(),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                )
                for i, chunk in enumerate(chunks)
            ]

            # Store in vector database
            logger.info("Storing documents in vector database...")
            self.vectorstore.add_documents(docs)
            logger.info("Vector storage complete")

            return docs

        except Exception as e:
            logger.error(f"Error storing document: {str(e)}", exc_info=True)
            raise

    async def find_similar_documents(self, docs: list) -> list:
        """Find similar documents in the vector store"""
        try:
            similar_docs = self.vectorstore.similarity_search_with_score(
                self.content,
                k=3,
                filter={"id": {"$nin": [doc.metadata["id"] for doc in docs]}}
            )

            similar_docs_formatted = []
            for doc, score in similar_docs:
                similar_docs_formatted.append({
                    "id": doc.metadata["id"],
                    "content": doc.page_content[:200],  # First 200 chars as preview
                    "similarity_score": float(score),
                    "metadata": {
                        k: v for k, v in doc.metadata.items() 
                        if k != "embedding"
                    }
                })

            return similar_docs_formatted

        except Exception as e:
            logger.warning(f"Error finding similar documents: {str(e)}")
            return []

    async def analyze_content(self) -> dict:
        """Analyze document content using LLM"""
        try:
            analysis_prompt = f"""Analyze this document thoroughly and provide a detailed structured analysis.

            Document Content:
            {self.content}

            Provide ONLY a JSON object with this exact structure:
            {{
                "document_metadata": {{
                    "document_type": "specific type of document (e.g., Policy Document, Technical Specification, Legal Agreement, etc.)",
                    "classification": "internal/external/confidential/public",
                    "language": "primary language of the document",
                    "formality_level": "formal/semi-formal/informal"
                }},
                
                "executive_summary": {{
                    "main_purpose": "clear statement of document's primary purpose",
                    "target_audience": ["list of intended audience groups"],
                    "brief_overview": "2-3 sentence overview of the document"
                }},
                
                "key_components": {{
                    "main_topics": ["list of primary topics covered"],
                    "critical_points": ["3-5 most important points"],
                    "key_stakeholders": ["individuals or groups mentioned or impacted"]
                }},
                
                "requirements_analysis": {{
                    "mandatory_requirements": ["list of must-have requirements"],
                    "optional_requirements": ["list of optional/recommended items"],
                    "prerequisites": ["list of prerequisites if any"],
                    "constraints": ["list of limitations or constraints"]
                }},
                
                "temporal_aspects": {{
                    "important_dates": ["list of specific dates mentioned"],
                    "deadlines": ["list of deadlines"],
                    "timelines": ["list of timeline-related information"],
                    "duration_details": ["any duration or time period specifications"]
                }},
                
                "structural_analysis": {{
                    "sections": [
                        {{
                            "section_name": "name of the section",
                            "section_purpose": "purpose of this section",
                            "key_points": ["main points from this section"],
                            "dependencies": ["other sections this depends on or relates to"]
                        }}
                    ]
                }},
                
                "action_items": {{
                    "immediate_actions": ["actions that need immediate attention"],
                    "future_actions": ["actions for later consideration"],
                    "responsibilities": ["specific responsibilities assigned"],
                    "dependencies": ["dependencies for actions"]
                }},
                
                "compliance_and_governance": {{
                    "regulatory_requirements": ["any regulatory/compliance requirements"],
                    "policies_referenced": ["internal or external policies mentioned"],
                    "governance_aspects": ["governance-related points"]
                }},
                
                "technical_aspects": {{
                    "technical_requirements": ["any technical specifications"],
                    "systems_mentioned": ["systems or platforms referenced"],
                    "technical_dependencies": ["technical dependencies noted"]
                }},
                
                "risks_and_considerations": {{
                    "identified_risks": ["potential risks mentioned"],
                    "mitigation_strategies": ["proposed risk mitigation approaches"],
                    "assumptions": ["key assumptions made"],
                    "dependencies": ["critical dependencies noted"]
                }},
                
                "next_steps": {{
                    "recommended_actions": ["suggested next actions"],
                    "required_approvals": ["approvals needed"],
                    "implementation_considerations": ["points to consider for implementation"]
                }},
                
                "appendix": {{
                    "definitions": {{
                        "key_terms": ["important terms used"],
                        "abbreviations": ["abbreviations used"]
                    }},
                    "references": ["external references or citations"],
                    "related_documents": ["related documents mentioned"]
                }}
            }}

            Guidelines:
            1. Provide concise but informative content for each field
            2. If a section is not applicable, provide an empty array or "Not applicable"
            3. Ensure all dates and deadlines are clearly specified
            4. Focus on factual information present in the document
            5. Maintain the exact structure provided"""

            response = await self.llm.ainvoke(analysis_prompt)
            return json.loads(clean_json_output(response.content))

        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}", exc_info=True)
            raise

    async def analyze(self) -> dict:
        """Main analysis pipeline"""
        try:
            logger.info("=========== Starting Document Analysis ===========")

            # Store document and get chunks
            docs = await self.store_document()

            # Analyze content
            logger.info("Analyzing document content...")
            content_analysis = await self.analyze_content()

            # Find similar documents
            logger.info("Finding similar documents...")
            similar_docs = await self.find_similar_documents(docs)

            # Compile results
            result = {
                "document_ids": [doc.metadata["id"] for doc in docs],
                "content_analysis": content_analysis,
                "similar_documents": similar_docs,
                "processing_metadata": {
                    "total_chunks": len(docs),
                    "timestamp": datetime.utcnow().isoformat(),
                    "analysis_version": "1.0"
                }
            }

            logger.info("=========== Analysis Complete ===========")
            return result

        except Exception as e:
            logger.error(f"Document analysis failed: {str(e)}", exc_info=True)
            raise

async def main(
    document_content: str,
    database_url: str,
    openai_api_key: str
) -> dict:
    """Main function to analyze a document"""
    analyzer = DocumentAnalyzer(
        content=document_content,
        database_url=database_url,
        openai_api_key=openai_api_key
    )
    return await analyzer.analyze()