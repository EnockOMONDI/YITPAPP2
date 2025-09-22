#!/usr/bin/env python3
"""
YITP JSON Builder - Fresh Schema Foundation
Converts extracted content into YITP LMS compatible JSON format

Usage:
python yitp_json_builder.py --input extracted_content.json --output yitp_course.json
"""

import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class YITPJSONBuilder:
    """Builds YITP LMS compatible JSON from extracted content"""
    
    def __init__(self):
        # YITP Brand Colors
        self.colors = {
            'primary_orange': '#ff5d15',
            'primary_blue': '#1a2e53',
            'secondary_blue': '#0c5460',
            'bg_yellow': '#fff8e1',
            'bg_blue': '#f0f8ff'
        }
        
        # Default course configuration
        self.course_defaults = {
            'difficulty_level': 'beginner',
            'category': 'Professional Development',
            'currency': 'USD',
            'price': 39.0,
            'status': 'draft'
        }
        
        # Quiz configuration
        self.quiz_defaults = {
            'passing_score': 70,
            'max_attempts': 15,
            'time_limit': None,
            'is_randomized': False,
            'show_results': True
        }
    
    def create_yitp_html_content(self, title: str, content_blocks: List[str], 
                                learning_objective: str = None) -> str:
        """Create YITP-styled HTML content"""
        
        html_parts = []
        
        # Main title with YITP styling
        html_parts.append(f'''<h2 style="color: {self.colors['primary_blue']}; border-bottom: 2px solid {self.colors['primary_orange']}; padding-bottom: 0.5rem;">{title}</h2>''')
        
        # Key takeaway box
        objective = learning_objective or "Understand and apply the key concepts presented in this lesson."
        html_parts.append(f'''<div style="background: {self.colors['bg_yellow']}; border-left: 4px solid {self.colors['primary_orange']}; padding: 1rem; margin: 1rem 0;">
<h4 style="color: {self.colors['primary_orange']}; margin-top: 0;">💡 Key Takeaway</h4>
<p><strong>Learning Objective:</strong> {objective}</p>
</div>''')
        
        # Process content blocks
        for i, content in enumerate(content_blocks):
            if not content.strip():
                continue
            
            # Check if this looks like a section header
            if len(content) < 100 and not content.endswith('.'):
                html_parts.append(f'''<h3 style="color: {self.colors['primary_orange']}; margin-top: 2rem;">{content}</h3>''')
            else:
                # Regular content paragraph
                formatted_content = self.format_text_content(content)
                html_parts.append(f"<p>{formatted_content}</p>")
        
        # Add activity section
        html_parts.append(f'''<div style="background: {self.colors['bg_blue']}; border: 2px solid {self.colors['primary_blue']}; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
<h4 style="color: {self.colors['primary_blue']}; margin-top: 0;">🎯 Activity</h4>
<p>Reflect on the concepts presented in this lesson and consider how you can apply them in your current situation or future goals.</p>
</div>''')
        
        return '\n'.join(html_parts)
    
    def format_text_content(self, text: str) -> str:
        """Format text content with basic HTML styling"""
        if not text:
            return ""
        
        # Clean up the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Basic formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)  # Italic
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)  # Underscore italic
        
        # Handle bullet points
        text = re.sub(r'^[-•]\s*', '', text, flags=re.MULTILINE)
        
        return text
    
    def generate_quiz_questions(self, lesson_title: str, content_blocks: List[str],
                              question_count: int = 5) -> List[Dict]:
        """Generate diverse quiz questions based on content with multiple question types"""

        questions = []

        # Define question type distribution (20% each for 5 types)
        question_types = [
            'true_false',
            'multiple_choice',
            'fill_in_blank',
            'multiple_select',
            'matching'
        ]

        # Ensure we have 4-6 questions, default to 5 for even distribution
        actual_count = min(max(question_count, 4), 6)

        # Create questions with diverse types
        for i in range(actual_count):
            question_type = question_types[i % len(question_types)]

            if question_type == 'true_false':
                question = self._generate_true_false_question(lesson_title, content_blocks, i + 1)
            elif question_type == 'multiple_choice':
                question = self._generate_multiple_choice_question(lesson_title, content_blocks, i + 1)
            elif question_type == 'fill_in_blank':
                question = self._generate_fill_in_blank_question(lesson_title, content_blocks, i + 1)
            elif question_type == 'multiple_select':
                question = self._generate_multiple_select_question(lesson_title, content_blocks, i + 1)
            elif question_type == 'matching':
                question = self._generate_matching_question(lesson_title, content_blocks, i + 1)

            questions.append(question)

        return questions

    def _generate_true_false_question(self, lesson_title: str, content_blocks: List[str], sort_order: int) -> Dict:
        """Generate a True/False question"""
        return {
            "question_text": f"The concepts presented in '{lesson_title}' provide practical value for personal and professional development.",
            "question_type": "true_false",
            "correct_answer": "true",
            "points": 2,
            "explanation": f"True. The lesson '{lesson_title}' covers important concepts that can be applied for growth and development.",
            "sort_order": sort_order
        }

    def _generate_multiple_choice_question(self, lesson_title: str, content_blocks: List[str], sort_order: int) -> Dict:
        """Generate a Multiple Choice question"""
        return {
            "question_text": f"Which of the following best describes the main focus of '{lesson_title}'?",
            "question_type": "multiple_choice",
            "correct_answer": "Providing practical knowledge and skills for personal development",
            "options": [
                "Providing practical knowledge and skills for personal development",
                "Theoretical concepts without practical application",
                "Historical information only",
                "Entertainment and casual reading"
            ],
            "points": 2,
            "explanation": f"The lesson focuses on providing practical knowledge and skills that can be applied for personal development.",
            "sort_order": sort_order
        }

    def _generate_fill_in_blank_question(self, lesson_title: str, content_blocks: List[str], sort_order: int) -> Dict:
        """Generate a Fill-in-the-Blank question"""
        return {
            "question_text": f"The primary objective of '{lesson_title}' is to help learners develop _______ skills and knowledge.",
            "question_type": "fill_in_blank",
            "correct_answer": "practical",
            "alternative_answers": ["applicable", "useful", "relevant", "actionable"],
            "points": 2,
            "explanation": f"The lesson focuses on developing practical skills and knowledge that can be applied in real-world situations.",
            "sort_order": sort_order,
            "case_sensitive": False
        }

    def _generate_multiple_select_question(self, lesson_title: str, content_blocks: List[str], sort_order: int) -> Dict:
        """Generate a Multiple Select (choose all that apply) question"""
        return {
            "question_text": f"Which of the following are key benefits of the concepts covered in '{lesson_title}'? (Select all that apply)",
            "question_type": "multiple_select",
            "correct_answers": [
                "Enhanced professional skills",
                "Improved problem-solving abilities",
                "Better career opportunities"
            ],
            "options": [
                "Enhanced professional skills",
                "Improved problem-solving abilities",
                "Better career opportunities",
                "Guaranteed immediate promotion",
                "Elimination of all workplace challenges"
            ],
            "points": 3,
            "explanation": f"The lesson provides benefits including enhanced skills, improved problem-solving, and better career opportunities. However, it doesn't guarantee promotions or eliminate all challenges.",
            "sort_order": sort_order,
            "partial_credit": True
        }

    def _generate_matching_question(self, lesson_title: str, content_blocks: List[str], sort_order: int) -> Dict:
        """Generate a Matching question"""
        return {
            "question_text": f"Match the following concepts from '{lesson_title}' with their appropriate applications:",
            "question_type": "matching",
            "pairs": [
                {"term": "Skill Development", "definition": "Continuous learning and practice"},
                {"term": "Goal Setting", "definition": "Defining clear objectives and outcomes"},
                {"term": "Self-Assessment", "definition": "Evaluating personal strengths and areas for improvement"},
                {"term": "Action Planning", "definition": "Creating specific steps to achieve objectives"}
            ],
            "points": 2,
            "explanation": f"Understanding the relationship between these concepts and their applications is essential for implementing the lessons from '{lesson_title}'.",
            "sort_order": sort_order
        }
    
    def create_lesson_structure(self, content_unit: Dict, lesson_number: int, 
                              estimated_duration: int = 60) -> Dict:
        """Create a lesson structure from content unit"""
        
        # Generate lesson title
        title = content_unit.get('title', '').strip()
        if not title:
            title = f"Lesson {lesson_number}: Content from {content_unit.get('source_file', 'Unknown')}"
        
        # Clean and prepare content
        content_blocks = [block for block in content_unit.get('content', []) if block.strip()]
        
        # Generate learning objective
        learning_objective = f"Understand and apply the key concepts and principles presented in {title}."
        
        # Create HTML content
        html_content = self.create_yitp_html_content(title, content_blocks, learning_objective)
        
        # Generate quiz
        quiz_questions = self.generate_quiz_questions(title, content_blocks)
        
        lesson = {
            "id": f"lesson_{lesson_number}",
            "title": title,
            "content_type": "enhanced",
            "estimated_duration": estimated_duration,
            "learning_objectives": learning_objective,
            "primary_content": html_content,
            "additional_resources": [
                {
                    "type": "document",
                    "title": f"{title} - Reference Material",
                    "url": "https://ucarecdn.com/placeholder-url/",
                    "description": f"Additional reference material for {title}"
                }
            ],
            "sort_order": lesson_number,
            "is_preview": lesson_number <= 2,  # First 2 lessons as preview
            "assessment": {
                "quiz": {
                    "title": f"{title} - Knowledge Check",
                    "description": "Test your understanding of the key concepts from this lesson",
                    "instructions": "Answer all questions based on the lesson content. You have 15 attempts to achieve the passing score of 70%.",
                    "time_limit": self.quiz_defaults['time_limit'],
                    "max_attempts": self.quiz_defaults['max_attempts'],
                    "passing_score": self.quiz_defaults['passing_score'],
                    "is_randomized": self.quiz_defaults['is_randomized'],
                    "show_results": self.quiz_defaults['show_results'],
                    "questions": quiz_questions
                }
            }
        }
        
        return lesson
    
    def organize_content_into_modules(self, content_units: List[Dict], 
                                    lessons_per_module: int = 6) -> List[Dict]:
        """Organize content units into modules with lessons"""
        
        modules = []
        current_module_lessons = []
        module_number = 1
        lesson_number = 1
        
        for content_unit in content_units:
            # Create lesson from content unit
            lesson = self.create_lesson_structure(content_unit, lesson_number)
            current_module_lessons.append(lesson)
            lesson_number += 1
            
            # Check if we should create a new module
            if len(current_module_lessons) >= lessons_per_module:
                module = self.create_module_structure(current_module_lessons, module_number)
                modules.append(module)
                
                current_module_lessons = []
                module_number += 1
        
        # Add remaining lessons as final module
        if current_module_lessons:
            module = self.create_module_structure(current_module_lessons, module_number)
            modules.append(module)
        
        return modules
    
    def create_module_structure(self, lessons: List[Dict], module_number: int) -> Dict:
        """Create module structure containing lessons"""
        
        total_duration = sum(lesson.get('estimated_duration', 60) for lesson in lessons)
        
        module = {
            "title": f"Module {module_number}: Core Concepts and Applications",
            "description": f"This module covers essential concepts and practical applications through {len(lessons)} comprehensive lessons.",
            "sort_order": module_number,
            "estimated_duration": total_duration,
            "lessons": lessons
        }
        
        return module
    
    def build_yitp_course_json(self, extracted_data: Dict, course_config: Dict = None) -> Dict:
        """Build complete YITP course JSON structure"""
        
        # Merge with default configuration
        config = {**self.course_defaults}
        if course_config:
            config.update(course_config)
        
        # Extract metadata and content
        metadata = extracted_data.get('metadata', {})
        content_units = extracted_data.get('content_units', [])
        
        if not content_units:
            raise ValueError("No content units found in extracted data")
        
        # Generate course title and description
        course_title = config.get('title') or metadata.get('course_title', 'Professional Development Course')
        course_description = config.get('description') or f"A comprehensive course covering essential concepts and practical applications for professional development."
        
        # Organize content into modules
        modules = self.organize_content_into_modules(content_units)
        
        # Calculate totals
        total_lessons = sum(len(module['lessons']) for module in modules)
        total_duration_minutes = sum(module['estimated_duration'] for module in modules)
        total_duration_hours = round(total_duration_minutes / 60, 1)
        
        # Build complete course structure
        course_json = {
            "session_id": str(uuid.uuid4()),
            "course_title": course_title,
            "course_description": course_description,
            "course_category": config['category'],
            "difficulty_level": config['difficulty_level'],
            "estimated_duration": total_duration_hours,
            "price": config['price'],
            "currency": config['currency'],
            "total_sessions": total_lessons,
            "modules": modules,
            "created_at": datetime.now().isoformat(),
            "status": config['status'],
            "generation_info": {
                "generator_version": "1.0.0",
                "source_files": metadata.get('source_files', []),
                "total_content_units": len(content_units),
                "generation_date": datetime.now().isoformat()
            }
        }
        
        return course_json
    
    def save_yitp_json(self, course_json: Dict, output_file: Path) -> bool:
        """Save YITP course JSON to file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(course_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"YITP course JSON saved to: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving YITP JSON: {str(e)}")
            return False


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description='YITP JSON Builder - Fresh Schema Foundation')
    parser.add_argument('--input', type=str, required=True,
                       help='Input JSON file with extracted content')
    parser.add_argument('--output', type=str, default='yitp_course.json',
                       help='Output YITP course JSON file')
    parser.add_argument('--title', type=str,
                       help='Course title (optional)')
    parser.add_argument('--description', type=str,
                       help='Course description (optional)')
    parser.add_argument('--price', type=float, default=39.0,
                       help='Course price (default: 39.0)')
    parser.add_argument('--category', type=str, default='Professional Development',
                       help='Course category (default: Professional Development)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    input_file = Path(args.input)
    output_file = Path(args.output)
    
    if not input_file.exists():
        logger.error(f"Input file does not exist: {input_file}")
        return False
    
    try:
        # Load extracted content
        with open(input_file, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        
        # Prepare course configuration
        course_config = {
            'price': args.price,
            'category': args.category
        }
        
        if args.title:
            course_config['title'] = args.title
        if args.description:
            course_config['description'] = args.description
        
        # Create JSON builder and build course
        builder = YITPJSONBuilder()
        course_json = builder.build_yitp_course_json(extracted_data, course_config)
        
        # Save YITP course JSON
        success = builder.save_yitp_json(course_json, output_file)
        
        if success:
            logger.info("✅ YITP course JSON generated successfully!")
            logger.info(f"📁 Output file: {output_file}")
            logger.info(f"📚 Modules: {len(course_json['modules'])}")
            logger.info(f"📖 Total lessons: {course_json['total_sessions']}")
            logger.info(f"⏱️ Duration: {course_json['estimated_duration']} hours")
            return True
        else:
            logger.error("❌ Failed to save YITP course JSON")
            return False
            
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
