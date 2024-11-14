
from fastapi import APIRouter, UploadFile, Depends, HTTPException
from app.core.ai.agents import DocumentProcessor
from app.db.session import get_db 
from sqlalchemy.orm import Session
import PyPDF2
import pandas as pd
import docx
from io import BytesIO
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

async def extract_text_from_file(file: UploadFile) -> str:
    try:
        content = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            text = ' '.join(page.extract_text() for page in pdf_reader.pages)
        
        elif file_extension == 'docx':
            doc = docx.Document(BytesIO(content))
            text = ' '.join(paragraph.text for paragraph in doc.paragraphs)
        
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(BytesIO(content))
            text = df.to_string()
        
        elif file_extension == 'txt':
            text = content.decode('utf-8', errors='ignore')
        
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}")
        
        return text.strip()
        
    except Exception as e:
        logger.error(f"File processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing file")

@router.post("/analyze")
async def analyze_document(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    text = await extract_text_from_file(file)
    if not text:
        raise HTTPException(status_code=400, detail="No content extracted from file")
        
    processor = DocumentProcessor(db)
    try:
        result = await processor.process_document(text)
        return result
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error analyzing document")
