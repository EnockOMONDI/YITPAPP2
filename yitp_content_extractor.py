#!/usr/bin/env python3
"""
YITP Content Extractor - Fresh Standalone System
Converts PDF and PPTX files into structured content for YITP LMS

Requirements:
pip install python-pptx pdfplumber pillow beautifulsoup4

Usage:
python yitp_content_extractor.py --input source_files/ --output course.json
"""

import json
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# PDF Processing
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("pdfplumber not available - PDF processing disabled")

# PPTX Processing
try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    logger.warning("python-pptx not available - PPTX processing disabled")

# DOCX Processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("python-docx not available - DOCX processing disabled")

# HTML Processing
try:
    from bs4 import BeautifulSoup
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logger.warning("beautifulsoup4 not available - HTML processing limited")


class YITPContentExtractor:
    """Fresh content extraction system for YITP LMS"""
    
    def __init__(self):
        self.extracted_content = []
        self.course_metadata = {
            'title': '',
            'description': '',
            'estimated_duration': 0,
            'total_lessons': 0,
            'extraction_date': datetime.now().isoformat()
        }
    
    def extract_from_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber not installed")
        
        logger.info(f"Extracting content from PDF: {file_path.name}")
        
        try:
            content = {
                'source_file': file_path.name,
                'file_type': 'pdf',
                'pages': [],
                'total_pages': 0,
                'extraction_success': True
            }
            
            with pdfplumber.open(file_path) as pdf:
                content['total_pages'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_data = {
                        'page_number': page_num,
                        'text_content': '',
                        'tables': [],
                        'images': [],
                        'has_content': False
                    }
                    
                    # Extract text with error handling
                    try:
                        text = page.extract_text()
                        if text and text.strip():
                            page_data['text_content'] = text.strip()
                            page_data['has_content'] = True
                    except Exception as e:
                        logger.warning(f"Text extraction failed for page {page_num}: {e}")
                        # Try alternative extraction method
                        try:
                            words = page.extract_words()
                            if words:
                                text = ' '.join([word['text'] for word in words])
                                page_data['text_content'] = text.strip()
                                page_data['has_content'] = True
                        except Exception as e2:
                            logger.warning(f"Alternative text extraction failed for page {page_num}: {e2}")

                    # Extract tables with error handling
                    try:
                        tables = page.extract_tables()
                        if tables:
                            page_data['tables'] = tables
                            page_data['has_content'] = True
                    except Exception as e:
                        logger.warning(f"Table extraction failed for page {page_num}: {e}")

                    # Extract image information with error handling
                    try:
                        images = page.images
                        if images:
                            page_data['images'] = []
                            for img in images:
                                img_data = {}
                                # Safely extract image properties
                                if hasattr(img, 'bbox') and img.bbox:
                                    img_data['bbox'] = img.bbox
                                if hasattr(img, 'width') and img.width:
                                    img_data['width'] = img.width
                                if hasattr(img, 'height') and img.height:
                                    img_data['height'] = img.height
                                if img_data:  # Only add if we got some data
                                    page_data['images'].append(img_data)
                            if page_data['images']:
                                page_data['has_content'] = True
                    except Exception as e:
                        logger.warning(f"Image extraction failed for page {page_num}: {e}")
                    
                    content['pages'].append(page_data)
            
            logger.info(f"Successfully extracted {content['total_pages']} pages from {file_path.name}")
            return content
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return {
                'source_file': file_path.name,
                'file_type': 'pdf',
                'extraction_success': False,
                'error': str(e)
            }
    
    def extract_from_pptx(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PowerPoint file"""
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx not installed")
        
        logger.info(f"Extracting content from PPTX: {file_path.name}")
        
        try:
            prs = Presentation(file_path)
            content = {
                'source_file': file_path.name,
                'file_type': 'pptx',
                'slides': [],
                'total_slides': len(prs.slides),
                'extraction_success': True
            }
            
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_data = {
                    'slide_number': slide_num,
                    'title': '',
                    'content_blocks': [],
                    'images': [],
                    'notes': '',
                    'has_content': False
                }
                
                # Extract text from shapes
                text_blocks = []
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and shape.text.strip():
                        text_content = shape.text.strip()
                        
                        # Try to identify title (usually first or largest text)
                        if not slide_data['title'] and (slide_num == 1 or len(text_content) < 100):
                            slide_data['title'] = text_content
                        else:
                            text_blocks.append(text_content)
                        
                        slide_data['has_content'] = True
                    
                    # Extract image information
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        slide_data['images'].append({
                            'shape_id': shape.shape_id,
                            'name': getattr(shape, 'name', f'image_{slide_num}'),
                            'position': {
                                'left': shape.left,
                                'top': shape.top,
                                'width': shape.width,
                                'height': shape.height
                            }
                        })
                        slide_data['has_content'] = True
                
                slide_data['content_blocks'] = text_blocks
                
                # Extract speaker notes
                if slide.has_notes_slide:
                    notes_slide = slide.notes_slide
                    if notes_slide.notes_text_frame:
                        notes_text = notes_slide.notes_text_frame.text.strip()
                        if notes_text:
                            slide_data['notes'] = notes_text
                            slide_data['has_content'] = True
                
                content['slides'].append(slide_data)
            
            logger.info(f"Successfully extracted {content['total_slides']} slides from {file_path.name}")
            return content
            
        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return {
                'source_file': file_path.name,
                'file_type': 'pptx',
                'extraction_success': False,
                'error': str(e)
            }

    def extract_from_docx(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from Word document file"""
        if not DOCX_AVAILABLE:
            raise ImportError("python-docx not installed")

        logger.info(f"Extracting content from DOCX: {file_path.name}")

        try:
            doc = Document(file_path)
            content = {
                'source_file': file_path.name,
                'file_type': 'docx',
                'sections': [],
                'total_paragraphs': len(doc.paragraphs),
                'extraction_success': True
            }

            current_section = {
                'section_number': 1,
                'title': '',
                'paragraphs': [],
                'tables': [],
                'has_content': False
            }

            # Extract paragraphs
            for para_num, paragraph in enumerate(doc.paragraphs, 1):
                para_text = paragraph.text.strip()
                if not para_text:
                    continue

                # Check if this looks like a heading/title
                is_heading = False
                if paragraph.style.name.startswith('Heading') or len(para_text) < 100:
                    # If we have content in current section, save it and start new one
                    if current_section['paragraphs'] and current_section['has_content']:
                        content['sections'].append(current_section)
                        current_section = {
                            'section_number': len(content['sections']) + 1,
                            'title': para_text,
                            'paragraphs': [],
                            'tables': [],
                            'has_content': False
                        }
                        is_heading = True
                    elif not current_section['title']:
                        current_section['title'] = para_text
                        is_heading = True

                if not is_heading:
                    current_section['paragraphs'].append({
                        'paragraph_number': para_num,
                        'text': para_text,
                        'style': paragraph.style.name
                    })
                    current_section['has_content'] = True

            # Add the last section if it has content
            if current_section['has_content']:
                content['sections'].append(current_section)

            # Extract tables
            for table_num, table in enumerate(doc.tables, 1):
                table_data = {
                    'table_number': table_num,
                    'rows': [],
                    'row_count': len(table.rows),
                    'column_count': len(table.columns) if table.rows else 0
                }

                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        row_data.append(cell_text)
                    table_data['rows'].append(row_data)

                # Add table to the last section or create a new one
                if content['sections']:
                    content['sections'][-1]['tables'].append(table_data)
                    content['sections'][-1]['has_content'] = True
                else:
                    # Create a section for tables if none exist
                    content['sections'].append({
                        'section_number': 1,
                        'title': 'Document Tables',
                        'paragraphs': [],
                        'tables': [table_data],
                        'has_content': True
                    })

            logger.info(f"Successfully extracted {len(content['sections'])} sections from {file_path.name}")
            return content

        except Exception as e:
            logger.error(f"Error extracting from {file_path}: {str(e)}")
            return {
                'source_file': file_path.name,
                'file_type': 'docx',
                'extraction_success': False,
                'error': str(e)
            }

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters that might break JSON
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Basic formatting preservation
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # Italic
        
        return text
    
    def structure_content(self, extracted_files: List[Dict]) -> List[Dict]:
        """Structure extracted content into logical units"""
        structured_content = []
        
        for file_data in extracted_files:
            if not file_data.get('extraction_success', False):
                logger.warning(f"Skipping failed extraction: {file_data.get('source_file', 'unknown')}")
                continue
            
            if file_data['file_type'] == 'pptx':
                # Process PPTX slides
                for slide in file_data.get('slides', []):
                    if slide.get('has_content', False):
                        content_unit = {
                            'source_file': file_data['source_file'],
                            'source_type': 'slide',
                            'source_number': slide['slide_number'],
                            'title': self.clean_text(slide.get('title', '')),
                            'content': [self.clean_text(block) for block in slide.get('content_blocks', [])],
                            'notes': self.clean_text(slide.get('notes', '')),
                            'has_images': len(slide.get('images', [])) > 0,
                            'image_count': len(slide.get('images', []))
                        }
                        structured_content.append(content_unit)
            
            elif file_data['file_type'] == 'pdf':
                # Process PDF pages
                for page in file_data.get('pages', []):
                    if page.get('has_content', False):
                        content_unit = {
                            'source_file': file_data['source_file'],
                            'source_type': 'page',
                            'source_number': page['page_number'],
                            'title': '',  # PDFs don't have clear titles per page
                            'content': [self.clean_text(page.get('text_content', ''))],
                            'notes': '',
                            'has_tables': len(page.get('tables', [])) > 0,
                            'table_count': len(page.get('tables', [])),
                            'has_images': len(page.get('images', [])) > 0,
                            'image_count': len(page.get('images', []))
                        }
                        structured_content.append(content_unit)

            elif file_data['file_type'] == 'docx':
                # Process DOCX sections
                for section in file_data.get('sections', []):
                    if section.get('has_content', False):
                        # Combine all paragraph text into content
                        content_text = []
                        for para in section.get('paragraphs', []):
                            content_text.append(self.clean_text(para.get('text', '')))

                        content_unit = {
                            'source_file': file_data['source_file'],
                            'source_type': 'section',
                            'source_number': section['section_number'],
                            'title': self.clean_text(section.get('title', '')),
                            'content': content_text,
                            'notes': '',
                            'has_tables': len(section.get('tables', [])) > 0,
                            'table_count': len(section.get('tables', [])),
                            'has_images': False,  # DOCX image extraction not implemented yet
                            'image_count': 0
                        }
                        structured_content.append(content_unit)
        
        logger.info(f"Structured {len(structured_content)} content units from {len(extracted_files)} files")
        return structured_content
    
    def process_file(self, file_path: Path) -> Dict:
        """Process a single file"""
        logger.info(f"Processing file: {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        if suffix == '.pdf':
            return self.extract_from_pdf(file_path)
        elif suffix == '.pptx':
            return self.extract_from_pptx(file_path)
        elif suffix == '.docx':
            return self.extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    def process_directory(self, input_dir: Path) -> List[Dict]:
        """Process all PDF, PPTX, and DOCX files in a directory"""
        logger.info(f"Processing directory: {input_dir}")

        # Find all relevant files
        pdf_files = list(input_dir.glob("*.pdf"))
        pptx_files = list(input_dir.glob("*.pptx"))
        docx_files = list(input_dir.glob("*.docx"))

        all_files = sorted(pdf_files) + sorted(pptx_files) + sorted(docx_files)

        if not all_files:
            logger.warning("No PDF, PPTX, or DOCX files found in input directory")
            return []

        logger.info(f"Found {len(pdf_files)} PDF files, {len(pptx_files)} PPTX files, and {len(docx_files)} DOCX files")

        extracted_files = []

        # Process each file
        for file_path in all_files:
            try:
                content = self.process_file(file_path)
                extracted_files.append(content)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                continue

        return extracted_files
    
    def generate_course_metadata(self, structured_content: List[Dict]) -> Dict:
        """Generate course metadata from structured content"""
        total_units = len(structured_content)
        
        # Estimate duration (rough calculation)
        estimated_minutes = total_units * 5  # 5 minutes per content unit
        
        # Try to extract course title from first content unit
        course_title = "Extracted Course Content"
        if structured_content and structured_content[0].get('title'):
            course_title = structured_content[0]['title']
        
        metadata = {
            'course_title': course_title,
            'total_content_units': total_units,
            'estimated_duration_minutes': estimated_minutes,
            'source_files': list(set([unit['source_file'] for unit in structured_content])),
            'extraction_timestamp': datetime.now().isoformat(),
            'content_types': list(set([unit['source_type'] for unit in structured_content]))
        }
        
        return metadata
    
    def save_extracted_content(self, output_file: Path, structured_content: List[Dict]) -> bool:
        """Save extracted content to JSON file"""
        try:
            metadata = self.generate_course_metadata(structured_content)
            
            output_data = {
                'metadata': metadata,
                'content_units': structured_content,
                'extraction_info': {
                    'extractor_version': '1.0.0',
                    'extraction_date': datetime.now().isoformat(),
                    'total_units': len(structured_content)
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Extracted content saved to: {output_file}")
            logger.info(f"Total content units: {len(structured_content)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving extracted content: {str(e)}")
            return False


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='YITP Content Extractor - Fresh System')
    parser.add_argument('--input', type=str, required=True,
                       help='Input directory or file (PDF/PPTX/DOCX)')
    parser.add_argument('--output', type=str, default='extracted_content.json',
                       help='Output JSON file name')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_path = Path(args.input)
    output_file = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return False

    # Create extractor and process files
    extractor = YITPContentExtractor()

    # Extract content from file(s)
    if input_path.is_file():
        # Process single file
        try:
            extracted_content = extractor.process_file(input_path)
            extracted_files = [extracted_content]
        except Exception as e:
            logger.error(f"Failed to process file {input_path}: {e}")
            return False
    elif input_path.is_dir():
        # Process directory
        extracted_files = extractor.process_directory(input_path)
    else:
        logger.error(f"Input path is neither a file nor directory: {input_path}")
        return False

    if not extracted_files:
        logger.error("No content extracted from input files")
        return False
    
    # Structure the content
    structured_content = extractor.structure_content(extracted_files)
    
    if not structured_content:
        logger.error("No structured content generated")
        return False
    
    # Save to output file
    success = extractor.save_extracted_content(output_file, structured_content)
    
    if success:
        logger.info("✅ Content extraction completed successfully!")
        logger.info(f"📁 Output file: {output_file}")
        logger.info(f"📊 Content units extracted: {len(structured_content)}")
        return True
    else:
        logger.error("❌ Content extraction failed")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
