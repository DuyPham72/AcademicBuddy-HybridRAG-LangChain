import os
import torch
from functools import lru_cache
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions, AcceleratorDevice
from langchain_core.documents import Document

@lru_cache(maxsize=1)
def get_docling_converter():
    '''
    Set up the docling converter
    '''
    acc_opts = AcceleratorOptions(device=AcceleratorDevice.CUDA if torch.cuda.is_available() else AcceleratorDevice.AUTO)
    
    pipeline_opts = PdfPipelineOptions()
    pipeline_opts.accelerator_options = acc_opts
    pipeline_opts.do_ocr = False
    pipeline_opts.do_table_structure = True 

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_opts)}
    )
    return converter

def load_file_with_docling(file_path):
    '''
    Load file into the converter and export as Markdown format
    '''
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} not found.")

    try:
        converter = get_docling_converter()
        result = converter.convert(file_path)
        
        output_docs = []
        for page_num, _ in result.document.pages.items():
            text = result.document.export_to_markdown(page_no=page_num)
            
            output_docs.append(Document(
                page_content=text,
                metadata={
                    "source": file_path, 
                    "filename": os.path.basename(file_path),
                    "page_number": page_num
                }
            ))
        return output_docs

    except Exception as e:
        print(f"Docling Error: {e}")
        return []