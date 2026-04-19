"""
Convert PDF files to Markdown using Docling.
Usage: python pdf2md.py <path_to_pdf>
"""

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional

from colorama import Fore, init
from PyPDF2 import PdfReader

from config.docling_config import create_document_converter
from utils.pdf_utils import (
    parse_page_range,
    sanitize_filename,
    download_pdf_to_temp,
    extract_pages_from_pdf,
)

# Initialize colorama
init()

def get_output_path(default_path: str = "raw/papers") -> str:
    """Ask user for output path with default suggestion."""
    user_input = input(f"{Fore.BLUE}Enter output path [default: {default_path}]: {Fore.RESET}").strip()
    return user_input if user_input else default_path


def get_output_filename(default_name: str) -> str:
    """Ask user for output filename with default suggestion."""
    user_input = input(f"{Fore.MAGENTA}Enter the filename [default: {default_name}]: {Fore.RESET}").strip()
    return sanitize_filename(user_input) if user_input else default_name


def ask_page_range(total_pages: int) -> Optional[List[int]]:
    """Ask user for page range and return the selected pages."""
    while True:
        range_input = input(f"{Fore.CYAN}Enter page range (inclusive, e.g., '1-5' means pages 1 through 5): {Fore.RESET}").strip()
        try:
            pages = parse_page_range(range_input, total_pages)
            if not pages:
                print(f"{Fore.RED}No valid pages selected. Using all pages.{Fore.RESET}")
                return None
            print(f"{Fore.GREEN}Selected pages: {range_input}{Fore.RESET}")
            return pages
        except (ValueError, IndexError):
            print(f"{Fore.RED}Invalid page range. Please try again.{Fore.RESET}")


def convert_pdf_to_markdown(pdf_path: str, output_dir: str) -> bool:
    """Convert PDF to Markdown using Docling."""
    is_url = pdf_path.startswith(('http://', 'https://'))
    
    # Validate input and determine default filename
    if not is_url:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            print(f"Error: PDF file not found: {pdf_path}")
            return False
        if pdf_path.suffix.lower() != '.pdf':
            print(f"Error: File is not a PDF: {pdf_path}")
            return False
        default_filename = pdf_path.stem  # Use filename without extension
    else:
        # Extract filename from URL path
        url_path = pdf_path.rstrip('/')
        default_filename = url_path.split('/')[-1]
    
    filename = get_output_filename(default_filename)
    output_filename = filename + '.md'
    output_path = Path(output_dir) / output_filename
    
    # Create output directory and all parent directories if they don't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize with original path; may be updated to temp file if page extraction needed
    temp_pdf_path: str = str(pdf_path)
    temp_dirs_to_cleanup: List[str] = []
    pages_to_extract: Optional[List[int]] = None
    
    # Prompt for page range selection (requires downloading/copying first to count pages)
    while True:
        choice = input(f"{Fore.CYAN}Select specific pages? (y/n) [default: n]: {Fore.RESET}").strip().lower()
        if not choice or choice == 'n':
            break
        elif choice == 'y':
            print(f"{Fore.YELLOW}Downloading PDF...{Fore.RESET}")
            temp_pdf_path, temp_dir = download_pdf_to_temp(pdf_path, is_url)
            temp_dirs_to_cleanup = [temp_dir]
            
            # Get page count to validate user's page range selection
            reader = PdfReader(temp_pdf_path)
            total_pages = len(reader.pages)
            print(f"{Fore.YELLOW}Total pages in PDF: {total_pages}{Fore.RESET}")
            
            pages_to_extract = ask_page_range(total_pages)
            
            # Extract selected pages to a new temp file
            if pages_to_extract:
                extracted_pdf_path, extracted_temp_dir = extract_pages_from_pdf(
                    Path(temp_pdf_path), pages_to_extract
                )
                temp_pdf_path = str(extracted_pdf_path)
                temp_dirs_to_cleanup.append(extracted_temp_dir)
            break
    
    converter = create_document_converter()
    print(f"Converting to {output_filename}...")
    
    try:
        # Perform the actual PDF to Markdown conversion
        result = converter.convert(temp_pdf_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result.document.export_to_markdown())
        print(f"Successfully converted to: {output_path}")
        
        # Cleanup temp directories regardless of success
        for temp_dir in temp_dirs_to_cleanup:
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return True
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        # Ensure cleanup happens even on conversion failure
        for temp_dir in temp_dirs_to_cleanup:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to Markdown using Docling"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file to convert"
    )
    
    args = parser.parse_args()
    
    # Ask user for output path
    output_dir = get_output_path("raw/papers")
    
    # Convert the PDF
    success = convert_pdf_to_markdown(args.pdf_path, output_dir)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()