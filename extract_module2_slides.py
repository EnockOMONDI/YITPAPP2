#!/usr/bin/env python3
"""
Extract individual lesson HTML files from the main Module 2 HTML file.
Each lesson contains specific slide ranges:
- Lesson 1: Slides 1-9 (IDs: pf1 through pf9)
- Lesson 2: Slides 10-20 (IDs: pfa through pf14)
- Lesson 3: Slides 21-31 (IDs: pf15 through pf1f)
- Lesson 4: Slides 32-39 (IDs: pf20 through pf27)
- Lesson 5: Slides 40-55 (IDs: pf28 through pf37)
"""

import os
import re
from bs4 import BeautifulSoup

def hex_to_decimal(hex_str):
    """Convert hexadecimal string to decimal"""
    return int(hex_str, 16)

def decimal_to_hex(decimal):
    """Convert decimal to hexadecimal string"""
    return format(decimal, 'x')

def get_slide_ids_for_lesson(lesson_number):
    """Get the slide IDs for a specific lesson"""
    slide_ranges = {
        1: range(1, 10),    # Slides 1-9
        2: range(10, 21),   # Slides 10-20
        3: range(21, 32),   # Slides 21-31
        4: range(32, 40),   # Slides 32-39
        5: range(40, 56),   # Slides 40-55
    }
    
    if lesson_number not in slide_ranges:
        return []
    
    slide_ids = []
    for slide_num in slide_ranges[lesson_number]:
        hex_id = decimal_to_hex(slide_num)
        slide_ids.append(f"pf{hex_id}")
    
    return slide_ids

def extract_lesson_content(main_html_path, lesson_number, output_path):
    """Extract content for a specific lesson and create individual HTML file"""
    
    # Read the main HTML file
    with open(main_html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Get slide IDs for this lesson
    slide_ids = get_slide_ids_for_lesson(lesson_number)
    
    if not slide_ids:
        print(f"No slides found for lesson {lesson_number}")
        return False
    
    print(f"Extracting lesson {lesson_number} with slides: {slide_ids}")
    
    # Find all slide divs with the specified IDs
    lesson_slides = []
    for slide_id in slide_ids:
        slide_div = soup.find('div', {'id': slide_id})
        if slide_div:
            lesson_slides.append(slide_div)
            print(f"  Found slide: {slide_id}")
        else:
            print(f"  Warning: Slide {slide_id} not found")
    
    if not lesson_slides:
        print(f"No slide content found for lesson {lesson_number}")
        return False
    
    # Extract the head section (CSS and fonts) but remove problematic scripts
    head_section = soup.find('head')

    if head_section:
        # Remove script tags that might cause issues in iframe
        for script in head_section.find_all('script'):
            script.decompose()

    # Create new HTML document for this lesson
    lesson_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Module 2 - Lesson {lesson_number}: Personal Initiative</title>
    {head_section.prettify() if head_section else ''}
    <style>
        /* Additional iframe-specific styles */
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
        }}
        #page-container {{
            width: 100%;
            max-width: none;
        }}
        .pf {{
            margin: 10px auto !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }}
        /* Ensure responsive behavior */
        @media (max-width: 768px) {{
            body {{ padding: 10px; }}
            .pf {{ margin: 5px auto !important; }}
        }}
    </style>
</head>
<body>
    <div id="page-container">
"""
    
    # Add each slide to the lesson HTML (remove any scripts)
    for slide in lesson_slides:
        # Remove any script tags from slides
        for script in slide.find_all('script'):
            script.decompose()
        lesson_html += slide.prettify()

    lesson_html += f"""
    </div>
    <script>
        // Simple script to ensure iframe loads properly
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Module 2 Lesson {lesson_number} loaded successfully');

            // Remove any problematic elements that might cause errors
            var problematicElements = document.querySelectorAll('[onclick], [onload], [onerror]');
            problematicElements.forEach(function(el) {{
                el.removeAttribute('onclick');
                el.removeAttribute('onload');
                el.removeAttribute('onerror');
            }});
        }});
    </script>
</body>
</html>"""
    
    # Write the lesson HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(lesson_html)
    
    print(f"Created lesson {lesson_number} HTML file: {output_path}")
    return True

def main():
    """Main function to extract all lesson files"""
    
    # Paths
    main_html_path = "static/module2/2. PERSONAL INITIATIVE FULL UNIT (MERGED) (1).html"
    output_dir = "static/module2"
    
    # Check if main HTML file exists
    if not os.path.exists(main_html_path):
        print(f"Error: Main HTML file not found: {main_html_path}")
        return
    
    # Extract each lesson
    for lesson_num in range(1, 6):  # Lessons 1-5
        output_path = os.path.join(output_dir, f"lesson_{lesson_num}.html")
        
        try:
            success = extract_lesson_content(main_html_path, lesson_num, output_path)
            if success:
                print(f"✅ Successfully created lesson {lesson_num}")
            else:
                print(f"❌ Failed to create lesson {lesson_num}")
        except Exception as e:
            print(f"❌ Error creating lesson {lesson_num}: {str(e)}")
    
    print("\n🎉 Module 2 lesson extraction complete!")

if __name__ == "__main__":
    main()
