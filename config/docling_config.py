"""
Docling configuration settings for PDF conversion.
"""

import os
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

def create_accelerator_options() -> AcceleratorOptions:
    """
    Create accelerator options with optimal thread count.
    Uses 75% of available CPU cores to leave headroom for system.
    """
    cpu_count = os.cpu_count() or 4
    num_threads = max(1, int(cpu_count * 0.75))
    print(f"Detected {cpu_count} CPU cores, using {num_threads} threads")
    
    # AUTO detects best available: CUDA → MPS → XPU → CPU
    return AcceleratorOptions(
        device=AcceleratorDevice.AUTO,
        num_threads=num_threads
    )

def create_pipeline_options() -> PdfPipelineOptions:
    """
    Create PDF pipeline options with optimal settings.
    Enables OCR, table structure detection, and cell matching.
    """
    accelerator_options = create_accelerator_options()
    
    pipeline_options = PdfPipelineOptions()
    pipeline_options.accelerator_options = accelerator_options
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    
    return pipeline_options

def create_document_converter() -> DocumentConverter:
    """
    Create and configure DocumentConverter with pipeline options.
    """
    pipeline_options = create_pipeline_options()
    
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
