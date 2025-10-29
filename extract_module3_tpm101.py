#!/usr/bin/env python
"""
Extract Module 3 content from TPM 101 PDF and convert to Module 1 format
Creates rich HTML content with YITP styling for database storage
"""

import os
import sys
import json
import re
from datetime import datetime

try:
    import PyPDF2
    import pdfplumber
except ImportError:
    print("❌ Required packages not installed. Installing...")
    os.system("pip install PyPDF2 pdfplumber")
    import PyPDF2
    import pdfplumber

def extract_pdf_content(pdf_path):
    """Extract text content from PDF"""
    print(f"📄 Extracting content from: {pdf_path}")
    
    content_sections = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"📊 PDF has {len(pdf.pages)} pages")
            
            full_text = ""
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    full_text += f"\n--- PAGE {page_num} ---\n{text}\n"
            
            # Split content into modules/lessons
            # Look for patterns like "Module 1:", "Module 2:", etc.
            module_pattern = r'(?:Module|MODULE)\s+(\d+)[:\s]*([^\n]+)'
            modules = re.finditer(module_pattern, full_text, re.IGNORECASE)
            
            current_pos = 0
            module_sections = []
            
            for match in modules:
                if current_pos > 0:
                    # Save previous section
                    prev_content = full_text[current_pos:match.start()].strip()
                    if prev_content:
                        module_sections[-1]['content'] = prev_content
                
                module_num = match.group(1)
                module_title = match.group(2).strip()
                
                module_sections.append({
                    'number': int(module_num),
                    'title': module_title,
                    'content': '',
                    'start_pos': match.start()
                })
                
                current_pos = match.start()
            
            # Handle last section
            if module_sections and current_pos > 0:
                last_content = full_text[current_pos:].strip()
                module_sections[-1]['content'] = last_content
            
            # If no modules found, create sections based on page breaks
            if not module_sections:
                print("⚠️  No module patterns found, creating lessons from page content")
                pages_text = full_text.split("--- PAGE")
                for i, page_content in enumerate(pages_text[1:], 1):  # Skip first empty split
                    if page_content.strip():
                        module_sections.append({
                            'number': i,
                            'title': f"Lesson {i}: TPM 101 Content",
                            'content': page_content.strip(),
                            'start_pos': 0
                        })
            
            print(f"✅ Extracted {len(module_sections)} content sections")
            return module_sections, full_text
            
    except Exception as e:
        print(f"❌ Error extracting PDF: {str(e)}")
        return [], ""

