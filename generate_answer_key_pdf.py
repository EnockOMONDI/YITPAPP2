#!/usr/bin/env python3
"""
Generate a comprehensive answer key PDF for all YITP quiz questions
"""

import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas

# YITP Brand Colors
YITP_ORANGE = HexColor('#ff5d15')
YITP_BLUE = HexColor('#1a2e53')

class NumberedCanvas(canvas.Canvas):
    """Custom canvas to add page numbers"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for (page_num, page_state) in enumerate(self._saved_page_states):
            self.__dict__.update(page_state)
            self.draw_page_number(page_num + 1, num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_num, total_pages):
        self.setFont("Helvetica", 9)
        self.setFillColor(YITP_BLUE)
        self.drawRightString(letter[0] - 0.75 * inch, 0.75 * inch, 
                           f"Page {page_num} of {total_pages}")

def create_custom_styles():
    """Create custom paragraph styles for the PDF"""
    styles = getSampleStyleSheet()
    
    # Title style
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        textColor=YITP_ORANGE,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    ))
    
    # Module header style
    styles.add(ParagraphStyle(
        name='ModuleHeader',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=YITP_ORANGE,
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    ))
    
    # Lesson header style
    styles.add(ParagraphStyle(
        name='LessonHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=YITP_BLUE,
        spaceAfter=8,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    ))
    
    # Quiz header style
    styles.add(ParagraphStyle(
        name='QuizHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=YITP_BLUE,
        spaceAfter=6,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    ))
    
    # Question style
    styles.add(ParagraphStyle(
        name='Question',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=4,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    ))
    
    # Answer style
    styles.add(ParagraphStyle(
        name='Answer',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=2,
        leftIndent=20,
        fontName='Helvetica'
    ))
    
    # Correct answer style
    styles.add(ParagraphStyle(
        name='CorrectAnswer',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        leftIndent=20,
        textColor=YITP_ORANGE,
        fontName='Helvetica-Bold'
    ))
    
    # Statistics style
    styles.add(ParagraphStyle(
        name='Statistics',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica'
    ))
    
    return styles

def generate_answer_key_pdf():
    """Generate the complete answer key PDF"""
    
    print("📄 GENERATING YITP COMPLETE ANSWER KEY PDF")
    print("=" * 60)
    
    # Check if quiz data file exists
    quiz_data_file = 'yitp_quiz_answers_complete.json'
    if not os.path.exists(quiz_data_file):
        print(f"❌ Quiz data file not found: {quiz_data_file}")
        print(f"🔄 Please run extract_quiz_answers.py first")
        return False
    
    # Load quiz data
    try:
        with open(quiz_data_file, 'r', encoding='utf-8') as f:
            quiz_data = json.load(f)
        print(f"✅ Loaded quiz data from {quiz_data_file}")
    except Exception as e:
        print(f"❌ Error loading quiz data: {e}")
        return False
    
    # Create PDF
    output_filename = 'YITP_Complete_Answer_Key.pdf'
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=1*inch
    )
    
    # Get custom styles
    styles = create_custom_styles()
    
    # Build PDF content
    story = []
    
    # Title page
    story.append(Paragraph("YITP Course", styles['CustomTitle']))
    story.append(Paragraph("Complete Answer Key", styles['CustomTitle']))
    story.append(Spacer(1, 0.5*inch))
    
    # Course info
    story.append(Paragraph(f"<b>Course:</b> {quiz_data['course_title']}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Statistics
    stats = quiz_data['statistics']
    story.append(Paragraph("<b>Course Statistics:</b>", styles['Normal']))
    story.append(Paragraph(f"• Total Modules: {stats['total_modules']}", styles['Statistics']))
    story.append(Paragraph(f"• Total Lessons: {stats['total_lessons']}", styles['Statistics']))
    story.append(Paragraph(f"• Total Quizzes: {stats['total_quizzes']}", styles['Statistics']))
    story.append(Paragraph(f"• Total Questions: {stats['total_questions']}", styles['Statistics']))
    story.append(Spacer(1, 0.3*inch))
    
    # Generation info
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles['Normal']))
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", styles['ModuleHeader']))
    story.append(Spacer(1, 0.2*inch))
    
    toc_data = []
    page_num = 3  # Starting after title and TOC pages
    
    for module in quiz_data['modules']:
        toc_data.append([f"Module {module['module_sort_order']}: {module['module_title']}", f"Page {page_num}"])
        page_num += 1  # Estimate pages per module
        
        for lesson in module['lessons']:
            toc_data.append([f"  • {lesson['lesson_title']}", ""])
    
    if toc_data:
        toc_table = Table(toc_data, colWidths=[5*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(toc_table)
    
    story.append(PageBreak())
    
    # Process each module
    for module in quiz_data['modules']:
        print(f"📂 Processing Module {module['module_sort_order']}: {module['module_title']}")
        
        # Module header
        story.append(Paragraph(f"Module {module['module_sort_order']}: {module['module_title']}", styles['ModuleHeader']))
        
        if module['module_description']:
            story.append(Paragraph(module['module_description'], styles['Normal']))
            story.append(Spacer(1, 0.1*inch))
        
        # Module statistics
        story.append(Paragraph(f"<b>Module Statistics:</b> {module['lesson_count']} lessons, {module['quiz_count']} quizzes, {module['question_count']} questions", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        
        # Process each lesson
        for lesson in module['lessons']:
            print(f"   📄 Processing Lesson: {lesson['lesson_title']}")
            
            # Lesson header
            story.append(Paragraph(f"Lesson: {lesson['lesson_title']}", styles['LessonHeader']))
            
            # Process each quiz
            for quiz in lesson['quizzes']:
                print(f"      🧪 Processing Quiz: {quiz['quiz_title']}")
                
                # Quiz header
                story.append(Paragraph(f"Quiz: {quiz['quiz_title']}", styles['QuizHeader']))
                story.append(Paragraph(f"Passing Score: {quiz['passing_score']}% | Max Attempts: {quiz['max_attempts']}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Process each question
                for question in quiz['questions']:
                    # Question text
                    story.append(Paragraph(f"Question {question['question_number']}: {question['question_text']}", styles['Question']))
                    
                    # Handle different question types
                    if question['question_type'] == 'multiple_choice' and question['options']:
                        # Show all options with correct answer highlighted
                        for i, option in enumerate(question['options']):
                            option_letter = chr(65 + i)  # A, B, C, D...
                            if option == question['correct_answer']:
                                story.append(Paragraph(f"<b>{option_letter}. {option} ✓ (CORRECT)</b>", styles['CorrectAnswer']))
                            else:
                                story.append(Paragraph(f"{option_letter}. {option}", styles['Answer']))
                    else:
                        # For other question types, just show the correct answer
                        story.append(Paragraph(f"<b>Correct Answer:</b> {question['correct_answer']}", styles['CorrectAnswer']))
                    
                    # Add explanation if available
                    if question['explanation']:
                        story.append(Paragraph(f"<b>Explanation:</b> {question['explanation']}", styles['Answer']))
                    
                    story.append(Spacer(1, 0.1*inch))
                
                story.append(Spacer(1, 0.2*inch))
            
            story.append(Spacer(1, 0.2*inch))
        
        # Add page break between modules (except for the last one)
        if module != quiz_data['modules'][-1]:
            story.append(PageBreak())
    
    # Build PDF
    try:
        print(f"📝 Building PDF document...")
        doc.build(story, canvasmaker=NumberedCanvas)
        print(f"✅ PDF generated successfully: {output_filename}")
        
        # Get file size
        file_size = os.path.getsize(output_filename)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"📊 PDF Statistics:")
        print(f"   • File size: {file_size_mb:.2f} MB")
        print(f"   • Total modules: {stats['total_modules']}")
        print(f"   • Total questions: {stats['total_questions']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating PDF: {e}")
        return False

def main():
    success = generate_answer_key_pdf()
    
    if success:
        print(f"\n🎉 YITP Complete Answer Key PDF generated successfully!")
        print(f"📁 Output file: YITP_Complete_Answer_Key.pdf")
        print(f"📖 The PDF contains all quiz questions and answers from all 5 modules")
    else:
        print(f"\n❌ Failed to generate answer key PDF")

if __name__ == "__main__":
    main()
