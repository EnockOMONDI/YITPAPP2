#!/usr/bin/env python
"""
Update all existing quizzes to have max_attempts = 15
Provides detailed report of changes made
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from assessments.models import Quiz
from django.db import transaction

def update_quiz_max_attempts():
    """Update all quizzes to have max_attempts = 15"""
    
    print("🔄 QUIZ MAX ATTEMPTS UPDATE SCRIPT")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Get all quizzes
    quizzes = Quiz.objects.all().order_by('id')
    
    if not quizzes.exists():
        print("❌ No quizzes found in database")
        return
    
    print(f"📊 Found {quizzes.count()} quizzes to update")
    print()
    
    # Track changes
    updated_count = 0
    unchanged_count = 0
    update_report = []
    
    try:
        with transaction.atomic():
            for quiz in quizzes:
                old_max_attempts = quiz.max_attempts
                
                # Update max_attempts to 15
                quiz.max_attempts = 15
                quiz.save()
                
                # Track the change
                if old_max_attempts != 15:
                    updated_count += 1
                    status = "UPDATED"
                else:
                    unchanged_count += 1
                    status = "UNCHANGED"
                
                update_report.append({
                    'quiz_id': quiz.id,
                    'title': quiz.title,
                    'old_max_attempts': old_max_attempts,
                    'new_max_attempts': 15,
                    'status': status
                })
                
                print(f"✅ Quiz {quiz.id}: {quiz.title[:50]}...")
                print(f"   Old max_attempts: {old_max_attempts} → New: 15 ({status})")
                print()
        
        print("=" * 50)
        print("📋 UPDATE SUMMARY")
        print("=" * 50)
        print(f"✅ Total quizzes processed: {len(update_report)}")
        print(f"🔄 Quizzes updated: {updated_count}")
        print(f"➡️  Quizzes unchanged: {unchanged_count}")
        print()
        
        print("📊 DETAILED REPORT")
        print("=" * 50)
        print(f"{'ID':<4} {'Title':<40} {'Old':<5} {'New':<5} {'Status':<10}")
        print("-" * 70)
        
        for report in update_report:
            title_truncated = report['title'][:37] + "..." if len(report['title']) > 40 else report['title']
            print(f"{report['quiz_id']:<4} {title_truncated:<40} {report['old_max_attempts']:<5} {report['new_max_attempts']:<5} {report['status']:<10}")
        
        print()
        print("✅ All quiz max_attempts successfully updated to 15!")
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"❌ Error updating quizzes: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    success = update_quiz_max_attempts()
    if success:
        print("\n🎉 Quiz update completed successfully!")
    else:
        print("\n❌ Quiz update failed!")
        sys.exit(1)
