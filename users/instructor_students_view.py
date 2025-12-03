class InstructorStudentsView(LoginRequiredMixin, InstructorRequiredMixin, ListView):
    """List view of students enrolled in instructor's modules"""
    template_name = 'instructor/students.html'
    context_object_name = 'students'
    paginate_by = 20
    
    def get_queryset(self):
        instructor = self.request.user
        instructor_profile = instructor.instructor_profile
        
        # Get all modules assigned to this instructor
        if instructor_profile.instructor_role == 'system_admin':
            assigned_modules = Module.objects.all()
        else:
            assigned_modules = Module.objects.filter(
                module_instructors__instructor=instructor,
                module_instructors__is_active=True
            ).distinct()
        
        # Get all courses for these modules
        course_ids = list(assigned_modules.values_list('course_id', flat=True).distinct())
        
        # Get all enrollments for these courses
        enrollments = Enrollment.objects.filter(
            course_id__in=course_ids,
            status='active'
        ).select_related('student', 'student__profile', 'course')
        
        # Group by student and calculate stats
        from collections import defaultdict
        student_stats = defaultdict(lambda: {
            'student': None,
            'enrolled_modules': set(),
            'total_progress': [],
            'quiz_scores': [],
            'last_activity': None
        })
        
        for enrollment in enrollments:
            student_id = enrollment.student.id
            student_stats[student_id]['student'] = enrollment.student
            student_stats[student_id]['enrolled_modules'].add(enrollment.course_id)
            student_stats[student_id]['total_progress'].append(float(enrollment.progress_percentage))
            
            # Get last activity
            last_progress = LessonProgress.objects.filter(
                enrollment=enrollment
            ).order_by('-updated_at').first()
            
            if last_progress:
                current_last = student_stats[student_id]['last_activity']
                if not current_last or last_progress.updated_at > current_last:
                    student_stats[student_id]['last_activity'] = last_progress.updated_at
            
            # Get quiz scores
            quiz_attempts = QuizAttempt.objects.filter(
                student=enrollment.student,
                quiz__lesson__module__course_id=enrollment.course_id
            ).values_list('score', flat=True)
            student_stats[student_id]['quiz_scores'].extend(quiz_attempts)
        
        # Convert to list with calculated averages
        students_list = []
        for student_id, stats in student_stats.items():
            avg_progress = sum(stats['total_progress']) / len(stats['total_progress']) if stats['total_progress'] else 0
            avg_quiz_score = sum(stats['quiz_scores']) / len(stats['quiz_scores']) if stats['quiz_scores'] else None
            
            students_list.append({
                'student': stats['student'],
                'enrolled_modules': len(stats['enrolled_modules']),
                'avg_progress': round(avg_progress, 1),
                'avg_quiz_score': round(avg_quiz_score, 1) if avg_quiz_score else None,
                'last_activity': stats['last_activity']
            })
        
        # Apply search filter
        search = self.request.GET.get('search')
        if search:
            students_list = [
                s for s in students_list
                if search.lower() in s['student'].get_full_name().lower() or
                   search.lower() in s['student'].username.lower() or
                   search.lower() in s['student'].email.lower()
            ]
        
        # Sort by last activity (most recent first)
        students_list.sort(key=lambda x: x['last_activity'] or timezone.datetime.min.replace(tzinfo=timezone.utc), reverse=True)
        
        return students_list
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['unread_messages_count'] = Message.objects.filter(
            recipient=self.request.user,
            is_read=False
        ).count()
        return context
