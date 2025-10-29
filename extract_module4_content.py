#!/usr/bin/env python3
"""
Module 4 Content Extraction Script
Extracts content from HTML file and creates JSON structure for database import
"""

import os
import sys
import django
import json
import re
from bs4 import BeautifulSoup

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

def extract_lesson_content():
    """Extract lesson content from HTML file"""
    
    html_file = 'courseunits/Soft Skills for the streets content.html'
    
    print("=== Module 4 Content Extraction ===\n")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract CSS styles from head
        style_tags = soup.find_all('style')
        css_content = '\n'.join([style.get_text() for style in style_tags])
        
        # Find all valid pages and sort them
        pages = soup.find_all('div', {'data-page-no': True})
        valid_pages = []
        
        for page in pages:
            page_no = page.get('data-page-no')
            try:
                page_num = int(page_no)
                valid_pages.append((page_num, page))
            except (ValueError, TypeError):
                continue
        
        valid_pages.sort(key=lambda x: x[0])
        pages = [page for _, page in valid_pages]
        
        print(f"Processing {len(pages)} pages...")
        
        # Define lesson structure based on analysis
        lesson_structure = [
            {
                'lesson_number': 1,
                'title': 'Introduction to Soft Skills',
                'start_page': 1,
                'end_page': 5,
                'description': 'Overview of soft skills and their importance in personal and professional development.'
            },
            {
                'lesson_number': 2,
                'title': 'Core Soft Skills Overview',
                'start_page': 6,
                'end_page': 10,
                'description': 'Understanding problem solving, critical thinking, adaptability, communication, collaboration, and networking.'
            },
            {
                'lesson_number': 3,
                'title': 'Leadership Styles and Self-Awareness',
                'start_page': 11,
                'end_page': 15,
                'description': 'Identifying your leadership style and building self-awareness as a foundation for effective leadership.'
            },
            {
                'lesson_number': 4,
                'title': 'Strategic Planning and Goal Setting',
                'start_page': 16,
                'end_page': 20,
                'description': 'Understanding strategic planning, goal alignment, and accountability frameworks for personal and professional success.'
            },
            {
                'lesson_number': 5,
                'title': 'Critical Thinking and Problem Solving',
                'start_page': 21,
                'end_page': 25,
                'description': 'Developing critical thinking skills, problem-solving methodologies, and stress reduction techniques.'
            },
            {
                'lesson_number': 6,
                'title': 'Communication and Adaptability',
                'start_page': 26,
                'end_page': 30,
                'description': 'Cultivating flexibility in dynamic environments and improving communication skills for better relationships.'
            },
            {
                'lesson_number': 7,
                'title': 'Time Management and Decision Making',
                'start_page': 31,
                'end_page': 35,
                'description': 'Mastering time management techniques, priority setting, and effective decision-making frameworks.'
            },
            {
                'lesson_number': 8,
                'title': 'Emotional Intelligence Fundamentals',
                'start_page': 36,
                'end_page': 40,
                'description': 'Understanding emotional intelligence, self-awareness, and managing emotions in personal and professional contexts.'
            },
            {
                'lesson_number': 9,
                'title': 'Teamwork, Collaboration, and Networking',
                'start_page': 41,
                'end_page': 45,
                'description': 'Mastering teamwork, collaboration, negotiation, and networking skills for professional development.'
            },
            {
                'lesson_number': 10,
                'title': 'Practical Applications and Case Studies',
                'start_page': 46,
                'end_page': 49,
                'description': 'Real-world scenarios and practical applications of soft skills in various professional and personal contexts.'
            }
        ]
        
        # Extract content for each lesson
        lessons = []
        
        for lesson_info in lesson_structure:
            print(f"Extracting Lesson {lesson_info['lesson_number']}: {lesson_info['title']}")
            
            # Get pages for this lesson
            lesson_pages = []
            for page_num, page in valid_pages:
                if lesson_info['start_page'] <= page_num <= lesson_info['end_page']:
                    lesson_pages.append(page)
            
            # Extract HTML content for this lesson
            lesson_html = extract_lesson_html(lesson_pages, css_content, lesson_info)
            
            # Create lesson data structure
            lesson_data = {
                'lesson_number': lesson_info['lesson_number'],
                'title': lesson_info['title'],
                'description': lesson_info['description'],
                'content': lesson_html,
                'pages': f"{lesson_info['start_page']}-{lesson_info['end_page']}",
                'quiz_questions': create_quiz_questions(lesson_info)
            }
            
            lessons.append(lesson_data)
        
        return lessons
        
    except Exception as e:
        print(f"Error extracting content: {e}")
        import traceback
        traceback.print_exc()
        return []

