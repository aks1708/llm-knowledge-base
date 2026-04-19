"""
PDF utility functions for page handling and file operations.
"""

import shutil
import tempfile
from pathlib import Path
from typing import List, Tuple

import requests
from PyPDF2 import PdfReader, PdfWriter


def parse_page_range(range_str: str, total_pages: int) -> List[int]:
    """
    Parse page range string like '1-5' or '1,3,5-7' into list of page numbers (0-indexed).
    
    Args:
        range_str: Page range string (e.g., '1-5', '1,3,5-7', '3')
        total_pages: Total number of pages in the PDF
        
    Returns:
        Sorted list of 0-indexed page numbers
    """
    pages = set()
    parts = range_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle range like '1-5' - clamp to valid page bounds
            start, end = part.split('-')
            start = max(1, int(start.strip()))
            end = min(total_pages, int(end.strip()))
            pages.update(range(start - 1, end))  # Convert to 0-indexed
        else:
            # Handle single page like '3' - validate bounds
            page = int(part.strip())
            if 1 <= page <= total_pages:
                pages.add(page - 1)  # Convert to 0-indexed
    
    return sorted(list(pages))


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be a valid filename.
    
    Args:
        name: Original filename string
        
    Returns:
        Sanitized filename string
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    name = name.strip('. ')
    name = ' '.join(name.split())
    return name


def download_pdf_to_temp(pdf_path: str, is_url: bool) -> Tuple[Path, str]:
    """
    Download PDF from URL or copy local file to temp directory.
    
    Args:
        pdf_path: Path to PDF (local file or URL)
        is_url: Whether the path is a URL
        
    Returns:
        Tuple of (temp_file_path, temp_dir_path)
    """
    temp_dir = tempfile.mkdtemp(prefix="pdf2md_")
    temp_path = Path(temp_dir) / "temp.pdf"
    
    if is_url:
        # Stream download to handle large PDFs efficiently
        response = requests.get(pdf_path, stream=True)
        response.raise_for_status()
        
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    else:
        # Copy local file preserving metadata
        shutil.copy2(pdf_path, temp_path)
    
    return temp_path, temp_dir


def extract_pages_from_pdf(pdf_path: Path, pages_to_extract: List[int]) -> Tuple[Path, str]:
    """
    Extract specific pages from PDF and save to new temp file.
    
    Args:
        pdf_path: Path to source PDF
        pages_to_extract: List of 0-indexed page numbers to extract
        
    Returns:
        Tuple of (extracted_pdf_path, temp_dir_path)
    """
    temp_dir = tempfile.mkdtemp(prefix="pdf2md_extracted_")
    output_path = Path(temp_dir) / "extracted.pdf"
    
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    
    # Copy selected pages to new PDF
    for page_num in pages_to_extract:
        writer.add_page(reader.pages[page_num])
    
    # Write extracted pages to output file
    with open(output_path, 'wb') as f:
        writer.write(f)
    
    return output_path, temp_dir
