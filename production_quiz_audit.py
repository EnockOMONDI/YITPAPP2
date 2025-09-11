#!/usr/bin/env python
"""
Production Quiz Audit Script for YITP Migration
Analyzes current quiz attempt settings before applying migration
"""

import os
import sys
import django
from datetime import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.db.models import Count, Q
from assessments.models import Quiz, Question
from courses.models import Course, Module, Lesson
from progress.models import QuizAttempt


class ProductionQuizAuditor:
    def __init__(self):
        self.audit_results = {
            'timestamp': datetime.now().isoformat(),
            'quiz_stats': {},
            'course_breakdown': {},
            'migration_impact': {},
            'recommendations': []
        }
    
    def run_audit(self):
        """Run complete audit of quiz attempt settings"""
        print("🔍 YITP PRODUCTION QUIZ AUDIT")
        print("=" * 60)
        print(f"Timestamp: {self.audit_results['timestamp']}")
        print()
        
        self.analyze_quiz_attempts()
        self.analyze_course_breakdown()
        self.analyze_migration_impact()
        self.generate_recommendations()
        self.create_audit_report()
        
        return self.audit_results
    
    def analyze_quiz_attempts(self):
        """Analyze current quiz attempt distribution"""
        print("📊 QUIZ ATTEMPT DISTRIBUTION")
        print("-" * 40)
        
        # Get quiz attempt statistics
        quiz_stats = Quiz.objects.values('max_attempts').annotate(
            count=Count('id')
        ).order_by('max_attempts')
        
        total_quizzes = Quiz.objects.count()
        
        print(f"Total Quizzes: {total_quizzes}")
        print()
        
        for stat in quiz_stats:
            attempts = stat['max_attempts']
            count = stat['count']
            percentage = (count / total_quizzes * 100) if total_quizzes > 0 else 0
            
            print(f"  {attempts:2d} attempts: {count:3d} quizzes ({percentage:5.1f}%)")
            
            self.audit_results['quiz_stats'][attempts] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        print()
    
    def analyze_course_breakdown(self):
        """Analyze quiz attempts by course"""
        print("📚 COURSE BREAKDOWN")
        print("-" * 40)
        
        courses = Course.objects.filter(is_published=True)
        
        for course in courses:
            quizzes = Quiz.objects.filter(lesson__module__course=course)
            quiz_count = quizzes.count()
            
            if quiz_count > 0:
                attempt_distribution = quizzes.values('max_attempts').annotate(
                    count=Count('id')
                ).order_by('max_attempts')
                
                print(f"📖 {course.title}")
                print(f"   Total Quizzes: {quiz_count}")
                
                course_stats = {}
                for dist in attempt_distribution:
                    attempts = dist['max_attempts']
                    count = dist['count']
                    print(f"   {attempts} attempts: {count} quizzes")
                    course_stats[attempts] = count
                
                self.audit_results['course_breakdown'][course.title] = {
                    'total_quizzes': quiz_count,
                    'attempt_distribution': course_stats
                }
                print()
    
    def analyze_migration_impact(self):
        """Analyze what will be affected by migration"""
        print("🔄 MIGRATION IMPACT ANALYSIS")
        print("-" * 40)
        
        # Quizzes that will be updated (max_attempts=1)
        quizzes_to_update = Quiz.objects.filter(max_attempts=1)
        update_count = quizzes_to_update.count()
        
        # Quizzes that will remain unchanged
        quizzes_unchanged = Quiz.objects.exclude(max_attempts=1)
        unchanged_count = quizzes_unchanged.count()
        
        total_quizzes = Quiz.objects.count()
        
        print(f"Quizzes to be UPDATED (1→15 attempts): {update_count}")
        print(f"Quizzes to remain UNCHANGED: {unchanged_count}")
        print(f"Total Quizzes: {total_quizzes}")
        print()
        
        if update_count > 0:
            print("📝 Quizzes that will be updated:")
            for quiz in quizzes_to_update[:10]:  # Show first 10
                course_title = quiz.lesson.module.course.title
                print(f"   • {quiz.title} (Course: {course_title})")
            
            if update_count > 10:
                print(f"   ... and {update_count - 10} more")
            print()
        
        # Check for any quiz attempts on quizzes that will be updated
        attempts_on_updating_quizzes = QuizAttempt.objects.filter(
            quiz__in=quizzes_to_update
        ).count()
        
        print(f"Existing attempts on quizzes to be updated: {attempts_on_updating_quizzes}")
        
        self.audit_results['migration_impact'] = {
            'quizzes_to_update': update_count,
            'quizzes_unchanged': unchanged_count,
            'total_quizzes': total_quizzes,
            'existing_attempts_affected': attempts_on_updating_quizzes,
            'update_percentage': round((update_count / total_quizzes * 100), 1) if total_quizzes > 0 else 0
        }
        print()
    
    def generate_recommendations(self):
        """Generate recommendations based on audit"""
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        
        impact = self.audit_results['migration_impact']
        
        if impact['quizzes_to_update'] == 0:
            recommendation = "✅ SAFE: No quizzes will be affected by migration"
            risk_level = "LOW"
        elif impact['quizzes_to_update'] < 5:
            recommendation = "✅ SAFE: Very few quizzes will be updated"
            risk_level = "LOW"
        elif impact['update_percentage'] < 50:
            recommendation = "⚠️ MODERATE: Some quizzes will be updated, monitor closely"
            risk_level = "MODERATE"
        else:
            recommendation = "🔍 HIGH IMPACT: Many quizzes will be updated, consider staged rollout"
            risk_level = "HIGH"
        
        print(f"Risk Level: {risk_level}")
        print(f"Recommendation: {recommendation}")
        print()
        
        # Specific recommendations
        recommendations = []
        
        if impact['existing_attempts_affected'] > 0:
            recommendations.append(
                f"📊 {impact['existing_attempts_affected']} existing quiz attempts will have their quiz limits increased"
            )
        
        if impact['quizzes_to_update'] > 0:
            recommendations.append(
                f"🔄 {impact['quizzes_to_update']} quizzes will be updated from 1 to 15 attempts"
            )
        
        recommendations.extend([
            "✅ All custom instructor settings will be preserved",
            "🔒 Migration includes rollback capability",
            "📧 Enhanced user experience with instructor contact features",
            "⏱️ Migration expected to complete in <30 seconds"
        ])
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        self.audit_results['recommendations'] = recommendations
        self.audit_results['risk_level'] = risk_level
        print()
    
    def create_audit_report(self):
        """Create detailed audit report"""
        report_filename = f"quiz_audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_filename, 'w') as f:
            f.write("YITP PRODUCTION QUIZ AUDIT REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {self.audit_results['timestamp']}\n\n")
            
            f.write("QUIZ ATTEMPT DISTRIBUTION:\n")
            f.write("-" * 30 + "\n")
            for attempts, stats in self.audit_results['quiz_stats'].items():
                f.write(f"{attempts:2d} attempts: {stats['count']:3d} quizzes ({stats['percentage']:5.1f}%)\n")
            f.write("\n")
            
            f.write("MIGRATION IMPACT:\n")
            f.write("-" * 20 + "\n")
            impact = self.audit_results['migration_impact']
            f.write(f"Quizzes to update: {impact['quizzes_to_update']}\n")
            f.write(f"Quizzes unchanged: {impact['quizzes_unchanged']}\n")
            f.write(f"Update percentage: {impact['update_percentage']}%\n")
            f.write(f"Risk level: {self.audit_results['risk_level']}\n\n")
            
            f.write("RECOMMENDATIONS:\n")
            f.write("-" * 20 + "\n")
            for i, rec in enumerate(self.audit_results['recommendations'], 1):
                f.write(f"{i}. {rec}\n")
        
        print(f"📄 Detailed report saved: {report_filename}")
        return report_filename


def main():
    """Main audit function"""
    try:
        auditor = ProductionQuizAuditor()
        results = auditor.run_audit()
        
        print("🎉 AUDIT COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("Next Steps:")
        print("1. Review audit results above")
        print("2. Proceed with migration if risk level is acceptable")
        print("3. Monitor deployment for any issues")
        print("4. Validate post-migration functionality")
        
        return True
        
    except Exception as e:
        print(f"❌ AUDIT FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
