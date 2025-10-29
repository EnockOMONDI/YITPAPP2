#!/usr/bin/env python3
"""
Module 4 Content Analysis Script
Analyzes the HTML file to identify actual lesson structure and boundaries
"""

import os
import sys
import django
import re
from bs4 import BeautifulSoup

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

def analyze_html_structure():
    """Analyze the HTML file to identify lesson structure"""
    
    html_file = 'courseunits/Soft Skills for the streets content.html'
    
    print("=== Module 4 Content Structure Analysis ===\n")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all pages
        pages = soup.find_all('div', {'data-page-no': True})
        print(f"Total pages found: {len(pages)}")

        # Filter and sort pages by page number
        valid_pages = []
        for page in pages:
            page_no = page.get('data-page-no')
            try:
                page_num = int(page_no)
                valid_pages.append((page_num, page))
            except (ValueError, TypeError):
                print(f"Skipping invalid page number: {page_no}")
                continue

        # Sort by page number
        valid_pages.sort(key=lambda x: x[0])
        pages = [page for _, page in valid_pages]

        print(f"Valid pages found: {len(pages)}")

        # Analyze content patterns
        lesson_indicators = []

        for i, page in enumerate(pages):
            page_no = page.get('data-page-no')

            # Extract text content from the page
            text_content = page.get_text(strip=True)

            # Look for lesson indicators
            lesson_patterns = [
                r'lesson\s*\d+',
                r'module\s*\d+',
                r'chapter\s*\d+',
                r'unit\s*\d+',
                r'section\s*\d+',
                r'part\s*\d+',
                r'understanding\s+\w+',
                r'introduction\s+to',
                r'basics\s+of',
                r'fundamentals\s+of'
            ]

            found_indicators = []
            for pattern in lesson_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    found_indicators.extend(matches)

            if found_indicators:
                lesson_indicators.append({
                    'page': int(page_no),
                    'indicators': found_indicators,
                    'text_preview': text_content[:200] + '...' if len(text_content) > 200 else text_content
                })
        
        print("\n=== Lesson Indicators Found ===")
        for indicator in lesson_indicators:
            print(f"Page {indicator['page']}: {indicator['indicators']}")
            print(f"Preview: {indicator['text_preview'][:100]}...")
            print("-" * 50)
        
        # Analyze major headings and titles
        print("\n=== Major Headings Analysis ===")
        
        # Look for large text elements (likely headings)
        large_text_elements = []

        # Find elements with large font sizes
        for page in pages:
            page_no = page.get('data-page-no')

            try:
                page_num = int(page_no)
            except (ValueError, TypeError):
                continue

            # Look for elements with large font size classes
            large_fonts = page.find_all('div', class_=re.compile(r'fs[0-9a-f]'))

            for element in large_fonts:
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Filter out very short text
                    font_class = None
                    for cls in element.get('class', []):
                        if cls.startswith('fs'):
                            font_class = cls
                            break

                    large_text_elements.append({
                        'page': page_num,
                        'text': text,
                        'font_class': font_class
                    })
        
        # Sort by font size (assuming fs0 is largest, fs1 next, etc.)
        large_text_elements.sort(key=lambda x: (x['font_class'] or 'fsz', x['page']))
        
        print("Large text elements (potential headings):")
        for i, element in enumerate(large_text_elements[:20]):  # Show first 20
            print(f"Page {element['page']}: {element['text']} (class: {element['font_class']})")
        
        # Identify potential lesson boundaries
        print("\n=== Potential Lesson Structure ===")
        
        # Group pages into lessons based on content analysis
        lessons = identify_lesson_boundaries(pages)
        
        for i, lesson in enumerate(lessons, 1):
            print(f"Lesson {i}: Pages {lesson['start_page']}-{lesson['end_page']}")
            print(f"  Title: {lesson['title']}")
            print(f"  Content preview: {lesson['preview'][:100]}...")
            print()
        
        return lessons
        
    except Exception as e:
        print(f"Error analyzing HTML structure: {e}")
        return []

def identify_lesson_boundaries(pages):
    """Identify lesson boundaries based on content analysis"""
    
    lessons = []
    total_pages = len(pages)
    
    # For now, create 10 lessons by dividing pages roughly equally
    # This will be refined based on actual content analysis
    pages_per_lesson = total_pages // 10
    remainder = total_pages % 10
    
    current_page = 1
    
    for lesson_num in range(1, 11):
        # Calculate pages for this lesson
        lesson_pages = pages_per_lesson
        if lesson_num <= remainder:
            lesson_pages += 1
        
        start_page = current_page
        end_page = current_page + lesson_pages - 1
        
        # Get content from the first page of this lesson
        lesson_page = None
        for page in pages:
            if int(page.get('data-page-no')) == start_page:
                lesson_page = page
                break
        
        title = f"Soft Skills Lesson {lesson_num}"
        preview = ""
        
        if lesson_page:
            text_content = lesson_page.get_text(strip=True)
            preview = text_content[:200] if text_content else ""
            
            # Try to extract a better title from content
            title_patterns = [
                r'understanding\s+[\w\s]+',
                r'introduction\s+to\s+[\w\s]+',
                r'basics\s+of\s+[\w\s]+',
                r'fundamentals\s+of\s+[\w\s]+'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    title = match.group(0).title()
                    break
        
        lessons.append({
            'lesson_number': lesson_num,
            'start_page': start_page,
            'end_page': end_page,
            'title': title,
            'preview': preview
        })
        
        current_page = end_page + 1
    
    return lessons

if __name__ == "__main__":
    lessons = analyze_html_structure()
    
    print(f"\n=== Summary ===")
    print(f"Identified {len(lessons)} lessons from 49 pages")
    print("Ready to proceed with extraction based on this structure.")
