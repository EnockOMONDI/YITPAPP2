#!/usr/bin/env python
"""
Fix Module 3 structure to have 8 lessons instead of 17
Based on the TPM 101 course outline provided by the user
"""

import os
import sys
import json
from datetime import datetime

def create_corrected_module3_json():
    """Create corrected Module 3 JSON with 8 lessons following the course outline"""
    
    # Course outline structure - 8 modules should become 8 lessons
    lesson_structure = [
        {
            "title": "Introduction to Mindset and Its Impact",
            "duration": 60,  # 1 hour
            "description": "Understand what mindset is and why it matters. Learn about fixed vs. growth mindset and the influence of mindset on success and resilience.",
            "content_focus": "Fixed vs. Growth Mindset (Carol Dweck overview), Influence of mindset on success and resilience, Insights from Nelson Mandela"
        },
        {
            "title": "The Science of a Positive Mental Attitude",
            "duration": 60,  # 1 hour
            "description": "Explore the principles behind maintaining a positive outlook and the psychology of positivity.",
            "content_focus": "Napoleon Hill's Positive Mental Attitude concept, W. Clement Stone's Success through a PMA, The psychology of positivity and neuroplasticity"
        },
        {
            "title": "Building a Foundation for Positivity",
            "duration": 90,  # 1.5 hours
            "description": "Learn to build habits that support a positive mindset through self-discipline and daily affirmations.",
            "content_focus": "Zig Ziglar's Priming the Pump, Og Mandino's Scrolls, Gandhi's approach to intentional living"
        },
        {
            "title": "Overcoming Negative Thinking",
            "duration": 90,  # 1.5 hours
            "description": "Identify and counteract negative thought patterns using proven strategies and techniques.",
            "content_focus": "Napoleon Hill's Mastering Your Fears, Strategies from Success Afrika resources, Mother Teresa's example"
        },
        {
            "title": "Mindset in Action: Adversity and Growth",
            "duration": 90,  # 1.5 hours
            "description": "Apply a positive mindset in challenging situations and transform obstacles into opportunities.",
            "content_focus": "Nelson Mandela's resilience lessons, Gandhi's nonviolent resistance, Transforming obstacles into opportunities"
        },
        {
            "title": "Sustaining a Positive Mindset",
            "duration": 90,  # 1.5 hours
            "description": "Develop routines and environments that foster positivity and create supportive networks.",
            "content_focus": "Zig Ziglar's motivation strategies, W. Clement Stone's autosuggestion, Creating supportive networks"
        },
        {
            "title": "Inspiring Others through a Positive Mindset",
            "duration": 60,  # 1 hour
            "description": "Learn how to model and encourage positivity in others and create a ripple effect in communities.",
            "content_focus": "Mother Teresa's leadership through compassion, The ripple effect of positivity, Mentoring others"
        },
        {
            "title": "Reflection and Long-Term Strategies",
            "duration": 60,  # 1 hour
            "description": "Reflect on learnings and create a sustainable mindset growth plan for long-term success.",
            "content_focus": "Reviewing key lessons, Identifying long-term mindset goals, Leveraging ongoing resources"
        }
    ]

    # Base JSON structure
    module3_json = {
        "course": {
            "title": "The Youth Impact Training Programme (YITP) — 9-Week Virtual Training",
            "slug": "yitp-9-week-virtual-training",
            "description": "Comprehensive youth development program focusing on purpose, initiative, and mindset transformation.",
            "learning_objectives": "Equip learners with essential life skills including purpose discovery, personal initiative, and mindset mastery for maximum impact.",
            "prerequisites": "None",
            "difficulty_level": "beginner",
            "estimated_duration": 800,
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
                "estimated_duration": 600  # 10 hours total (sum of all lessons)
            }
        ],
        "lessons": []
    }

    # Create 8 proper lessons
    for i, lesson_info in enumerate(lesson_structure, 1):
        lesson_title = f"Lesson {i}: {lesson_info['title']}"
        
        # Create rich HTML content for each lesson
        html_content = create_lesson_html_content(lesson_title, lesson_info, i)
        
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
            "estimated_duration": lesson_info['duration'],
            "learning_objectives": f"Master key concepts from {lesson_info['title']} and apply mindset principles to personal development.",
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

