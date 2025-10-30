#!/usr/bin/env python3
"""
Fix Module 5 heading colors - convert paragraph headings to proper orange headings
"""

import json
import re

def fix_heading_colors():
    """Fix heading colors in Module 5 extracted content"""
    
    print("=== FIXING MODULE 5 HEADING COLORS ===")
    
    # Load the extracted content
    try:
        with open('module5_esba_extracted.json', 'r', encoding='utf-8') as f:
            lessons = json.load(f)
        print(f"✅ Loaded {len(lessons)} lessons")
    except FileNotFoundError:
        print("❌ Error: module5_esba_extracted.json not found")
        return False
    
    # Define exact text items that should be headings (currently formatted as paragraphs)
    heading_texts = [
        # Business plan sections
        "Executive Summary",
        "Business Description",
        "Market Analysis",
        "Competitive Analysis",
        "Sales and Marketing Plan",
        "Ownership and Management Plan",
        "Operating Plan",
        "Financial Plan",
        "Appendices and Exhibits",

        # Other section headings
        "Ideation",
        "Business plan",
        "Business Structures",
        "Financial statements",
        "By type",
        "By Size",

        # Financial statement types
        "Balance sheet",
        "Income statement",
        "Cash flow statement",

        # Financial statement categories
        "Assets",
        "Liabilities",
        "Equity",
        "Revenue",
        "Expenses",

        # Financial statement line items
        "Cash",
        "Accounts Receivable",
        "Inventory",
        "Prepaid Expenses",
        "Investments",
        "Buildings / land",
        "Machinery / equipment",
        "Intangible assets (patents, trademarks, goodwill)",
        "Accounts Payable",
        "Wages Payable",
        "Loans Payable (Principal & Interest)",
        "Bonds Payable (Principal & Interest)",
        "Capital (shareholders' and/or owners' equity)",
        "Retained earnings",
        "Operating Activities Cash Flow",
        "Investing Activities Cash Flow",
        "Financing Activities Cash Flow",
    ]
    
    total_fixes = 0

    # Process each lesson
    for lesson_idx, lesson in enumerate(lessons):
        lesson_fixes = 0
        content = lesson['content']

        print(f"\n🔄 Processing {lesson['title']}...")

        # Find and replace paragraph headings with proper headings
        for heading_text in heading_texts:
            # Escape special regex characters in the heading text
            escaped_text = re.escape(heading_text)

            # Look for paragraphs that contain exactly this heading text
            paragraph_pattern = r'<div class="content-paragraph"[^>]*>\s*<p style="color: #333;[^"]*">\s*' + escaped_text + r'\s*</p>\s*</div>'

            def replace_with_heading(match):
                return f'''<div class="section-heading" style="margin: 25px 0 15px 0;">
                <h3 style="color: #ff5d15; font-size: 1.4rem; font-weight: bold; margin-bottom: 10px;">
                    {heading_text}
                </h3>
            </div>'''

            new_content, count = re.subn(paragraph_pattern, replace_with_heading, content, flags=re.IGNORECASE | re.DOTALL)
            if count > 0:
                content = new_content
                lesson_fixes += count
                print(f"   ✅ Fixed {count} instances of: {heading_text}")

        # Update lesson content
        lesson['content'] = content
        total_fixes += lesson_fixes

        if lesson_fixes > 0:
            print(f"   📊 Total fixes for this lesson: {lesson_fixes}")
        else:
            print(f"   ✅ No fixes needed for this lesson")
    
    # Save the fixed content
    try:
        with open('module5_esba_extracted_fixed.json', 'w', encoding='utf-8') as f:
            json.dump(lessons, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Fixed content saved to: module5_esba_extracted_fixed.json")
        print(f"📊 Total heading fixes applied: {total_fixes}")
        
        # Also backup original and replace
        import shutil
        shutil.copy('module5_esba_extracted.json', 'module5_esba_extracted_backup.json')
        shutil.copy('module5_esba_extracted_fixed.json', 'module5_esba_extracted.json')
        print(f"✅ Original backed up to: module5_esba_extracted_backup.json")
        print(f"✅ Fixed version now active as: module5_esba_extracted.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Error saving fixed content: {e}")
        return False

def main():
    success = fix_heading_colors()
    if success:
        print(f"\n🎉 Module 5 heading colors fixed successfully!")
        print(f"🔄 Next step: Re-run create_module5_seed.py and import_module5_database.py")
    else:
        print(f"\n❌ Failed to fix heading colors")

if __name__ == "__main__":
    main()
