#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from progress.models import Enrollment
from assessments.models import Quiz

def main():
    user = User.objects.get(username='testuser')
    quiz = Quiz.objects.get(id=3)
    course = quiz.lesson.module.course
    
    print(f'User: {user.username}')
    print(f'Course: {course.title}')
    print(f'Course ID: {course.id}')
    
    # Check enrollment
    enrollment = Enrollment.objects.filter(student=user, course=course)
    print(f'Enrollment exists: {enrollment.exists()}')
    
    if enrollment.exists():
        enr = enrollment.first()
        print(f'Enrollment status: {enr.status}')
        print(f'Enrollment ID: {enr.id}')
        print(f'Enrolled at: {enr.enrolled_at}')
    
    # Check enrollment with active status specifically
    active_enrollment = Enrollment.objects.filter(student=user, course=course, status='active')
    print(f'Active enrollment exists: {active_enrollment.exists()}')
    
    # Check all enrollments for this user
    all_enrollments = Enrollment.objects.filter(student=user)
    print(f'All enrollments for user: {all_enrollments.count()}')
    for enr in all_enrollments:
        print(f'  - Course: {enr.course.title}, Status: {enr.status}')

if __name__ == "__main__":
    main()
