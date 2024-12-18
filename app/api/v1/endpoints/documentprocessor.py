from fastapi import APIRouter, UploadFile, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional, List
import PyPDF2
import pandas as pd
import docx
from io import BytesIO
import logging
from uuid import uuid4
from datetime import datetime

from app.db.session import get_db
from app.core.config import get_settings
from app.core.ai.documentanalyzer import DocumentAnalyzer
from app.models.opinion import Document

logger = logging.getLogger(__name__)
router = APIRouter()

class AnalysisResponse(BaseModel):
    document_id: str
    status: str
    analysis_result: Optional[Dict] = None
    metadata: Dict

class DocumentSection(BaseModel):
    section_name: str
    key_content: str

class DocumentAnalysis(BaseModel):
    document_type: str
    main_purpose: str
    key_points: List[str]
    requirements: List[str]
    important_dates_deadlines: List[str]
    sections_analysis: List[DocumentSection]
    summary: str
    audience: str
    action_items: List[str]

async def extract_text_from_file(file: UploadFile) -> str:
    """Extract text content from various file types"""
    try:
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text = ' '.join(
                page.extract_text() 
                for page in pdf_reader.pages 
                if page.extract_text()
            )
            
        elif file_extension == 'docx':
            doc = docx.Document(BytesIO(content))
            text = ' '.join(
                paragraph.text 
                for paragraph in doc.paragraphs 
                if paragraph.text.strip()
            )
            
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(BytesIO(content))
            text = (
                f"Spreadsheet Contents:\n"
                f"Columns: {', '.join(df.columns)}\n"
                f"Data:\n{df.to_string(index=False)}"
            )
            
        elif file_extension == 'txt':
            text = content.decode('utf-8', errors='ignore')
            
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type: {file_extension}"
            )
        
        text = text.strip()
        if not text:
            raise HTTPException(
                status_code=400, 
                detail=f"No content could be extracted from the {file_extension} file"
            )
            
        return text
        
    except Exception as e:
        logger.error(f"File processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing file: {str(e)}"
        )

