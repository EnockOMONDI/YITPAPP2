#!/usr/bin/env python3
"""
PDF Generator and Course Builder Session Creator for UPL 101
Creates downloadable PDFs and Course Builder compatible session data
"""

import json
import os
from datetime import datetime
import uuid

class UPLSessionGenerator:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.course_builder_session = {
            "session_id": self.session_id,
            "course_title": "Understanding Purpose in Life (UPL 101)",
            "course_description": "A comprehensive 8-session course exploring the foundations of purpose, service, and meaningful living through African wisdom and personal development principles.",
            "course_category": "Personal Development",
            "difficulty_level": "beginner",
            "estimated_duration": 10,  # hours for 8 sessions
            "price": 39.00,
            "currency": "USD",
            "weeks": 2,
            "total_sessions": 8,
            "modules": [
                {
                    "title": "Week 1: Discovering the Foundations of Purpose",
                    "description": "Explore the fundamental concepts of purpose through stories, principles, and overcoming obstacles",
                    "week": 1,
                    "lessons": []
                },
                {
                    "title": "Week 2: Living, Sharing, and Sustaining Your Purpose",
                    "description": "Apply purpose in daily life, share with others, and create sustainable practices for long-term growth",
                    "week": 2,
                    "lessons": []
                }
            ],
            "created_at": datetime.now().isoformat(),
            "status": "draft"
        }

    def load_lesson_data(self, session_num):
        """Load lesson data from generated JSON files"""
        filename = f"upl_session_{session_num}_lesson.json"
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Lesson file {filename} not found")
            return None

    def create_html_for_pdf(self, lesson_data):
        """Create HTML content suitable for PDF generation"""
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{lesson_data['title']} - YITP</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }}
        
        .header {{
            text-align: center;
            border-bottom: 3px solid #ff5d15;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .logo {{
            color: #1a2e53;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .course-title {{
            color: #ff5d15;
            font-size: 20px;
            margin-bottom: 5px;
        }}
        
        .lesson-title {{
            color: #1a2e53;
            font-size: 28px;
            margin: 0;
        }}
        
        .lesson-meta {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #1a2e53;
        }}
        
        .content {{
            margin: 30px 0;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #f0f0f0;
            color: #666;
            font-size: 14px;
        }}
        
        h2, h3, h4 {{
            color: #1a2e53;
        }}
        
        .highlight {{
            background: #fff8e1;
            border-left: 4px solid #ff5d15;
            padding: 15px;
            margin: 15px 0;
        }}
        
        .activity {{
            background: #f0f8ff;
            border: 2px solid #1a2e53;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
        }}
        
        @media print {{
            body {{ margin: 0; }}
            .header {{ page-break-after: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">YITP - Youth Impact Global</div>
        <div class="course-title">Understanding Purpose in Life (UPL 101)</div>
        <h1 class="lesson-title">{lesson_data['title']}</h1>
    </div>
    
    <div class="lesson-meta">
        <p><strong>Duration:</strong> {lesson_data['estimated_duration']} minutes</p>
        <p><strong>Learning Objectives:</strong> {lesson_data['learning_objectives']}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    
    <div class="content">
        {lesson_data['primary_content']}
    </div>
    
    <div class="footer">
        <p>© 2024 Youth Impact Global - Understanding Purpose in Life Course</p>
        <p>For more courses and resources, visit: www.youthimpactglobal.com</p>
    </div>
</body>
</html>
        """
        return html_template

    def convert_lesson_to_course_builder_format(self, lesson_data, lesson_order):
        """Convert lesson data to Course Builder format"""
        return {
            "id": f"temp_{lesson_order}",
            "title": lesson_data['title'],
            "content_type": lesson_data['content_type'],
            "estimated_duration": lesson_data['estimated_duration'],
            "learning_objectives": lesson_data['learning_objectives'],
            "primary_content": lesson_data['primary_content'],
            "additional_resources": lesson_data['additional_resources'],
            "sort_order": lesson_order,
            "is_preview": False,
            "assessment": lesson_data.get('assessment', {})
        }

    def generate_session_data(self):
        """Generate complete Course Builder session data for all 8 sessions"""
        print("🔄 Generating Complete Course Builder session data (8 sessions)...")

        # Week 1 sessions (1-4)
        week1_lessons = []
        print("\n📅 Processing Week 1 Sessions...")
        for session_num in [1, 2, 3, 4]:
            lesson_data = self.load_lesson_data(session_num)
            if lesson_data:
                course_builder_lesson = self.convert_lesson_to_course_builder_format(lesson_data, session_num)
                week1_lessons.append(course_builder_lesson)

                # Generate HTML for PDF
                html_content = self.create_html_for_pdf(lesson_data)
                html_filename = f"upl_session_{session_num}_pdf.html"
                with open(html_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"📄 Generated PDF HTML: {html_filename}")

        # Week 2 sessions (5-8)
        week2_lessons = []
        print("\n📅 Processing Week 2 Sessions...")
        for session_num in [5, 6, 7, 8]:
            lesson_data = self.load_lesson_data(session_num)
            if lesson_data:
                course_builder_lesson = self.convert_lesson_to_course_builder_format(lesson_data, session_num)
                week2_lessons.append(course_builder_lesson)

                # Generate HTML for PDF
                html_content = self.create_html_for_pdf(lesson_data)
                html_filename = f"upl_session_{session_num}_pdf.html"
                with open(html_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"📄 Generated PDF HTML: {html_filename}")

        # Add lessons to respective modules
        self.course_builder_session["modules"][0]["lessons"] = week1_lessons
        self.course_builder_session["modules"][1]["lessons"] = week2_lessons

        # Save session data
        session_filename = f"upl_complete_course_session_{self.session_id[:8]}.json"
        with open(session_filename, 'w', encoding='utf-8') as f:
            json.dump(self.course_builder_session, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Complete Course Builder session created: {session_filename}")
        print(f"📊 Week 1 Sessions: {len(week1_lessons)}")
        print(f"📊 Week 2 Sessions: {len(week2_lessons)}")
        print(f"📊 Total Sessions: {len(week1_lessons) + len(week2_lessons)}")
        return session_filename

    def create_import_instructions(self):
        """Create instructions for importing into Course Builder"""
        instructions = f"""
# UPL 101 Complete Course Import Instructions

## 📋 Files Generated:
- `upl_complete_course_session_{self.session_id[:8]}.json` - Main session data for Course Builder
- `upl_session_1_pdf.html` through `upl_session_8_pdf.html` - PDF-ready HTML files
- Individual lesson JSON files for reference (upl_session_1_lesson.json through upl_session_8_lesson.json)

## 🚀 Import Process:

### Step 1: Upload Images to Uploadcare
1. Extract any images from the original PDF (if present)
2. Upload images to Uploadcare
3. Update CDN URLs in the session JSON file

### Step 2: Generate PDFs
1. Open each HTML file in a browser (all 8 sessions)
2. Print to PDF with these settings:
   - Paper size: A4
   - Margins: Normal
   - Include headers/footers: No
   - Background graphics: Yes
3. Upload PDFs to Uploadcare
4. Update PDF URLs in session JSON

### Step 3: Import to Course Builder
1. Access YITP Course Builder: `/course-builder/wizard/`
2. Use the session import functionality
3. Load the session JSON file: `upl_complete_course_session_{self.session_id[:8]}.json`

### Step 4: Verify and Publish
1. Review all lesson content in the Course Builder
2. Test quiz functionality for all 8 sessions
3. Verify all resources are accessible
4. Set course price to $39 USD
5. Publish the course

## 📊 Course Structure:
- **Course Title:** Understanding Purpose in Life (UPL 101)
- **Duration:** 10 hours (8 sessions over 2 weeks)
- **Price:** $39 USD
- **Category:** Personal Development
- **Difficulty:** Beginner
- **Format:** 2-week structured program

## 🎯 Complete Session Structure:

### Week 1: Discovering the Foundations of Purpose
1. **Session 1:** Introduction to Life's Purpose (60 min)
2. **Session 2:** The Foundations of Purpose (90 min)
3. **Session 3:** Purpose and Service (60 min)
4. **Session 4:** Overcoming Obstacles to Purpose (60 min)

### Week 2: Living, Sharing, and Sustaining Your Purpose
5. **Session 5:** Practical Tools for Defining Your Purpose (90 min)
6. **Session 6:** Purpose in Action (90 min)
7. **Session 7:** Sharing and Sustaining Your Purpose (90 min)
8. **Session 8:** Reflection and Forward Planning (60 min)

## 📚 Each Session Includes:
- Rich HTML content with YITP styling and African wisdom
- Interactive stories, proverbs, and real-world examples
- 5 true/false quiz questions with detailed explanations (40 total)
- Downloadable PDF resource
- Learning objectives and practical activities
- Reflection questions and community engagement

## 🔗 Next Steps:
1. Complete the Uploadcare uploads for all 8 PDFs
2. Import the complete session into Course Builder
3. Test the full 8-session workflow
4. Launch for student enrollment with 2-week structure
        """
        
        with open("UPL_IMPORT_INSTRUCTIONS.md", 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        print("📋 Import instructions created: UPL_IMPORT_INSTRUCTIONS.md")

    def run_complete_generation(self):
        """Run the complete generation process"""
        print("🚀 Starting UPL 101 Complete Generation Process...")
        print("=" * 60)
        
        # Generate session data
        session_file = self.generate_session_data()
        
        # Create import instructions
        self.create_import_instructions()
        
        print("\n" + "=" * 70)
        print("🎉 UPL 101 COMPLETE COURSE GENERATION FINISHED!")
        print("\n📁 Generated Files:")
        print(f"   • {session_file} (Main Course Builder session)")
        print("   • upl_session_1_pdf.html through upl_session_8_pdf.html (8 PDF files)")
        print("   • upl_session_1_lesson.json through upl_session_8_lesson.json (8 lesson files)")
        print("   • UPL_COMPLETE_IMPORT_INSTRUCTIONS.md (Import guide)")

        print("\n🎯 Ready for Course Builder Import!")
        print(f"   Session ID: {self.session_id[:8]}")
        print("   Course: Understanding Purpose in Life (UPL 101)")
        print("   Price: $39 USD")
        print("   Duration: 10 hours (8 sessions over 2 weeks)")
        print("   Total Quiz Questions: 40 (5 per session)")
        print("   Format: 2-week structured program with African wisdom")

if __name__ == "__main__":
    generator = UPLSessionGenerator()
    generator.run_complete_generation()
