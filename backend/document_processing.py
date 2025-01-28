from typing import List, Dict, Tuple
from markitdown import MarkItDown # Changed from convert_to_markdown
import os
import tempfile
from fastapi import HTTPException
import mimetypes
import logging
import asyncio
import PyPDF2
from chunking import chunk_text
from extraction import extract_text_from_pdf
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define supported MIME types and their file extensions
SUPPORTED_MIMETYPES = {
    'application/pdf': '.pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
    'application/msword': '.doc',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
    'application/vnd.ms-powerpoint': '.ppt',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
    'application/vnd.ms-excel': '.xls',
    'text/plain': '.txt',
    'text/markdown': '.md'
}

def validate_file_type(filename: str) -> bool:
    """
    Validate if the file type is supported.
    """
    mime_type = mimetypes.guess_type(filename)[0]
    return mime_type in SUPPORTED_MIMETYPES

async def process_markdown_content(markdown_content: str) -> List[dict]:
    """
    Process markdown content into chunks with page estimates.
    """
    chunks = chunk_text(markdown_content)
    chars_per_page = 3000
    for chunk in chunks:
        estimated_page = (chunk['start_position'] // chars_per_page) + 1
        chunk['page'] = estimated_page
    return chunks

async def process_office_document(file_bytes: bytes, file_extension: str) -> str:
    """
    Process Office documents using markitdown.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name
        
        try:
            # Using to_markdown instead of convert_to_markdown
            markdown_text = MarkItDown(temp_path)
            if not markdown_text:
                raise ValueError("Failed to convert document to markdown")
            return markdown_text
        except Exception as e:
            logger.error(f"Error converting document to markdown: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error converting document: {str(e)}"
            )
        finally:
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Error removing temporary file {temp_path}: {str(e)}")

async def process_text_file(file_bytes: bytes) -> str:
    """
    Process plain text files.
    """
    try:
        return file_bytes.decode('utf-8', errors='replace')
    except Exception as e:
        logger.error(f"Error decoding text file: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error processing text file: Invalid encoding"
        )

async def process_document_content(file_bytes: bytes, filename: str) -> List[dict]:
    """
    Process different document types and convert them to text chunks.
    """
    mime_type = mimetypes.guess_type(filename)[0]
    
    if not mime_type or mime_type not in SUPPORTED_MIMETYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported types: {', '.join(SUPPORTED_MIMETYPES.keys())}"
        )
    
    try:
        # Process based on file type
        if mime_type == 'application/pdf':
            return await extract_text_from_pdf(file_bytes)
            
        elif mime_type in ('text/plain', 'text/markdown'):
            text_content = await process_text_file(file_bytes)
            return await process_markdown_content(text_content)
            
        else:
            # Handle Office documents
            markdown_content = await process_office_document(
                file_bytes,
                SUPPORTED_MIMETYPES[mime_type]
            )
            return await process_markdown_content(markdown_content)
            
    except Exception as e:
        logger.error(f"Error processing document {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )

async def get_document_metadata(file_bytes: bytes, filename: str) -> Dict[str, str]:
    """
    Extract metadata from the document.
    """
    mime_type = mimetypes.guess_type(filename)[0]
    
    metadata = {
        'filename': filename,
        'mime_type': mime_type or 'application/octet-stream',
        'size': len(file_bytes)
    }
    
    try:
        if mime_type == 'application/pdf':
            pdf_reader = PyPDF2.PdfReader(BytesIO(file_bytes))
            metadata.update({
                'pages': len(pdf_reader.pages),
                'pdf_version': pdf_reader.pdf_version
            })
            
            if pdf_reader.metadata:
                metadata.update({
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'creation_date': pdf_reader.metadata.get('/CreationDate', '')
                })
    except Exception as e:
        logger.warning(f"Error extracting metadata from {filename}: {str(e)}")
    
    return metadata