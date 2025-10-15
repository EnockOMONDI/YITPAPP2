#!/usr/bin/env python3
"""
Module 2 Complete Phase 1 Implementation
========================================

Creates all 5 lessons for Module 2 Phase 1 (Personal Initiative & Assessments)
following the proven approach from Lesson 1.
"""

import json
import os
from datetime import datetime
from analyze_module2_html import Module2HTMLAnalyzer

class Module2Phase1Creator:
    def __init__(self):
        self.analyzer = Module2HTMLAnalyzer()
        self.lessons_data = []
        
        # Define all 5 lessons for Phase 1
        self.lesson_definitions = [
            {
                'lesson_number': 1,
                'id': 118,
                'title': 'Lesson 1 – Personal Initiative Fundamentals (1 hour)',
                'slides': (1, 9),
                'duration': 60,
                'objectives': 'Understand the concept of Personal Initiative; Identify key characteristics of proactive behavior; Recognize the importance of self-directed action in personal and professional development',
                'description': 'foundational concepts of Personal Initiative and learn how proactive behavior can transform your personal and professional life'
            },
            {
                'lesson_number': 2,
                'id': 119,
                'title': 'Lesson 2 – Future Orientation (1.25 hours)',
                'slides': (10, 20),
                'duration': 75,
                'objectives': 'Develop future-oriented thinking skills; Learn to anticipate challenges and opportunities; Practice long-term planning techniques; Master strategic thinking approaches',
                'description': 'future-oriented thinking and strategic planning skills essential for effective Personal Initiative'
            },
            {
                'lesson_number': 3,
                'id': 120,
                'title': 'Lesson 3 – Opportunity Scanning (1.17 hours)',
                'slides': (21, 31),
                'duration': 70,
                'objectives': 'Master opportunity identification techniques; Develop environmental scanning skills; Learn to evaluate potential opportunities; Practice systematic opportunity assessment',
                'description': 'systematic approaches to identifying and evaluating opportunities in your environment'
            },
            {
                'lesson_number': 4,
                'id': 121,
                'title': 'Lesson 4 – SMART-PI Goals (1.08 hours)',
                'slides': (32, 39),
                'duration': 65,
                'objectives': 'Understand SMART-PI goal framework; Practice setting effective personal initiative goals; Learn goal tracking and adjustment techniques; Master goal achievement strategies',
                'description': 'SMART-PI goal framework and learn to set, track, and achieve meaningful personal initiative goals'
            },
            {
                'lesson_number': 5,
                'id': 122,
                'title': 'Lesson 5 – Internal Barriers I (1.33 hours)',
                'slides': (40, 55),
                'duration': 80,
                'objectives': 'Identify internal barriers to personal initiative; Develop strategies to overcome mental obstacles; Build self-awareness and confidence; Practice barrier removal techniques',
                'description': 'internal barriers that limit personal initiative and develop practical strategies to overcome them'
            }
        ]

    def generate_enhanced_quiz_questions(self, lesson_number, lesson_title):
        """Generate comprehensive quiz questions for each lesson"""
        
        question_sets = {
            1: [  # Personal Initiative Fundamentals
                {
                    "question_text": "What is the primary characteristic of Personal Initiative?",
                    "question_type": "multiple_choice",
                    "options": ["Reactive behavior", "Proactive self-starting behavior", "Following instructions", "Waiting for direction"],
                    "correct_answer": "Proactive self-starting behavior",
                    "explanation": "Personal Initiative is fundamentally about being proactive and self-starting rather than reactive.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "Personal Initiative requires taking action without being told what to do.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "Personal Initiative is characterized by self-starting behavior and taking action without explicit direction.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "List three key benefits of developing Personal Initiative in your career.",
                    "question_type": "short_answer",
                    "correct_answer": "Sample answers: Increased job satisfaction, better career advancement opportunities, improved problem-solving skills, greater autonomy, enhanced leadership potential",
                    "explanation": "Personal Initiative leads to numerous career benefits including advancement opportunities and increased satisfaction.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which of the following best describes a person with high Personal Initiative?",
                    "question_type": "multiple_choice",
                    "options": ["Waits for clear instructions", "Takes action to improve situations", "Avoids responsibility", "Follows established routines only"],
                    "correct_answer": "Takes action to improve situations",
                    "explanation": "High Personal Initiative involves actively seeking to improve situations and taking responsibility for outcomes.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Describe a situation where you demonstrated Personal Initiative and explain the outcome.",
                    "question_type": "short_answer",
                    "correct_answer": "Answers should include: identification of an opportunity or problem, self-directed action taken, positive outcome achieved, reflection on learning",
                    "explanation": "Personal examples help reinforce understanding and application of Personal Initiative concepts.",
                    "points": 2,
                    "sort_order": 5
                }
            ],
            2: [  # Future Orientation
                {
                    "question_text": "Future orientation in Personal Initiative means:",
                    "question_type": "multiple_choice",
                    "options": ["Living in the future", "Planning and anticipating future needs", "Ignoring present challenges", "Predicting exact outcomes"],
                    "correct_answer": "Planning and anticipating future needs",
                    "explanation": "Future orientation involves strategic thinking and planning for anticipated future needs and opportunities.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "Long-term thinking is more important than short-term action in Personal Initiative.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "False",
                    "explanation": "Both long-term thinking and short-term action are important; Personal Initiative requires balancing future planning with present action.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "What are the key components of effective future-oriented planning?",
                    "question_type": "short_answer",
                    "correct_answer": "Key components include: environmental scanning, trend analysis, scenario planning, goal setting, risk assessment, contingency planning",
                    "explanation": "Effective future planning requires systematic analysis and preparation for multiple scenarios.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which technique is most effective for developing future orientation?",
                    "question_type": "multiple_choice",
                    "options": ["Reactive problem-solving", "Scenario planning", "Historical analysis only", "Intuitive guessing"],
                    "correct_answer": "Scenario planning",
                    "explanation": "Scenario planning helps develop future orientation by considering multiple possible futures and preparing accordingly.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Create a 5-year vision for your career development including specific milestones.",
                    "question_type": "short_answer",
                    "correct_answer": "Answers should include: clear long-term vision, specific measurable milestones, timeline, skill development plans, potential challenges and solutions",
                    "explanation": "Creating a detailed career vision demonstrates future-oriented thinking and planning skills.",
                    "points": 2,
                    "sort_order": 5
                }
            ],
            3: [  # Opportunity Scanning
                {
                    "question_text": "Opportunity scanning involves:",
                    "question_type": "multiple_choice",
                    "options": ["Waiting for opportunities to appear", "Systematically searching for potential opportunities", "Only focusing on obvious opportunities", "Avoiding risky situations"],
                    "correct_answer": "Systematically searching for potential opportunities",
                    "explanation": "Opportunity scanning is a proactive, systematic approach to identifying potential opportunities in the environment.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "Environmental scanning should only focus on your immediate work environment.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "False",
                    "explanation": "Effective environmental scanning considers multiple environments including industry, market, technological, and social contexts.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "What are the main sources of information for effective opportunity scanning?",
                    "question_type": "short_answer",
                    "correct_answer": "Sources include: industry reports, market research, networking, customer feedback, competitor analysis, technology trends, regulatory changes",
                    "explanation": "Comprehensive opportunity scanning requires diverse information sources to identify emerging opportunities.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which factor is most important when evaluating an identified opportunity?",
                    "question_type": "multiple_choice",
                    "options": ["Personal interest only", "Alignment with goals and capabilities", "Immediate financial gain", "Popularity with others"],
                    "correct_answer": "Alignment with goals and capabilities",
                    "explanation": "The best opportunities align with your goals, skills, and capabilities while offering meaningful value.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Identify an opportunity in your current environment and explain how you would evaluate its potential.",
                    "question_type": "short_answer",
                    "correct_answer": "Answers should include: opportunity description, evaluation criteria, resource requirements, potential benefits, risks assessment, action plan",
                    "explanation": "Practical application of opportunity identification and evaluation skills demonstrates understanding.",
                    "points": 2,
                    "sort_order": 5
                }
            ],
            4: [  # SMART-PI Goals
                {
                    "question_text": "What does the 'PI' in SMART-PI goals stand for?",
                    "question_type": "multiple_choice",
                    "options": ["Personal Interest", "Personal Initiative", "Professional Integration", "Practical Implementation"],
                    "correct_answer": "Personal Initiative",
                    "explanation": "SMART-PI goals specifically incorporate Personal Initiative principles into the traditional SMART goal framework.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "SMART-PI goals should always be achievable within one year.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "False",
                    "explanation": "SMART-PI goals can have various timeframes depending on their scope and complexity, from short-term to long-term objectives.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "What are the key differences between traditional SMART goals and SMART-PI goals?",
                    "question_type": "short_answer",
                    "correct_answer": "SMART-PI goals emphasize: proactive behavior, self-starting action, future orientation, opportunity focus, barrier anticipation, personal responsibility",
                    "explanation": "SMART-PI goals integrate Personal Initiative principles with traditional goal-setting frameworks.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which element is essential for effective SMART-PI goal tracking?",
                    "question_type": "multiple_choice",
                    "options": ["Daily reporting to supervisor", "Regular self-assessment and adjustment", "Waiting for annual reviews", "Focusing only on final outcomes"],
                    "correct_answer": "Regular self-assessment and adjustment",
                    "explanation": "SMART-PI goals require ongoing self-monitoring and proactive adjustments to maintain effectiveness.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Create a SMART-PI goal for developing a new skill and explain how it incorporates Personal Initiative principles.",
                    "question_type": "short_answer",
                    "correct_answer": "Goal should include: Specific skill, Measurable progress indicators, Achievable steps, Relevant to career/life, Time-bound, plus Personal Initiative elements like self-starting action and future orientation",
                    "explanation": "Practical application of SMART-PI goal setting demonstrates understanding of both frameworks.",
                    "points": 2,
                    "sort_order": 5
                }
            ],
            5: [  # Internal Barriers I
                {
                    "question_text": "Internal barriers to Personal Initiative are:",
                    "question_type": "multiple_choice",
                    "options": ["External obstacles beyond your control", "Mental and emotional obstacles within yourself", "Physical limitations only", "Organizational policies"],
                    "correct_answer": "Mental and emotional obstacles within yourself",
                    "explanation": "Internal barriers are psychological, emotional, and mental obstacles that limit your ability to take initiative.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "Fear of failure is always a negative barrier that should be completely eliminated.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "False",
                    "explanation": "While excessive fear can be limiting, healthy concern about failure can motivate better preparation and risk assessment.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "What are the most common internal barriers to Personal Initiative?",
                    "question_type": "short_answer",
                    "correct_answer": "Common barriers include: fear of failure, perfectionism, lack of confidence, negative self-talk, comfort zone attachment, analysis paralysis, imposter syndrome",
                    "explanation": "Understanding common internal barriers helps in developing targeted strategies to overcome them.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which strategy is most effective for overcoming internal barriers?",
                    "question_type": "multiple_choice",
                    "options": ["Ignoring the barriers", "Gradual exposure and skill building", "Waiting for motivation", "Avoiding challenging situations"],
                    "correct_answer": "Gradual exposure and skill building",
                    "explanation": "Systematic, gradual exposure combined with skill development is the most effective approach to overcoming internal barriers.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Identify your biggest internal barrier to Personal Initiative and create a plan to address it.",
                    "question_type": "short_answer",
                    "correct_answer": "Plan should include: barrier identification, root cause analysis, specific strategies, practice opportunities, progress measurement, support systems",
                    "explanation": "Personal application of barrier removal techniques demonstrates practical understanding and commitment to growth.",
                    "points": 2,
                    "sort_order": 5
                }
            ]
        }
        
        return question_sets.get(lesson_number, [])

    def create_lesson_json(self, lesson_def):
        """Create complete JSON structure for a lesson"""
        print(f"\n📖 CREATING LESSON {lesson_def['lesson_number']}: {lesson_def['title']}")
        print("=" * 60)
        
        # Extract lesson content
        start_slide, end_slide = lesson_def['slides']
        lesson_content = self.analyzer.extract_lesson_content(
            lesson_def['lesson_number'], start_slide, end_slide
        )
        
        if not lesson_content:
            print(f"❌ Failed to extract content for lesson {lesson_def['lesson_number']}")
            return None
        
        # Generate quiz questions
        quiz_questions = self.generate_enhanced_quiz_questions(
            lesson_def['lesson_number'], lesson_def['title']
        )
        
        if not quiz_questions:
            print(f"❌ Failed to generate quiz for lesson {lesson_def['lesson_number']}")
            return None
        
        # Create lesson JSON structure
        lesson_json = {
            "id": lesson_def['id'],
            "title": lesson_def['title'],
            "content_type": "text",
            "learning_objectives": lesson_def['objectives'],
            "estimated_duration": lesson_def['duration'],
            "sort_order": lesson_def['lesson_number'],
            "is_published": True,
            "is_mandatory": True,
            "content": self._create_enhanced_content_wrapper(
                lesson_content['html_content'], 
                lesson_def
            ),
            "assessment": {
                "quiz": {
                    "id": lesson_def['id'],
                    "title": f"Lesson {lesson_def['lesson_number']} Quiz",
                    "lesson_id": lesson_def['id'],
                    "passing_score": 70,
                    "max_attempts": 15,
                    "time_limit": None,
                    "is_published": True,
                    "questions": quiz_questions
                }
            }
        }
        
        print(f"✅ Lesson {lesson_def['lesson_number']} JSON created")
        print(f"📄 Slides: {start_slide}-{end_slide} ({lesson_content['pages_extracted']} pages)")
        print(f"📝 Content size: {len(lesson_json['content']):,} characters")
        print(f"❓ Quiz questions: {len(quiz_questions)}")
        
        return lesson_json

    def _create_enhanced_content_wrapper(self, html_content, lesson_def):
        """Create enhanced YITP content wrapper for each lesson"""
        
        lesson_titles = {
            1: "Personal Initiative Fundamentals",
            2: "Future Orientation",
            3: "Opportunity Scanning", 
            4: "SMART-PI Goals",
            5: "Internal Barriers I"
        }
        
        lesson_title = lesson_titles.get(lesson_def['lesson_number'], f"Lesson {lesson_def['lesson_number']}")
        
        wrapper = f'''<div class="yitp-lesson-content">
    <div class="lesson-header mb-4">
        <div class="alert alert-info">
            <h4><i class="fas fa-lightbulb me-2" style="color: #ff5d15;"></i>{lesson_title}</h4>
            <p class="mb-0">In this lesson, you'll explore {lesson_def['description']}.</p>
        </div>
    </div>
    
    <div class="lesson-content-wrapper">
        <style>
        .yitp-lesson-content {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        .yitp-lesson-content .module2-personal-initiative {{
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: 20px 0;
        }}
        
        .yitp-lesson-content .lesson-slide {{
            margin: 30px 0;
            padding: 20px;
            border-left: 4px solid #ff5d15;
            background: #f8f9fa;
            border-radius: 0 8px 8px 0;
        }}
        
        .yitp-lesson-content .pf {{
            position: relative;
            margin: 15px 0;
            background: white;
            border-radius: 4px;
            overflow: hidden;
        }}
        
        .yitp-lesson-content .pc {{
            position: relative;
            padding: 10px;
        }}
        
        .yitp-lesson-content .t {{
            position: absolute;
            white-space: pre;
            font-size: 14px;
            line-height: 1.4;
        }}
        
        /* Responsive adjustments */
        @media (max-width: 768px) {{
            .yitp-lesson-content .lesson-slide {{
                margin: 15px 0;
                padding: 15px;
            }}
            
            .yitp-lesson-content .t {{
                font-size: 12px;
                position: relative !important;
                white-space: normal !important;
            }}
        }}
        
        /* YITP brand colors */
        .yitp-lesson-content .highlight {{
            background-color: #ff5d15;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        
        .yitp-lesson-content .secondary-highlight {{
            background-color: #1a2e53;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        </style>
        
        {html_content}
    </div>
    
    <div class="lesson-footer mt-4">
        <div class="alert alert-success">
            <h5><i class="fas fa-check-circle me-2" style="color: #28a745;"></i>Lesson Complete</h5>
            <p class="mb-0">You have completed the {lesson_title} lesson. Take the quiz below to test your understanding and proceed to the next lesson.</p>
        </div>
    </div>
</div>'''
        
        return wrapper

    def create_all_lessons(self):
        """Create all 5 lessons for Phase 1"""
        print("🚀 MODULE 2 PHASE 1 COMPLETE IMPLEMENTATION")
        print("=" * 70)
        
        all_lessons = []
        
        for lesson_def in self.lesson_definitions:
            lesson_json = self.create_lesson_json(lesson_def)
            if lesson_json:
                all_lessons.append(lesson_json)
            else:
                print(f"❌ Failed to create lesson {lesson_def['lesson_number']}")
                return None
        
        return all_lessons

    def save_complete_module(self, lessons):
        """Save complete module with all lessons"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"module2_phase1_complete_{timestamp}.json"
        
        # Create complete module structure
        module_structure = {
            "module_info": {
                "id": 15,  # Next module after Module 1 (id: 14)
                "title": "Module 2: Personal Initiative & Assessments (Phase 1)",
                "description": "Comprehensive training in Personal Initiative concepts and practical applications",
                "sort_order": 2,
                "is_published": True,
                "total_lessons": len(lessons),
                "estimated_duration_minutes": sum(lesson['estimated_duration'] for lesson in lessons)
            },
            "lessons": lessons,
            "implementation_notes": {
                "phase": "Phase 1 of 4",
                "slides_covered": "1-55 out of 180 total",
                "coverage_percentage": round((55/180) * 100, 1),
                "creation_date": datetime.now().isoformat(),
                "validation_status": "Ready for import"
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(module_structure, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(filename)
            print(f"\n💾 COMPLETE MODULE SAVED")
            print(f"📁 File: {filename}")
            print(f"📊 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"📚 Lessons: {len(lessons)}")
            print(f"⏱️ Total Duration: {module_structure['module_info']['estimated_duration_minutes']} minutes")
            
            return filename
        except Exception as e:
            print(f"❌ Failed to save module: {e}")
            return None

if __name__ == "__main__":
    creator = Module2Phase1Creator()
    
    print("🎯 Creating all 5 lessons for Module 2 Phase 1...")
    lessons = creator.create_all_lessons()
    
    if lessons:
        filename = creator.save_complete_module(lessons)
        if filename:
            print(f"\n🎉 PHASE 1 IMPLEMENTATION COMPLETED!")
            print(f"📄 File: {filename}")
            print(f"✅ Ready for validation and import")
        else:
            print(f"\n❌ Failed to save complete module")
    else:
        print(f"\n❌ Failed to create all lessons")
