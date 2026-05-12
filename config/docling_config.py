"""
Docling configuration settings for PDF conversion.
"""

import os
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions, CodeFormulaVlmOptions
from docling.datamodel.settings import settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.threaded_standard_pdf_pipeline import ThreadedStandardPdfPipeline

# Global performance tuning
# Note: On Mac, Formula Enrichment falls back to CPU due to MPS compatibility issues.
settings.perf.elements_batch_size = 8  # Higher throughput
settings.perf.page_batch_size = 4      # Page-level batching

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

def create_pipeline_options(generate_images: bool = True) -> ThreadedPdfPipelineOptions:
    """
    Create PDF pipeline options with optimal settings.
    Uses ThreadedPdfPipelineOptions for multi-stage parallel processing.

    Args:
        generate_images: Whether to extract images from the PDF
    """
    accelerator_options = create_accelerator_options()

    pipeline_options = ThreadedPdfPipelineOptions()
    pipeline_options.accelerator_options = accelerator_options
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True

    # Batch sizes for threaded pipeline
    pipeline_options.ocr_batch_size = 4
    pipeline_options.layout_batch_size = 4
    pipeline_options.table_batch_size = 4

    # Formula enrichment settings
    pipeline_options.do_formula_enrichment = True
    pipeline_options.code_formula_options = CodeFormulaVlmOptions.from_preset("granite_docling")

    # Image extraction settings
    pipeline_options.generate_page_images = generate_images
    pipeline_options.generate_picture_images = generate_images
    pipeline_options.images_scale = 2.0  # Higher scale for better quality

    return pipeline_options

def create_document_converter(generate_images: bool = True) -> DocumentConverter:
    """
    Create and configure DocumentConverter with pipeline options.

    Args:
        generate_images: Whether to extract images from the PDF
    """
    pipeline_options = create_pipeline_options(generate_images=generate_images)

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                pipeline_cls=ThreadedStandardPdfPipeline,
            )
        }
    )