@router.post("/analyze-document", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    """
    Analyze document and return structured analysis results
    """
    try:
        # Log file details
        logger.info(f"""
        Starting document analysis:
        - Filename: {file.filename}
        - Content type: {file.content_type}
        - Size: {file.size if hasattr(file, 'size') else 'Unknown'} bytes
        """)
        
        # Extract text from file
        logger.info("Extracting text from file...")
        text = await extract_text_from_file(file)
        logger.info(f"Extracted {len(text)} characters of text")
        
        # Generate document ID
        document_id = str(uuid4())
        
        try:
            # Initialize settings and analyzer
            settings = get_settings()
            analyzer = DocumentAnalyzer(
                content=text,
                database_url=settings.DATABASE_URL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Process document
            logger.info("Starting document analysis...")
            result = await analyzer.analyze()
            
            # Log success details
            logger.info(f"""
            Analysis completed successfully:
            - Document ID: {document_id}
            - Document chunks: {len(result.get('document_ids', []))}
            - Similar documents found: {len(result.get('similar_documents', []))}
            """)
            
            # Prepare metadata
            metadata = {
                "filename": file.filename,
                "content_type": file.content_type,
                "text_length": len(text),
                "processing_time": datetime.utcnow().isoformat(),
                "chunks_processed": len(result.get('document_ids', [])),
                "similar_docs_found": len(result.get('similar_documents', []))
            }
            
            return AnalysisResponse(
                document_id=document_id,
                status="completed",
                analysis_result=result,
                metadata=metadata
            )
            
        except Exception as e:
            error_message = f"""
            Analysis error:
            - Document ID: {document_id}
            - Error type: {type(e).__name__}
            - Error message: {str(e)}
            """
            logger.error(error_message, exc_info=True)
            
            raise HTTPException(
                status_code=500,
                detail=f"Analysis error: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"""
        Endpoint error:
        - Error type: {type(e).__name__}
        - Error message: {str(e)}
        - File: {file.filename if file else 'Unknown'}
        """
        logger.error(error_message, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

@router.get("/document/{document_id}", response_model=AnalysisResponse)
async def get_document_analysis(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve analysis results for a specific document"""
    try:
        # Here you would typically fetch the results from your database
        # For now, we'll return a 404 since we're not implementing storage
        raise HTTPException(
            status_code=404,
            detail="Document analysis not found"
        )
    except Exception as e:
        logger.error(f"Error retrieving analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analysis: {str(e)}"
        )
        
@router.post("/analyze-document/existing/{document_id}", response_model=AnalysisResponse)
async def analyze_existing_document(
    document_id: int = Path(...),
    db: Session = Depends(get_db)
):
    """
    Analyze an existing document from the database
    """
    logger.info(f"Starting analysis for existing document ID: {document_id}")
    
    try:
        # Get document from database
        logger.info(f"Fetching document {document_id} from database")
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found in database")
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"Found document: {document.file_name} (ID: {document.id})")
        
        # Get full file path
        settings = get_settings()
        file_path = f"{document.file_path}"
        logger.info(f"Constructed file path: {file_path}")
        
        try:
            # Read file content
            logger.info(f"Attempting to read file from: {file_path}")
            with open(file_path, 'rb') as f:
                content = f.read()
            logger.info(f"Successfully read {len(content)} bytes from file")
            
            # Create mock UploadFile
            logger.info("Creating mock UploadFile object")
            content_io = BytesIO(content)
            mock_file = UploadFile(
                filename=document.file_name,
                file=content_io,
                size=len(content),
                headers={"content-type": document.file_type} 
            )
            mock_file._file = content_io
            logger.info(f"Created mock file with name: {mock_file.filename} and type: {mock_file.content_type}")
            
            # Extract text
            logger.info("Starting text extraction")
            text = await extract_text_from_file(mock_file)
            logger.info(f"Successfully extracted {len(text)} characters of text")
            
            # Generate document ID
            document_id = str(uuid4())
            logger.info(f"Generated analysis ID: {document_id}")
            
            # Initialize analyzer
            logger.info("Initializing DocumentAnalyzer")
            analyzer = DocumentAnalyzer(
                content=text,
                database_url=settings.DATABASE_URL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Process document
            logger.info("Starting document analysis...")
            result = await analyzer.analyze()
            logger.info("Analysis completed successfully")
            
            # Log analysis results summary
            logger.info(f"""
            Analysis Results Summary:
            - Document IDs: {len(result.get('document_ids', []))}
            - Similar Documents: {len(result.get('similar_documents', []))}
            - Analysis Status: Completed
            """)
            
            # Prepare metadata
            metadata = {
                "filename": document.file_name,
                "content_type": document.file_type,
                "text_length": len(text),
                "processing_time": datetime.utcnow().isoformat(),
                "chunks_processed": len(result.get('document_ids', [])),
                "similar_docs_found": len(result.get('similar_documents', []))
            }
            logger.info(f"Prepared metadata: {metadata}")
            
            response = AnalysisResponse(
                document_id=document_id,
                status="completed",
                analysis_result=result,
                metadata=metadata
            )
            logger.info("Successfully prepared analysis response")
            return response
            
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise HTTPException(
                status_code=404,
                detail="Document file not found on server"
            )
        except Exception as e:
            error_msg = f"Error processing document: {str(e)}"
            logger.error(error_msg, exc_info=True)
            logger.error(f"""
            Processing Error Details:
            - Document ID: {document_id}
            - File Path: {file_path}
            - Error Type: {type(e).__name__}
            - Error Message: {str(e)}
            """)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing document: {str(e)}"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error in analyze_existing_document: {str(e)}"
        logger.error(error_msg, exc_info=True)
        logger.error(f"""
        General Error Details:
        - Document ID: {document_id}
        - Error Type: {type(e).__name__}
        - Error Message: {str(e)}
        - Stack Trace: Available in logs
        """)
        raise HTTPException(
            status_code=500,
            detail=f"Server error: {str(e)}"
        )