#!/usr/bin/env python3
"""
Extract individual lesson HTML files from the main Module 2 HTML file.
This version preserves the complete CSS framework and container structure.
"""

import os
from bs4 import BeautifulSoup

def get_slide_ids_for_lesson(lesson_number):
    """Get the slide IDs for a specific lesson"""
    slide_ranges = {
        1: range(1, 10),    # Slides 1-9
        2: range(10, 21),   # Slides 10-20
        3: range(21, 32),   # Slides 21-31
        4: range(32, 40),   # Slides 32-39
        5: range(40, 56),   # Slides 40-55
    }
    
    slide_ids = []
    for i in slide_ranges[lesson_number]:
        if i <= 9:
            slide_ids.append(f'pf{i}')
        else:
            # Convert to hexadecimal for slides 10+
            slide_ids.append(f'pf{hex(i)[2:]}')
    
    return slide_ids

def extract_lesson_slides(lesson_number):
    """Extract slides for a specific lesson and create HTML file with complete CSS context"""
    try:
        # Read the main HTML file
        with open('2. PERSONAL INITIATIVE FULL Module HTML (MERGED)/2. PERSONAL INITIATIVE FULL UNIT (MERGED) (1).html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Get slide IDs for this lesson
        slide_ids = get_slide_ids_for_lesson(lesson_number)
        print(f"Extracting lesson {lesson_number} with slides: {slide_ids}")
        
        # Find all slides for this lesson
        lesson_slides = []
        for slide_id in slide_ids:
            slide = soup.find('div', {'id': slide_id})
            if slide:
                print(f"  Found slide: {slide_id}")
                lesson_slides.append(slide)
            else:
                print(f"  WARNING: Slide {slide_id} not found!")
        
        if not lesson_slides:
            print(f"❌ No slides found for lesson {lesson_number}")
            return False

        # Extract the complete head section (preserve ALL CSS)
        head_section = soup.find('head')
        
        # Create new HTML document for this lesson with COMPLETE CSS framework
        lesson_html = f"""<!DOCTYPE html>
<!-- Created by pdf2htmlEX (https://github.com/pdf2htmlEX/pdf2htmlEX) -->
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta charset="utf-8"/>
    <meta name="generator" content="pdf2htmlEX"/>
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1"/>
    <title>Module 2 - Lesson {lesson_number}: Personal Initiative</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
"""

        # Add ALL style tags from the original head
        if head_section:
            for style_tag in head_section.find_all('style'):
                lesson_html += str(style_tag) + "\n"

        lesson_html += """
    <style type="text/css">
        /* Additional iframe-specific optimizations */
        body {
            margin: 0;
            padding: 0;
            background-color: #9e9e9e;
        }
        
        #page-container {
            position: relative;
            margin: 0;
            padding: 20px;
            background-color: #9e9e9e;
        }
        
        .pf {
            margin: 13px auto !important;
            box-shadow: 1px 1px 3px 1px #333 !important;
            border-collapse: separate !important;
            background-color: white !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        /* Ensure proper scaling for iframe */
        @media (max-width: 768px) {
            #page-container {
                padding: 10px;
            }
            .pf {
                margin: 8px auto !important;
            }
        }
        
        @media (max-width: 480px) {
            #page-container {
                padding: 5px;
            }
            .pf {
                margin: 5px auto !important;
            }
        }
    </style>
</head>
<body>
    <div id="page-container">
"""

        # Add each slide to the lesson HTML (preserve complete structure)
        for slide in lesson_slides:
            lesson_html += str(slide) + "\n"
        
        lesson_html += """
    </div>
    <script>
        // Simple script to ensure iframe loads properly
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Module 2 Lesson """ + str(lesson_number) + """ loaded successfully');
            
            // Ensure all slides are visible
            var slides = document.querySelectorAll('.pf');
            slides.forEach(function(slide) {
                slide.style.display = 'block';
                slide.style.visibility = 'visible';
            });
        });
    </script>
</body>
</html>"""
        
        # Write the lesson HTML file
        output_file = f'static/module2/lesson_{lesson_number}.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(lesson_html)
        
        print(f"Created lesson {lesson_number} HTML file: {output_file}")
        print(f"✅ Successfully created lesson {lesson_number}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating lesson {lesson_number}: {e}")
        return False

def main():
    """Extract all lessons"""
    # Ensure output directory exists
    os.makedirs('static/module2', exist_ok=True)
    
    # Extract all 5 lessons
    for lesson_num in range(1, 6):
        extract_lesson_slides(lesson_num)
    
    print("\n🎉 Module 2 lesson extraction complete!")

if __name__ == "__main__":
    main()
