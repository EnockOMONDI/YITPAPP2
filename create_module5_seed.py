#!/usr/bin/env python3
"""
Create Module 5 (ESBA) JSON seed file for database import
Converts extracted content to YITP database format
"""

import json
import os
from datetime import datetime

def create_module5_seed():
    """Create Module 5 seed file from extracted content"""
    
    print("=== CREATING MODULE 5 SEED FILE ===")
    
    # Load extracted content
    try:
        with open('module5_esba_extracted.json', 'r', encoding='utf-8') as f:
            extracted_lessons = json.load(f)
        print(f"✅ Loaded {len(extracted_lessons)} extracted lessons")
    except FileNotFoundError:
        print("❌ Error: module5_esba_extracted.json not found. Run extract_module5_esba.py first.")
        return None
    
    # Module 5 seed structure
    seed_data = {
        "module": {
            "title": "Entrepreneurship & Small Business Administration (ESBA)",
            "description": "Comprehensive training on starting, building, managing, and sustaining successful businesses. Covers ideation, business planning, financing, operations, and long-term sustainability strategies.",
            "sort_order": 5,
            "is_published": True,
            "estimated_duration": 325,  # Total duration in minutes
            "created_at": datetime.now().isoformat()
        },
        "lessons": [],
        "quizzes": [],
        "questions": []
    }
    
    lesson_id_counter = 1
    quiz_id_counter = 1
    question_id_counter = 1
    
    # Process each extracted lesson
    for lesson_data in extracted_lessons:
        lesson_number = lesson_data['lesson_number']
        
        # Create lesson
        lesson = {
            "id": lesson_id_counter,
            "title": lesson_data['title'],
            "content_type": "text",
            "content": lesson_data['content'],
            "learning_objectives": f"By the end of this lesson, you will be able to:\n" + 
                                 "\n".join([f"• Understand {section.lower()}" for section in lesson_data['sections']]),
            "resources": {
                "additional_reading": [],
                "external_links": [],
                "downloadable_files": []
            },
            "sort_order": lesson_number,
            "estimated_duration": lesson_data['estimated_duration'],
            "is_published": True,
            "created_at": datetime.now().isoformat()
        }
        
        seed_data["lessons"].append(lesson)
        
        # Create quiz for this lesson
        quiz = {
            "id": quiz_id_counter,
            "lesson_id": lesson_id_counter,
            "title": f"{lesson_data['title']} - Knowledge Check",
            "description": f"Test your understanding of the key concepts covered in {lesson_data['title']}.",
            "passing_score": 70,
            "time_limit": 15,  # 15 minutes
            "max_attempts": 3,
            "is_published": True,
            "created_at": datetime.now().isoformat()
        }
        
        seed_data["quizzes"].append(quiz)
        
        # Create questions for this quiz
        for question_data in lesson_data['quiz_questions']:
            question = {
                "id": question_id_counter,
                "quiz_id": quiz_id_counter,
                "question_text": question_data['question'],
                "question_type": "multiple_choice",
                "options": question_data['options'],
                "correct_answer": question_data['correct_answer'],
                "explanation": question_data['explanation'],
                "points": 20,  # 5 questions × 20 points = 100 points total
                "created_at": datetime.now().isoformat()
            }
            
            seed_data["questions"].append(question)
            question_id_counter += 1
        
        lesson_id_counter += 1
        quiz_id_counter += 1
    
    # Save seed file
    output_file = 'yitp_seed_module5.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(seed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Module 5 seed file created: {output_file}")
    print(f"📊 Summary:")
    print(f"   • Module: {seed_data['module']['title']}")
    print(f"   • Lessons: {len(seed_data['lessons'])}")
    print(f"   • Quizzes: {len(seed_data['quizzes'])}")
    print(f"   • Questions: {len(seed_data['questions'])}")
    print(f"   • Total Duration: {seed_data['module']['estimated_duration']} minutes")
    
    return seed_data

def main():
    seed_data = create_module5_seed()
    if seed_data:
        print("\n🎯 Next step: Run import_module5_database.py to import into database")
    else:
        print("\n❌ Failed to create seed file")

if __name__ == "__main__":
    main()