def extract_lesson_html(lesson_pages, css_content, lesson_info):
    """Extract and format HTML content for a lesson"""
    
    # Create lesson HTML with YITP styling wrapper
    lesson_html = f'''
    <div class="lesson-content" style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div class="lesson-header" style="background: linear-gradient(135deg, #ff5d15, #1a2e53); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 24px; font-weight: bold;">{lesson_info['title']}</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 16px;">{lesson_info['description']}</p>
        </div>
        
        <div class="lesson-body" style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    '''
    
    # Add embedded CSS styles
    lesson_html += f'<style>{css_content}</style>\n'
    
    # Add each page's content
    for page in lesson_pages:
        page_content = str(page)
        # Clean up the page content but preserve all styling and images
        lesson_html += f'<div class="page-content">{page_content}</div>\n'
    
    # Close the lesson wrapper
    lesson_html += '''
        </div>
        
        <div class="lesson-footer" style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #ff5d15;">
            <p style="margin: 0; color: #666; font-style: italic;">
                Complete this lesson and take the quiz to continue to the next lesson.
            </p>
        </div>
    </div>
    '''
    
    return lesson_html

def create_quiz_questions(lesson_info):
    """Create quiz questions for each lesson"""
    
    # Base questions that can be adapted for each lesson
    questions = [
        {
            'question': f'What is the main focus of "{lesson_info["title"]}"?',
            'options': [
                'Technical skills development',
                lesson_info['description'][:50] + '...',
                'Hardware troubleshooting',
                'Software programming'
            ],
            'correct_answer': 1,
            'explanation': f'This lesson focuses on {lesson_info["description"].lower()}'
        },
        {
            'question': f'Which of the following best describes the key learning outcome of this lesson?',
            'options': [
                'Learning programming languages',
                'Understanding database management',
                lesson_info['description'][:60] + '...',
                'Network configuration'
            ],
            'correct_answer': 2,
            'explanation': f'The key learning outcome is {lesson_info["description"].lower()}'
        }
    ]
    
    # Add lesson-specific questions based on content
    if 'leadership' in lesson_info['title'].lower():
        questions.extend([
            {
                'question': 'What is the first step in identifying your leadership style?',
                'options': [
                    'Taking a personality test',
                    'Building self-awareness',
                    'Reading leadership books',
                    'Asking others for feedback'
                ],
                'correct_answer': 1,
                'explanation': 'Building self-awareness is the foundation for understanding your leadership style.'
            }
        ])
    elif 'emotional intelligence' in lesson_info['title'].lower():
        questions.extend([
            {
                'question': 'Emotional Intelligence (EI) refers to the ability to:',
                'options': [
                    'Solve mathematical problems',
                    'Recognize, understand, and manage emotions',
                    'Write computer programs',
                    'Analyze financial data'
                ],
                'correct_answer': 1,
                'explanation': 'EI is about recognizing, understanding, and managing our own emotions and those of others.'
            }
        ])
    elif 'communication' in lesson_info['title'].lower():
        questions.extend([
            {
                'question': 'Effective communication skills are important because they:',
                'options': [
                    'Help in technical troubleshooting',
                    'Improve relationships and collaboration',
                    'Increase computer processing speed',
                    'Reduce software bugs'
                ],
                'correct_answer': 1,
                'explanation': 'Effective communication improves relationships and enables better collaboration.'
            }
        ])
    
    # Ensure we have exactly 5 questions
    while len(questions) < 5:
        questions.append({
            'question': f'What is an important aspect covered in {lesson_info["title"]}?',
            'options': [
                'Technical specifications',
                'Practical application of concepts',
                'Hardware requirements',
                'Software installation'
            ],
            'correct_answer': 1,
            'explanation': 'This lesson emphasizes practical application of the concepts covered.'
        })
    
    return questions[:5]  # Return exactly 5 questions

if __name__ == "__main__":
    lessons = extract_lesson_content()
    
    if lessons:
        print(f"\n=== Extraction Complete ===")
        print(f"Successfully extracted {len(lessons)} lessons")
        
        # Save to JSON file
        output_file = 'yitp_seed_module4.json'
        
        module_data = {
            'module': {
                'title': 'Soft Skills for the Streets',
                'description': 'Essential soft skills for personal and professional development in real-world contexts.',
                'sort_order': 4,
                'is_published': True
            },
            'lessons': lessons
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(module_data, f, indent=2, ensure_ascii=False)
        
        print(f"Content saved to {output_file}")
        print("Ready for database import!")
    else:
        print("Failed to extract lessons")