def create_yitp_html_content(title, content, lesson_number):
    """Convert plain text to rich HTML with YITP styling"""
    
    # Clean and format content
    content = content.replace("---", "").strip()
    paragraphs = [p.strip() for p in content.split('\n') if p.strip()]
    
    # Create HTML structure following Module 1 pattern
    html_content = f'''<div class="yitp-lesson-content">
    <div class="container-fluid px-0">
        <!-- Lesson Header with YITP Branding -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card border-0 shadow-sm" style="background: linear-gradient(135deg, #1a2e53 0%, #ff5d15 100%);">
                    <div class="card-body text-white py-4">
                        <h1 class="display-6 fw-bold mb-0 text-center">
                            <i class="fas fa-brain me-3"></i>{title}
                        </h1>
                    </div>
                </div>
            </div>
        </div>

        <!-- Learning Objectives Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-target me-2"></i>Learning Objectives
                        </h3>
                    </div>
                    <div class="card-body">
                        <p class="mb-0">By the end of this lesson, you will be able to:</p>
                        <ul class="mt-2">
                            <li>Understand key concepts related to mindset and personal development</li>
                            <li>Apply TPM 101 principles to your daily life</li>
                            <li>Develop strategies for mindset transformation</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Content Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-book-open me-2"></i>Lesson Content
                        </h3>
                    </div>
                    <div class="card-body">'''
    
    # Add content paragraphs
    for paragraph in paragraphs[:10]:  # Limit to first 10 paragraphs for readability
        if len(paragraph) > 20:  # Only include substantial paragraphs
            # Check if it looks like a heading
            if paragraph.isupper() or (len(paragraph) < 100 and not paragraph.endswith('.')):
                html_content += f'\n                        <h4 class="mt-4 mb-3" style="color: #1a2e53;">{paragraph}</h4>'
            else:
                html_content += f'\n                        <p class="mb-3">{paragraph}</p>'
    
    html_content += '''
                    </div>
                </div>
            </div>
        </div>

        <!-- Key Takeaways Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-lightbulb me-2"></i>Key Takeaways
                        </h3>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-info border-0" style="background-color: #f8f9fa; border-left: 4px solid #ff5d15 !important;">
                            <p class="mb-2"><strong>Remember:</strong></p>
                            <ul class="mb-0">
                                <li>Mindset is the foundation of personal transformation</li>
                                <li>Small changes in thinking can lead to significant results</li>
                                <li>Consistent practice is key to developing new mental patterns</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Reflection Activity -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-pencil-alt me-2"></i>Reflection Activity
                        </h3>
                    </div>
                    <div class="card-body">
                        <p><strong>Take a moment to reflect:</strong></p>
                        <ol>
                            <li>What is one key insight you gained from this lesson?</li>
                            <li>How can you apply this concept in your daily life?</li>
                            <li>What specific action will you take this week to implement this learning?</li>
                        </ol>
                        <div class="mt-3 p-3" style="background-color: #f8f9fa; border-radius: 8px;">
                            <p class="mb-0"><em>Write your reflections in your learning journal or discuss with a study partner.</em></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>'''
    
    return html_content

def create_quiz_questions(lesson_title, lesson_number):
    """Create 5 quiz questions for each lesson"""
    
    base_questions = [
        {
            "question_text": f"What is the main focus of {lesson_title}?",
            "question_type": "multiple_choice",
            "options": [
                "Understanding mindset principles",
                "Physical fitness training", 
                "Financial planning",
                "Social media marketing"
            ],
            "correct_answer": "Understanding mindset principles",
            "points": 1,
            "explanation": "This lesson focuses on mindset development and personal transformation principles.",
            "sort_order": 1
        },
        {
            "question_text": "Mindset transformation requires consistent practice and application.",
            "question_type": "true_false",
            "correct_answer": "true",
            "points": 1,
            "explanation": "Consistent practice is essential for developing new mental patterns and habits.",
            "sort_order": 2
        },
        {
            "question_text": "Which of the following is a key component of personal development?",
            "question_type": "multiple_choice",
            "options": [
                "Self-awareness",
                "Ignoring feedback",
                "Avoiding challenges",
                "Staying in comfort zone"
            ],
            "correct_answer": "Self-awareness",
            "points": 1,
            "explanation": "Self-awareness is fundamental to personal growth and development.",
            "sort_order": 3
        },
        {
            "question_text": "The concepts learned in this lesson can be applied immediately in daily life.",
            "question_type": "true_false",
            "correct_answer": "true",
            "points": 1,
            "explanation": "TPM 101 principles are designed for practical, immediate application.",
            "sort_order": 4
        },
        {
            "question_text": "What is the most important factor in successful mindset change?",
            "question_type": "multiple_choice",
            "options": [
                "Expensive courses",
                "Consistent daily practice",
                "Perfect conditions",
                "Waiting for motivation"
            ],
            "correct_answer": "Consistent daily practice",
            "points": 1,
            "explanation": "Consistent daily practice is the most crucial factor in creating lasting mindset changes.",
            "sort_order": 5
        }
    ]
    
    return base_questions

