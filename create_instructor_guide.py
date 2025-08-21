#!/usr/bin/env python
"""
Generate comprehensive instructor guide PDF for YITP course creation
"""

import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.platypus.flowables import Flowable
from datetime import datetime

# YITP Brand Colors
YITP_ORANGE = HexColor('#ff5d15')
YITP_DARK_BLUE = HexColor('#1a2e53')
YITP_LIGHT_BLUE = HexColor('#e7f3ff')

class HeaderFooter:
    def __init__(self, canvas, doc):
        self.canvas = canvas
        self.doc = doc
        
    def header(self):
        # Header with YITP branding
        self.canvas.setFillColor(YITP_DARK_BLUE)
        self.canvas.rect(0, letter[1] - 60, letter[0], 60, fill=1)
        
        self.canvas.setFillColor(white)
        self.canvas.setFont("Helvetica-Bold", 16)
        self.canvas.drawString(50, letter[1] - 35, "YITP Course Creation Guide")
        
        self.canvas.setFont("Helvetica", 10)
        self.canvas.drawRightString(letter[0] - 50, letter[1] - 35, f"Generated: {datetime.now().strftime('%B %Y')}")
        
    def footer(self):
        # Footer with page number
        self.canvas.setFillColor(YITP_ORANGE)
        self.canvas.rect(0, 0, letter[0], 30, fill=1)
        
        self.canvas.setFillColor(white)
        self.canvas.setFont("Helvetica", 10)
        self.canvas.drawCentredString(letter[0]/2, 15, f"Page {self.canvas.getPageNumber()}")
        
        self.canvas.setFont("Helvetica", 8)
        self.canvas.drawString(50, 15, "Youth Impact Training Programme")
        self.canvas.drawRightString(letter[0] - 50, 15, "www.youthimpactglobal.com")