def create_lesson_html_content(title, lesson_info, lesson_number):
    """Create rich HTML content for each lesson"""
    
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
                        <p class="text-center mt-2 mb-0 opacity-90">Duration: {lesson_info['duration']} minutes</p>
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
                        <p class="mb-2"><strong>By the end of this lesson, you will be able to:</strong></p>
                        <p class="mb-0">{lesson_info['description']}</p>
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
                    <div class="card-body">
                        <h4 class="mt-4 mb-3" style="color: #1a2e53;">Key Topics Covered:</h4>
                        <p class="mb-3">{lesson_info['content_focus']}</p>
                        
                        <div class="alert alert-primary border-0 mt-4" style="background-color: #f0f8ff; border-left: 4px solid #1a2e53 !important;">
                            <h5 class="alert-heading" style="color: #1a2e53;">
                                <i class="fas fa-lightbulb me-2"></i>Core Concept
                            </h5>
                            <p class="mb-0">This lesson focuses on practical application of mindset principles that can transform your personal and professional life through consistent practice and reflection.</p>
                        </div>
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
                                <li>Every challenge is an opportunity for growth and learning</li>
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
                            <li>How will you measure your progress in developing this mindset skill?</li>
                        </ol>
                        <div class="mt-3 p-3" style="background-color: #f8f9fa; border-radius: 8px;">
                            <p class="mb-0"><em>Write your reflections in your learning journal or discuss with a study partner. Share your insights in the course forum to inspire others.</em></p>
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
                "Understanding mindset principles and their practical application",
                "Physical fitness training", 
                "Financial planning strategies",
                "Social media marketing techniques"
            ],
            "correct_answer": "Understanding mindset principles and their practical application",
            "points": 1,
            "explanation": "This lesson focuses on mindset development and personal transformation principles that can be applied in daily life.",
            "sort_order": 1
        },
        {
            "question_text": "Mindset transformation requires consistent practice and application.",
            "question_type": "true_false",
            "correct_answer": "true",
            "points": 1,
            "explanation": "Consistent practice is essential for developing new mental patterns and creating lasting change in mindset.",
            "sort_order": 2
        },
        {
            "question_text": "Which of the following is a key component of developing a positive mindset?",
            "question_type": "multiple_choice",
            "options": [
                "Self-awareness and intentional practice",
                "Ignoring negative feedback",
                "Avoiding all challenges",
                "Staying in your comfort zone"
            ],
            "correct_answer": "Self-awareness and intentional practice",
            "points": 1,
            "explanation": "Self-awareness and intentional practice are fundamental to developing and maintaining a positive mindset.",
            "sort_order": 3
        },
        {
            "question_text": "The concepts learned in this lesson can be applied immediately in daily life.",
            "question_type": "true_false",
            "correct_answer": "true",
            "points": 1,
            "explanation": "TPM 101 principles are designed for practical, immediate application in personal and professional situations.",
            "sort_order": 4
        },
        {
            "question_text": "What is the most important factor in successful mindset transformation?",
            "question_type": "multiple_choice",
            "options": [
                "Expensive courses and certifications",
                "Consistent daily practice and reflection",
                "Perfect conditions and circumstances",
                "Waiting for external motivation"
            ],
            "correct_answer": "Consistent daily practice and reflection",
            "points": 1,
            "explanation": "Consistent daily practice and reflection are the most crucial factors in creating lasting mindset changes and personal growth.",
            "sort_order": 5
        }
    ]
    
    return base_questions

def main():
    """Main function to create corrected Module 3 structure"""
    
    print("🔧 MODULE 3 STRUCTURE FIX")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    print("🎯 Creating corrected Module 3 structure with 8 lessons...")
    
    # Create corrected JSON structure
    corrected_module3_json = create_corrected_module3_json()
    
    # Save corrected JSON file
    json_filename = "yitp_seed_module3_corrected.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(corrected_module3_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Corrected Module 3 JSON created: {json_filename}")
    print(f"📊 Created {len(corrected_module3_json['lessons'])} lessons (corrected from 17)")
    print()
    
    # Display summary
    print("📋 CORRECTED MODULE 3 SUMMARY")
    print("=" * 40)
    total_duration = 0
    for lesson in corrected_module3_json['lessons']:
        duration = lesson['estimated_duration']
        total_duration += duration
        print(f"• {lesson['title']} ({duration}min)")
    
    print(f"\n⏱️  Total Duration: {total_duration} minutes ({total_duration/60:.1f} hours)")
    print("🎉 Module 3 structure correction completed!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