def create_module3_json(sections):
    """Create Module 3 JSON structure following Module 1 format"""

    # Base JSON structure following yitp_seed_module1.json
    module3_json = {
        "course": {
            "title": "The Youth Impact Training Programme (YITP) — 9-Week Virtual Training",
            "slug": "yitp-9-week-virtual-training",
            "description": "Comprehensive youth development program focusing on purpose, initiative, and mindset transformation.",
            "learning_objectives": "Equip learners with essential life skills including purpose discovery, personal initiative, and mindset mastery for maximum impact.",
            "prerequisites": "None",
            "difficulty_level": "beginner",
            "estimated_duration": 800,  # Total duration for all modules
            "status": "in_review",
            "is_published": True,
            "is_featured": False,
            "enrollment_limit": 0,
            "price": 39.0,
            "instructor": 1,
            "category": 1
        },
        "modules": [
            {
                "id": "M3",
                "course_slug": "yitp-9-week-virtual-training",
                "title": "Module 3: TPM 101 – The Power of Mindset",
                "description": "Master the fundamentals of mindset transformation and develop the mental frameworks necessary for personal and professional success.",
                "sort_order": 3,
                "is_published": True,
                "unlock_criteria": {
                    "requires_payment": True,
                    "requires_module_completion": 2
                },
                "estimated_duration": 480  # 8 hours total
            }
        ],
        "lessons": []
    }

    # Create lessons from extracted sections
    for i, section in enumerate(sections, 1):
        lesson_title = f"Lesson {i}: {section['title']}"

        # Create rich HTML content
        html_content = create_yitp_html_content(lesson_title, section['content'], i)

        # Create quiz questions
        quiz_questions = create_quiz_questions(lesson_title, i)

        lesson = {
            "id": f"L3_{i}",
            "module_id": "M3",
            "title": lesson_title,
            "content_type": "text",
            "content": html_content,
            "video_url": "",
            "presentation_file": "",
            "sort_order": i,
            "is_published": True,
            "is_mandatory": True,
            "estimated_duration": 30,  # 30 minutes per lesson
            "learning_objectives": f"Master key concepts from {section['title']} and apply mindset principles to personal development.",
            "resources": [
                {
                    "title": f"Lesson {i} Reflection Guide",
                    "type": "text",
                    "url": ""
                }
            ],
            "assessment": {
                "quiz": {
                    "title": f"{lesson_title} Quiz",
                    "description": "Test your understanding of key mindset concepts from this lesson.",
                    "instructions": "Answer all questions. You need 70% to pass. You have 15 attempts.",
                    "max_attempts": 15,
                    "passing_score": 70,
                    "is_randomized": True,
                    "show_results": True,
                    "time_limit": None,
                    "is_published": True,
                    "questions": quiz_questions
                }
            }
        }

        module3_json["lessons"].append(lesson)

    return module3_json

def main():
    """Main extraction and conversion process"""

    print("🧠 MODULE 3: TPM 101 EXTRACTION SCRIPT")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    pdf_path = "courseunits/3. TPM 101 PDF Full Course.pdf"

    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return False

    # Extract content from PDF
    sections, full_text = extract_pdf_content(pdf_path)

    if not sections:
        print("❌ No content sections extracted from PDF")
        return False

    print(f"✅ Successfully extracted {len(sections)} sections")
    print()

    # Save full extracted text for reference
    with open("module3_extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(full_text)
    print("📄 Full extracted text saved to: module3_extracted_text.txt")

    # Create Module 3 JSON structure
    print("🔄 Converting to Module 3 JSON structure...")
    module3_json = create_module3_json(sections)

    # Save JSON file
    json_filename = "yitp_seed_module3.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(module3_json, f, indent=2, ensure_ascii=False)

    print(f"✅ Module 3 JSON created: {json_filename}")
    print(f"📊 Created {len(module3_json['lessons'])} lessons")
    print()

    # Display summary
    print("📋 MODULE 3 SUMMARY")
    print("=" * 30)
    for lesson in module3_json['lessons']:
        print(f"• {lesson['title']} ({lesson['estimated_duration']}min)")

    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Module 3 content extraction completed!")
    else:
        print("\n❌ Module 3 extraction failed!")
        sys.exit(1)