def create_instructor_guide():
    """Create comprehensive instructor guide PDF"""
    
    filename = "YITP_Instructor_Course_Creation_Guide.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=80, bottomMargin=50)
    
    # Custom styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=YITP_DARK_BLUE,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Heading styles
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        spaceBefore=20,
        textColor=YITP_DARK_BLUE,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=15,
        spaceBefore=15,
        textColor=YITP_ORANGE,
        fontName='Helvetica-Bold'
    )
    
    # Body text style
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        fontName='Helvetica'
    )
    
    # Code style
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=9,
        spaceAfter=10,
        leftIndent=20,
        backgroundColor=YITP_LIGHT_BLUE,
        fontName='Courier'
    )
    
    # Build document content
    story = []
    
    # Title Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("YITP Course Creation Guide", title_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Comprehensive Guide for Instructors", heading2_style))
    story.append(Spacer(1, 1*inch))
    
    # Introduction section
    story.append(Paragraph("Welcome to the Youth Impact Training Programme (YITP) course creation system. This comprehensive guide will walk you through every aspect of creating engaging, effective courses on our platform.", body_style))
    story.append(Spacer(1, 0.5*inch))
    
    # Key features box
    features_data = [
        ['Feature', 'Description'],
        ['Rich Content Support', 'Text, videos, presentations, documents, and interactive elements'],
        ['Assessment Tools', 'Quizzes, assignments, and automated grading'],
        ['Progress Tracking', 'Detailed student progress and analytics'],
        ['Certification', 'Automatic certificate generation upon completion'],
        ['Gamification', 'Points, badges, and achievement system'],
        ['Mobile Responsive', 'Optimized for all devices']
    ]
    
    features_table = Table(features_data, colWidths=[2*inch, 4*inch])
    features_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), YITP_DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), YITP_LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(features_table)
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", heading1_style))
    
    toc_data = [
        ['Section', 'Page'],
        ['1. Getting Started', '3'],
        ['2. Course Structure Overview', '4'],
        ['3. Content Creation Guidelines', '6'],
        ['4. Assessment Design', '8'],
        ['5. Student Engagement Strategies', '10'],
        ['6. Technical Requirements', '12'],
        ['7. Quality Assurance Checklist', '14'],
        ['8. Publishing and Deployment', '15'],
        ['9. Analytics and Improvement', '16'],
        ['10. Support and Resources', '17']
    ]
    
    toc_table = Table(toc_data, colWidths=[4*inch, 1*inch])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), YITP_ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, black)
    ]))
    
    story.append(toc_table)
    story.append(PageBreak())
    
    # Section 1: Getting Started
    story.append(Paragraph("1. Getting Started", heading1_style))
    
    story.append(Paragraph("Course Creation Workflow", heading2_style))
    story.append(Paragraph("The YITP platform follows a structured workflow for course creation:", body_style))
    
    workflow_steps = [
        "1. <b>Course Planning</b>: Define learning objectives, target audience, and course structure",
        "2. <b>Content Development</b>: Create modules, lessons, and assessments",
        "3. <b>Review Process</b>: Submit for admin review and approval",
        "4. <b>Publication</b>: Course goes live for student enrollment",
        "5. <b>Monitoring</b>: Track student progress and course effectiveness"
    ]
    
    for step in workflow_steps:
        story.append(Paragraph(step, body_style))
    
    story.append(Spacer(1, 0.3*inch))
    
    # Access Requirements
    story.append(Paragraph("Access Requirements", heading2_style))
    story.append(Paragraph("To create courses on the YITP platform, you need:", body_style))
    
    requirements = [
        "• Instructor account with appropriate permissions",
        "• Access to the Django admin interface",
        "• Understanding of your target audience and learning objectives",
        "• Content materials (videos, documents, presentations)",
        "• Assessment questions and rubrics"
    ]
    
    for req in requirements:
        story.append(Paragraph(req, body_style))
    
    story.append(PageBreak())
    
    # Section 2: Course Structure Overview
    story.append(Paragraph("2. Course Structure Overview", heading1_style))
    
    story.append(Paragraph("Hierarchical Structure", heading2_style))
    story.append(Paragraph("YITP courses follow a three-level hierarchy:", body_style))
    
    structure_data = [
        ['Level', 'Description', 'Key Features'],
        ['Course', 'Top-level container', 'Title, description, pricing, instructor assignment'],
        ['Module', 'Organizational units', 'Grouping related lessons, unlock criteria, duration'],
        ['Lesson', 'Individual learning units', 'Content, assessments, resources, objectives']
    ]
    
    structure_table = Table(structure_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
    structure_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), YITP_DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), YITP_LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    
    story.append(structure_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Course Planning Template
    story.append(Paragraph("Course Planning Template", heading2_style))
    story.append(Paragraph("Use this template to plan your course structure:", body_style))
    
    planning_text = """
<b>Course Title:</b> ________________________________

<b>Target Audience:</b> ____________________________

<b>Learning Objectives:</b>
1. Students will be able to ________________________
2. Students will understand ________________________
3. Students will demonstrate _______________________

<b>Prerequisites:</b> _______________________________

<b>Estimated Duration:</b> _________ hours

<b>Module Structure:</b>
Module 1: ________________________________________
  - Lesson 1.1: __________________________________
  - Lesson 1.2: __________________________________
  - Assessment: __________________________________

Module 2: ________________________________________
  - Lesson 2.1: __________________________________
  - Lesson 2.2: __________________________________
  - Assessment: __________________________________
"""
    
    story.append(Paragraph(planning_text, code_style))
    story.append(PageBreak())

    # Section 3: Content Creation Guidelines
    story.append(Paragraph("3. Content Creation Guidelines", heading1_style))

    story.append(Paragraph("Supported Content Types", heading2_style))
    story.append(Paragraph("The YITP platform supports various content types to create engaging learning experiences:", body_style))

    content_types_data = [
        ['Content Type', 'Best Use Cases', 'Technical Notes'],
        ['Rich Text', 'Explanations, instructions, theory', 'CKEditor5 with formatting, images, links'],
        ['Video Content', 'Demonstrations, lectures, tutorials', 'YouTube/Vimeo integration recommended'],
        ['Presentations', 'Slide-based content, visual aids', 'PowerPoint, PDF uploads (max 10MB)'],
        ['Documents', 'Reading materials, handouts', 'PDF, Word documents (max 10MB)'],
        ['Interactive Elements', 'Exercises, simulations', 'Embedded content, external tools'],
        ['Images', 'Diagrams, infographics, photos', 'JPEG, PNG, GIF support'],
        ['Audio', 'Podcasts, voice instructions', 'MP3, WAV, external platform integration']
    ]

    content_table = Table(content_types_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
    content_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), YITP_ORANGE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), YITP_LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 8)
    ]))

    story.append(content_table)
    story.append(Spacer(1, 0.3*inch))

    # Content Creation Best Practices
    story.append(Paragraph("Content Creation Best Practices", heading2_style))

    best_practices = [
        "<b>Chunking:</b> Break content into digestible 5-15 minute segments",
        "<b>Multimedia Balance:</b> Combine text, visuals, and interactive elements",
        "<b>Clear Objectives:</b> State learning objectives at the beginning of each lesson",
        "<b>Progressive Disclosure:</b> Introduce concepts gradually, building on previous knowledge",
        "<b>Engagement:</b> Include questions, activities, and real-world examples",
        "<b>Accessibility:</b> Provide alt text for images, captions for videos",
        "<b>Mobile Optimization:</b> Ensure content works well on all device sizes",
        "<b>Resource Links:</b> Include additional resources for deeper learning"
    ]

    for practice in best_practices:
        story.append(Paragraph(f"• {practice}", body_style))

    story.append(PageBreak())

    # Section 4: Assessment Design
    story.append(Paragraph("4. Assessment Design", heading1_style))

    story.append(Paragraph("Assessment Types Available", heading2_style))

    assessment_data = [
        ['Type', 'Question Formats', 'Grading', 'Best Use'],
        ['Quiz', 'Multiple choice, True/False, Short answer, Essay, Matching, Fill-in-blank', 'Automatic/Manual', 'Knowledge checks, comprehension'],
        ['Assignment', 'Business plan, SWOT analysis, Case study, Reflection, Presentation, Project, Research', 'Manual with rubrics', 'Application, analysis, synthesis']
    ]

    assessment_table = Table(assessment_data, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1.5*inch])
    assessment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), YITP_DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), YITP_LIGHT_BLUE),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 1), (-1, -1), 8)
    ]))

    story.append(assessment_table)
    story.append(Spacer(1, 0.3*inch))

    # Assessment Guidelines
    story.append(Paragraph("Assessment Design Guidelines", heading2_style))

    assessment_guidelines = [
        "<b>Alignment:</b> Ensure assessments align with learning objectives",
        "<b>Variety:</b> Use different question types to assess different skills",
        "<b>Difficulty Progression:</b> Start with easier questions, increase complexity",
        "<b>Clear Instructions:</b> Provide clear, unambiguous instructions",
        "<b>Feedback:</b> Include explanations for correct answers",
        "<b>Time Limits:</b> Set reasonable time limits for quizzes",
        "<b>Multiple Attempts:</b> Allow retakes for learning-focused assessments",
        "<b>Passing Scores:</b> Set appropriate passing thresholds (typically 70%)"
    ]

    for guideline in assessment_guidelines:
        story.append(Paragraph(f"• {guideline}", body_style))

    story.append(PageBreak())

    # Section 5: Technical Implementation
    story.append(Paragraph("5. Technical Implementation", heading1_style))

    story.append(Paragraph("Step-by-Step Course Creation", heading2_style))

    implementation_steps = [
        "<b>Step 1: Create Course</b><br/>Navigate to Django Admin → Courses → Add Course<br/>Fill in title, description, learning objectives, prerequisites",
        "<b>Step 2: Add Modules</b><br/>Create organizational modules with clear titles and descriptions<br/>Set sort order for proper sequencing",
        "<b>Step 3: Create Lessons</b><br/>Add individual lessons to each module<br/>Choose appropriate content type and add content",
        "<b>Step 4: Add Assessments</b><br/>Create quizzes and assignments for each lesson<br/>Configure grading and attempt settings",
        "<b>Step 5: Review and Test</b><br/>Preview content, test assessments, check progression<br/>Ensure all links and media work correctly",
        "<b>Step 6: Submit for Review</b><br/>Change status to 'in_review' for admin approval<br/>Address any feedback from reviewers"
    ]

    for step in implementation_steps:
        story.append(Paragraph(step, body_style))
        story.append(Spacer(1, 0.1*inch))

    story.append(PageBreak())

    # Section 6: Quality Assurance Checklist
    story.append(Paragraph("6. Quality Assurance Checklist", heading1_style))

    qa_checklist = [
        "☐ Course title is clear and descriptive",
        "☐ Learning objectives are specific and measurable",
        "☐ Prerequisites are clearly stated",
        "☐ Content is organized logically in modules and lessons",
        "☐ Each lesson has clear learning objectives",
        "☐ Content is engaging and interactive",
        "☐ All media files work correctly",
        "☐ External links are functional",
        "☐ Assessments align with learning objectives",
        "☐ Quiz questions are clear and unambiguous",
        "☐ Correct answers are accurate",
        "☐ Passing scores are appropriate",
        "☐ Content is accessible and mobile-friendly",
        "☐ Estimated durations are realistic",
        "☐ Course flows logically from basic to advanced concepts",
        "☐ All content is original or properly attributed",
        "☐ Grammar and spelling are correct",
        "☐ Course is ready for student enrollment"
    ]

    for item in qa_checklist:
        story.append(Paragraph(item, body_style))

    story.append(PageBreak())

    # Section 7: Support and Resources
    story.append(Paragraph("7. Support and Resources", heading1_style))

    story.append(Paragraph("Getting Help", heading2_style))
    story.append(Paragraph("If you need assistance with course creation:", body_style))

    support_info = [
        "<b>Technical Support:</b> Contact the YITP technical team for platform issues",
        "<b>Instructional Design:</b> Consult with educational specialists for course design",
        "<b>Content Review:</b> Submit courses for peer review before publication",
        "<b>Student Feedback:</b> Monitor course analytics and student feedback for improvements"
    ]

    for info in support_info:
        story.append(Paragraph(f"• {info}", body_style))

    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Additional Resources", heading2_style))

    resources = [
        "• YITP Platform Documentation: Complete technical documentation",
        "• Video Tutorials: Step-by-step video guides for course creation",
        "• Best Practices Library: Examples of excellent courses",
        "• Community Forum: Connect with other instructors",
        "• Regular Training Sessions: Live training and Q&A sessions"
    ]

    for resource in resources:
        story.append(Paragraph(resource, body_style))

    # Build PDF with custom header/footer
    def add_page_decorations(canvas, doc):
        header_footer = HeaderFooter(canvas, doc)
        header_footer.header()
        header_footer.footer()

    doc.build(story, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)

    print(f"✅ Instructor guide created: {filename}")
    return filename

if __name__ == '__main__':
    create_instructor_guide()
