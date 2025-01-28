import PyPDF2
from io import BytesIO
import asyncio
from typing import List
from chunking import chunk_text

async def process_page(page_num: int, pdf_reader: PyPDF2.PdfReader) -> List[dict]:
    page_text = pdf_reader.pages[page_num].extract_text()
    if page_text.strip():
        chunks = chunk_text(page_text)
        for chunk in chunks:
            chunk['page'] = page_num + 1
        return chunks
    return []

async def extract_text_from_pdf(file_bytes: bytes) -> List[dict]:
    pdf_stream = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_stream)
    
    tasks = [process_page(i, pdf_reader) for i in range(len(pdf_reader.pages))]
    chunks_list = await asyncio.gather(*tasks)
    
    return [chunk for page_chunks in chunks_list for chunk in page_chunks]
