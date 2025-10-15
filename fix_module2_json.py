#!/usr/bin/env python3
"""
Fix Module 2 Phase 1 JSON by Adding Missing Required Fields
===========================================================

This script adds the missing required fields to the Module 2 Phase 1 JSON file
to ensure compatibility with the production database schema.

Missing fields to add:
- video_url: "" (empty string for text-based lessons)
- document_url: "" (empty string for text-based lessons)  
- audio_url: "" (empty string for text-based lessons)
- resources: [] (empty array for additional resources)
"""

import json
import os
from datetime import datetime

def fix_module2_json():
    """Add missing required fields to Module 2 Phase 1 JSON"""
    
    input_file = "module2_phase1_complete_20251013_025946.json"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"module2_phase1_fixed_{timestamp}.json"
    
    print("🔧 FIXING MODULE 2 PHASE 1 JSON")
    print("=" * 60)
    
    # Load the original JSON
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded original JSON: {input_file}")
    print(f"📊 Original lessons: {len(data['lessons'])}")
    
    # Add missing fields to each lesson
    lessons_updated = 0
    for lesson in data['lessons']:
        # Add missing URL fields (empty strings for text-based lessons)
        if 'video_url' not in lesson:
            lesson['video_url'] = ""
            
        if 'document_url' not in lesson:
            lesson['document_url'] = ""
            
        if 'audio_url' not in lesson:
            lesson['audio_url'] = ""
            
        if 'resources' not in lesson:
            lesson['resources'] = []
            
        lessons_updated += 1
        print(f"✅ Updated Lesson {lesson['sort_order']}: {lesson['title'][:50]}...")
    
    # Save the fixed JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Get file sizes for comparison
    original_size = os.path.getsize(input_file)
    fixed_size = os.path.getsize(output_file)
    
    print(f"\n📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Lessons updated: {lessons_updated}")
    print(f"📄 Original file: {input_file} ({original_size:,} bytes)")
    print(f"📄 Fixed file: {output_file} ({fixed_size:,} bytes)")
    print(f"📈 Size difference: {fixed_size - original_size:,} bytes")
    
    # Validate the fixed JSON
    print(f"\n🔍 VALIDATION")
    print("=" * 60)
    
    validation_passed = True
    for i, lesson in enumerate(data['lessons'], 1):
        required_fields = ['video_url', 'document_url', 'audio_url', 'resources']
        missing_fields = []
        
        for field in required_fields:
            if field not in lesson:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ Lesson {i} missing fields: {missing_fields}")
            validation_passed = False
        else:
            print(f"✅ Lesson {i}: All required fields present")
    
    if validation_passed:
        print(f"\n🎉 SUCCESS: Module 2 Phase 1 JSON fixed successfully!")
        print(f"📄 Fixed file ready for import: {output_file}")
        return output_file
    else:
        print(f"\n❌ FAILED: Validation errors found")
        return False

if __name__ == "__main__":
    result = fix_module2_json()
    if result:
        print(f"\n✅ Fixed JSON file: {result}")
        print(f"🚀 Ready for production import!")
    else:
        print(f"\n❌ Failed to fix JSON file")
