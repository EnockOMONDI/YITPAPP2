#!/usr/bin/env python3
"""
YITP Content Extraction System
Converts PDF and PPTX files into structured JSON for YITP LMS integration

Requirements:
pip install python-pptx pdfplumber beautifulsoup4 pillow

Usage:
python content_extraction_system.py --input-dir PI/ --output-file pi_training_module.json
"""

import json
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse

# PDF Processing
try:
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("Warning: pdfplumber not installed. PDF processing disabled.")

# PPTX Processing
try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    print("Warning: python-pptx not installed. PPTX processing disabled.")

# HTML Processing
try:
    from bs4 import BeautifulSoup
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    print("Warning: beautifulsoup4 not installed. HTML processing limited.")


class YITPContentExtractor:
    """Main content extraction class for YITP LMS"""
    
    def __init__(self):
        self.yitp_colors = {
            'primary_orange': '#ff5d15',
            'primary_blue': '#1a2e53',
            'secondary_blue': '#0c5460',
            'bg_yellow': '#fff8e1',
            'bg_blue': '#f0f8ff'
        }
        
        self.content_structure = {
            'session_id': str(uuid.uuid4()),
            'course_title': '',
            'course_description': '',
            'course_category': 'Personal Development',
            'difficulty_level': 'beginner',
            'estimated_duration': 10,
            'price': 39.0,
            'currency': 'USD',
            'weeks': 2,
            'total_sessions': 6,
            'modules': [],
            'created_at': datetime.now().isoformat(),
            'status': 'draft'
        }
    
    def extract_from_pptx(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PowerPoint file"""
        if not PPTX_AVAILABLE:
            raise ImportError("python-pptx not installed")
        
        try:
            prs = Presentation(file_path)
            extracted_content = {
                'file_name': file_path.name,
                'slide_count': len(prs.slides),
                'slides': []
            }
            
            for slide_num, slide in enumerate(prs.slides, 1):
                slide_content = {
                    'slide_number': slide_num,
                    'title': '',
                    'content': [],
                    'images': [],
                    'notes': ''
                }
                
                # Extract text from shapes
                for shape in slide.shapes:
                    if hasattr(shape, 'text') and shape.text.strip():
                        # Check if this is likely a title
                        if slide_num == 1 or len(shape.text) < 100:
                            if not slide_content['title']:
                                slide_content['title'] = shape.text.strip()
                            else:
                                slide_content['content'].append(shape.text.strip())
                        else:
                            slide_content['content'].append(shape.text.strip())
                    
                    # Extract images
                    if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                        slide_content['images'].append({
                            'shape_id': shape.shape_id,
                            'name': getattr(shape, 'name', f'image_{slide_num}'),
                            'position': {
                                'left': shape.left,
                                'top': shape.top,
                                'width': shape.width,
                                'height': shape.height
                            }
                        })
                
                # Extract speaker notes
                if slide.has_notes_slide:
                    notes_slide = slide.notes_slide
                    if notes_slide.notes_text_frame:
                        slide_content['notes'] = notes_slide.notes_text_frame.text.strip()
                
                extracted_content['slides'].append(slide_content)
            
            return extracted_content
            
        except Exception as e:
            print(f"Error extracting from {file_path}: {str(e)}")
            return {'error': str(e), 'file_name': file_path.name}
    
    def extract_from_pdf(self, file_path: Path) -> Dict[str, Any]:
        """Extract content from PDF file"""
        if not PDF_AVAILABLE:
            raise ImportError("pdfplumber not installed")
        
        try:
            extracted_content = {
                'file_name': file_path.name,
                'page_count': 0,
                'pages': []
            }
            
            with pdfplumber.open(file_path) as pdf:
                extracted_content['page_count'] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_content = {
                        'page_number': page_num,
                        'text': '',
                        'tables': [],
                        'images': []
                    }
                    
                    # Extract text
                    text = page.extract_text()
                    if text:
                        page_content['text'] = text.strip()
                    
                    # Extract tables
                    tables = page.extract_tables()
                    if tables:
                        page_content['tables'] = tables
                    
                    # Extract images (basic info)
                    images = page.images
                    if images:
                        page_content['images'] = [
                            {
                                'bbox': img['bbox'],
                                'width': img['width'],
                                'height': img['height']
                            } for img in images
                        ]
                    
                    extracted_content['pages'].append(page_content)
            
            return extracted_content
            
        except Exception as e:
            print(f"Error extracting from {file_path}: {str(e)}")
            return {'error': str(e), 'file_name': file_path.name}
    
    def structure_content_into_lessons(self, extracted_files: List[Dict], target_lessons: int = 6) -> List[Dict]:
        """Structure extracted content into logical lessons"""
        lessons = []
        
        # Combine all content
        all_content = []
        for file_data in extracted_files:
            if 'error' in file_data:
                continue
            
            if 'slides' in file_data:  # PPTX
                for slide in file_data['slides']:
                    all_content.append({
                        'type': 'slide',
                        'source_file': file_data['file_name'],
                        'title': slide['title'],
                        'content': slide['content'],
                        'slide_number': slide['slide_number']
                    })
            elif 'pages' in file_data:  # PDF
                for page in file_data['pages']:
                    all_content.append({
                        'type': 'page',
                        'source_file': file_data['file_name'],
                        'content': [page['text']],
                        'page_number': page['page_number']
                    })
        
        # Divide content into lessons
        content_per_lesson = len(all_content) // target_lessons
        remainder = len(all_content) % target_lessons
        
        lesson_titles = [
            "PI Foundations and Introduction",
            "PI Core Concepts and Principles", 
            "PI Application Methods and Tools",
            "PI Implementation Strategies",
            "PI Case Studies and Examples",
            "PI Assessment and Next Steps"
        ]
        
        start_idx = 0
        for i in range(target_lessons):
            # Calculate content for this lesson
            lesson_content_count = content_per_lesson + (1 if i < remainder else 0)
            end_idx = start_idx + lesson_content_count
            
            lesson_content = all_content[start_idx:end_idx]
            
            # Generate lesson
            lesson = self.create_lesson_structure(
                lesson_id=f"temp_{i+1}",
                title=f"Lesson {i+1}: {lesson_titles[i]}",
                content_items=lesson_content,
                sort_order=i+1,
                estimated_duration=60
            )
            
            lessons.append(lesson)
            start_idx = end_idx
        
        return lessons
    
    def create_lesson_structure(self, lesson_id: str, title: str, content_items: List[Dict], 
                              sort_order: int, estimated_duration: int = 60) -> Dict:
        """Create a lesson structure following YITP JSON schema"""
        
        # Combine content into HTML
        html_content = self.format_content_as_html(title, content_items)
        
        # Generate learning objectives
        learning_objectives = self.generate_learning_objectives(content_items)
        
        # Create quiz
        quiz = self.generate_quiz_for_lesson(title, content_items)
        
        lesson = {
            "id": lesson_id,
            "title": title,
            "content_type": "enhanced",
            "estimated_duration": estimated_duration,
            "learning_objectives": learning_objectives,
            "primary_content": html_content,
            "additional_resources": [
                {
                    "type": "document",
                    "title": f"{title} PDF Download",
                    "url": "https://ucarecdn.com/placeholder-url/",
                    "description": f"Complete {title} content in PDF format"
                }
            ],
            "sort_order": sort_order,
            "is_preview": False,
            "assessment": {
                "quiz": quiz
            }
        }
        
        return lesson
    
    def format_content_as_html(self, title: str, content_items: List[Dict]) -> str:
        """Format content items into YITP-styled HTML"""
        
        html_parts = []
        
        # Main title
        html_parts.append(f'''<h2 style="color: {self.yitp_colors['primary_blue']}; border-bottom: 2px solid {self.yitp_colors['primary_orange']}; padding-bottom: 0.5rem;">{title}</h2>''')
        
        # Key takeaway box
        html_parts.append(f'''<div style="background: {self.yitp_colors['bg_yellow']}; border-left: 4px solid {self.yitp_colors['primary_orange']}; padding: 1rem; margin: 1rem 0;">
<h4 style="color: {self.yitp_colors['primary_orange']}; margin-top: 0;">💡 Key Takeaway</h4>
<p><strong>Learning Objective:</strong> Understand and apply personal initiative principles in professional and personal contexts.</p>
</div>''')
        
        # Process content items
        for item in content_items:
            if item.get('title'):
                html_parts.append(f'''<h3 style="color: {self.yitp_colors['primary_orange']}; margin-top: 2rem;">{item['title']}</h3>''')
            
            for content_piece in item.get('content', []):
                if content_piece.strip():
                    # Clean and format content
                    formatted_content = self.clean_and_format_text(content_piece)
                    html_parts.append(f"<p>{formatted_content}</p>")
        
        # Add activity section
        html_parts.append(f'''<div style="background: {self.yitp_colors['bg_blue']}; border: 2px solid {self.yitp_colors['primary_blue']}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
<h4 style="color: {self.yitp_colors['primary_blue']}; margin-top: 0;">🎯 Activity</h4>
<p>Reflect on the concepts presented and consider how you can apply personal initiative principles in your current situation.</p>
</div>''')
        
        return '\n'.join(html_parts)
    
    def clean_and_format_text(self, text: str) -> str:
        """Clean and format text content"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Basic formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # Italic
        
        return text
    
    def generate_learning_objectives(self, content_items: List[Dict]) -> str:
        """Generate learning objectives based on content"""
        # This is a simplified version - in practice, you'd analyze content more deeply
        return "Understand key concepts of personal initiative, apply practical tools and methods, and develop implementation strategies for personal and professional growth."
    
    def generate_quiz_for_lesson(self, lesson_title: str, content_items: List[Dict]) -> Dict:
        """Generate quiz structure for a lesson"""
        
        # Extract key concepts for quiz questions
        quiz_questions = self.create_quiz_questions(lesson_title, content_items)
        
        quiz = {
            "title": f"{lesson_title} Knowledge Check",
            "description": "Test your understanding of key concepts from this lesson",
            "instructions": "Answer all questions based on the lesson content. You have 15 attempts to achieve the passing score of 70%.",
            "time_limit": None,
            "max_attempts": 15,
            "passing_score": 70,
            "is_randomized": False,
            "show_results": True,
            "questions": quiz_questions
        }
        
        return quiz
    
    def create_quiz_questions(self, lesson_title: str, content_items: List[Dict]) -> List[Dict]:
        """Create quiz questions based on content"""
        
        # This is a template - in practice, you'd analyze content to generate relevant questions
        questions = [
            {
                "question_text": f"The concepts presented in {lesson_title} are fundamental to personal initiative development.",
                "question_type": "true_false",
                "correct_answer": "true",
                "points": 2,
                "explanation": f"True. {lesson_title} covers essential concepts for developing personal initiative.",
                "sort_order": 1
            },
            {
                "question_text": f"Personal initiative principles discussed in this lesson can be applied in both professional and personal contexts.",
                "question_type": "true_false", 
                "correct_answer": "true",
                "points": 2,
                "explanation": "True. Personal initiative principles are versatile and applicable across various life domains.",
                "sort_order": 2
            },
            {
                "question_text": f"The strategies outlined in {lesson_title} require significant financial investment to implement.",
                "question_type": "true_false",
                "correct_answer": "false", 
                "points": 2,
                "explanation": "False. Most personal initiative strategies focus on mindset and behavior changes rather than financial investment.",
                "sort_order": 3
            },
            {
                "question_text": f"According to the lesson, personal initiative is primarily about taking action without planning.",
                "question_type": "true_false",
                "correct_answer": "false",
                "points": 2,
                "explanation": "False. Personal initiative involves both strategic planning and purposeful action.",
                "sort_order": 4
            }
        ]
        
        return questions
    
    def create_module_structure(self, lessons: List[Dict]) -> Dict:
        """Create module structure for Module 2"""
        
        module = {
            "title": "Personal Initiative (PI) Training",
            "description": "Advanced training in personal initiative development, implementation strategies, and practical application in professional and personal contexts.",
            "week": 2,
            "lessons": lessons
        }
        
        return module
    
    def process_files(self, input_directory: Path, output_file: Path) -> bool:
        """Main processing function"""
        
        print(f"🚀 Starting YITP Content Extraction from {input_directory}")
        
        # Find all relevant files
        pptx_files = list(input_directory.glob("*.pptx"))
        pdf_files = list(input_directory.glob("*.pdf"))
        
        if not pptx_files and not pdf_files:
            print("❌ No PPTX or PDF files found in input directory")
            return False
        
        print(f"📁 Found {len(pptx_files)} PPTX files and {len(pdf_files)} PDF files")
        
        # Extract content from all files
        extracted_files = []
        
        for pptx_file in sorted(pptx_files):
            print(f"📄 Processing {pptx_file.name}...")
            content = self.extract_from_pptx(pptx_file)
            extracted_files.append(content)
        
        for pdf_file in sorted(pdf_files):
            print(f"📄 Processing {pdf_file.name}...")
            content = self.extract_from_pdf(pdf_file)
            extracted_files.append(content)
        
        # Structure content into lessons
        print("🏗️ Structuring content into lessons...")
        lessons = self.structure_content_into_lessons(extracted_files, target_lessons=6)
        
        # Create module structure
        module = self.create_module_structure(lessons)
        
        # Update course structure
        self.content_structure['course_title'] = "Personal Initiative (PI) Training - Module 2"
        self.content_structure['course_description'] = "Advanced training module focusing on personal initiative development, practical implementation strategies, and real-world application of PI principles."
        self.content_structure['total_sessions'] = len(lessons)
        self.content_structure['modules'] = [module]
        
        # Save to JSON file
        print(f"💾 Saving structured content to {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.content_structure, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Content extraction completed successfully!")
        print(f"📊 Generated {len(lessons)} lessons from {len(extracted_files)} source files")
        
        return True


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='YITP Content Extraction System')
    parser.add_argument('--input-dir', type=str, default='PI/', 
                       help='Input directory containing PPTX/PDF files')
    parser.add_argument('--output-file', type=str, default='pi_training_module2.json',
                       help='Output JSON file name')
    parser.add_argument('--lessons', type=int, default=6,
                       help='Number of lessons to create')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)
    
    if not input_dir.exists():
        print(f"❌ Input directory {input_dir} does not exist")
        return
    
    # Create extractor and process files
    extractor = YITPContentExtractor()
    success = extractor.process_files(input_dir, output_file)
    
    if success:
        print(f"\n🎉 Success! Module 2 JSON created at: {output_file}")
        print(f"📋 Next steps:")
        print(f"   1. Review and edit the generated JSON content")
        print(f"   2. Upload any referenced files to Uploadcare")
        print(f"   3. Update resource URLs in the JSON")
        print(f"   4. Import into YITP LMS for testing")
    else:
        print(f"\n❌ Processing failed. Check error messages above.")


if __name__ == "__main__":
    main()
