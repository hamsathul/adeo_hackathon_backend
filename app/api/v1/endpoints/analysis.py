
from fastapi import APIRouter, UploadFile, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Optional
import PyPDF2
import pandas as pd
import docx
from io import BytesIO
import logging
from uuid import uuid4
from datetime import datetime

from app.db.session import get_db
from app.core.ai.departmentdocprocessor import DepartmentDocumentProcessor

logger = logging.getLogger(__name__)
router = APIRouter()

class ProcessingResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict] = None

class ProcessingTask:
    def __init__(self):
        self.tasks = {}

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

processing_tasks = ProcessingTask()

@router.post("/analyze", response_model=ProcessingResponse)
async def analyze_document(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    """
    Analyze document using CrewAI document processing system and wait for results
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
        
        # Create task ID
        task_id = str(uuid4())
        logger.info(f"Created task ID: {task_id}")
        
        # Initialize task status
        processing_tasks.tasks[task_id] = {
            "status": "processing",
            "metadata": {
                "filename": file.filename,
                "content_type": file.content_type,
                "timestamp": datetime.utcnow().isoformat(),
                "text_length": len(text)
            }
        }
        
        # Process document
        try:
            processor = DepartmentDocumentProcessor(db, text)
            logger.info("Starting document processing...")
            
            # Process document and wait for result
            result = await processor.process()
            
            # Log processing success details
            logger.info(f"""
            Processing completed successfully:
            - Task ID: {task_id}
            - Document chunks: {len(result.get('document_ids', []))}
            - Analysis completed: {bool(result.get('analysis'))}
            - Departments matched: {bool(result.get('matched_department1')) and bool(result.get('matched_department2'))}
            - Similar documents found: {len(result.get('similar_documents', []))}
            """)
            
            # Update task with results
            processing_tasks.tasks[task_id] = {
                "status": "completed",
                "result": result,
                "completion_time": datetime.utcnow().isoformat()
            }
            
            # Return completed response with results
            return ProcessingResponse(
                task_id=task_id,
                status="completed",
                result=result
            )
            
        except Exception as e:
            error_message = f"""
            Processing error:
            - Task ID: {task_id}
            - Error type: {type(e).__name__}
            - Error message: {str(e)}
            """
            logger.error(error_message, exc_info=True)
            
            processing_tasks.tasks[task_id] = {
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
                "failure_time": datetime.utcnow().isoformat()
            }
            
            raise HTTPException(
                status_code=500,
                detail=f"Processing error: {str(e)}"
            )
            
        finally:
            try:
                await processor.cleanup()
                logger.info(f"Cleanup completed for task {task_id}")
            except Exception as cleanup_error:
                logger.error(f"Cleanup error for task {task_id}: {str(cleanup_error)}")
        
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

# Status endpoint remains for checking historical tasks
@router.get("/status/{task_id}", response_model=ProcessingResponse)
async def get_task_status(task_id: str):
    """Get the status of a document processing task"""
    try:
        if task_id not in processing_tasks.tasks:
            logger.warning(f"Task not found: {task_id}")
            raise HTTPException(status_code=404, detail="Task not found")
            
        task = processing_tasks.tasks[task_id]
        logger.info(f"""
        Task status check:
        - Task ID: {task_id}
        - Status: {task['status']}
        - Has result: {bool(task.get('result'))}
        - Error: {task.get('error', 'None')}
        """)
        
        return ProcessingResponse(
            task_id=task_id,
            status=task["status"],
            result=task.get("result")
        )
        
    except Exception as e:
        logger.error(f"Error checking task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error checking task status: {str(e)}"
        )