#!/usr/bin/env python3
"""
Verify that all modules (3, 4, 5) short-answer to multiple-choice conversion was successful
and test that the entire YITP course is now free of problematic short-answer questions
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
django.setup()

from django.contrib.auth.models import User
from courses.models import Course, Module, Lesson
from assessments.models import Quiz, Question
from progress.models import QuizAttempt

class AllModulesConversionVerifier:
    def __init__(self):
        self.verification_results = {
            'modules_scanned': {},
            'total_questions': 0,
            'multiple_choice_questions': 0,
            'short_answer_questions': 0,
            'conversion_success_rate': 0,
            'problematic_questions': []
        }
    
    def verify_all_modules_conversion(self):
        """Verify conversion across all 5 modules"""
        
        print("🔍 VERIFYING ALL MODULES CONVERSION")
        print("=" * 60)
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
            print(f"✅ Found course: {course.title}")
        except Course.DoesNotExist:
            print(f"❌ Course not found")
            return False
        
        total_questions = 0
        total_mc_questions = 0
        total_sa_questions = 0
        
        for module_num in range(1, 6):
            try:
                module = Module.objects.get(course=course, sort_order=module_num)
                print(f"\n📚 Module {module_num}: {module.title}")
                
                lessons = Lesson.objects.filter(module=module).order_by('sort_order')
                module_questions = 0
                module_mc = 0
                module_sa = 0
                
                for lesson in lessons:
                    quizzes = Quiz.objects.filter(lesson=lesson)
                    
                    for quiz in quizzes:
                        questions = Question.objects.filter(quiz=quiz)
                        mc_questions = questions.filter(question_type='multiple_choice')
                        sa_questions = questions.filter(question_type='short_answer')
                        
                        lesson_total = questions.count()
                        lesson_mc = mc_questions.count()
                        lesson_sa = sa_questions.count()
                        
                        module_questions += lesson_total
                        module_mc += lesson_mc
                        module_sa += lesson_sa
                        
                        if lesson_sa > 0:
                            print(f"   ⚠️  {lesson.title} - {quiz.title}: {lesson_sa} short-answer questions remain")
                            
                            # Log problematic questions
                            for sa_question in sa_questions:
                                self.verification_results['problematic_questions'].append({
                                    'module_num': module_num,
                                    'module_title': module.title,
                                    'lesson_title': lesson.title,
                                    'quiz_title': quiz.title,
                                    'question_id': sa_question.id,
                                    'question_text': sa_question.question_text[:100] + "...",
                                    'current_answer': sa_question.correct_answer[:100] + "..."
                                })
                        else:
                            print(f"   ✅ {lesson.title} - {quiz.title}: All questions converted")
                
                total_questions += module_questions
                total_mc_questions += module_mc
                total_sa_questions += module_sa
                
                # Determine module status
                if module_num == 1:
                    status = "✅ WORKS FINE (No conversion needed)"
                elif module_num == 2:
                    status = "✅ ALREADY CONVERTED" if module_sa == 0 else "⚠️  CONVERSION INCOMPLETE"
                elif module_num in [3, 4, 5]:
                    status = "✅ CONVERSION SUCCESSFUL" if module_sa == 0 else "❌ CONVERSION FAILED"
                else:
                    status = "❓ UNKNOWN"
                
                print(f"   📊 Questions: {module_questions} total, {module_mc} MC, {module_sa} SA - {status}")
                
                self.verification_results['modules_scanned'][module_num] = {
                    'module_title': module.title,
                    'total_questions': module_questions,
                    'multiple_choice': module_mc,
                    'short_answer': module_sa,
                    'status': status,
                    'conversion_complete': module_sa == 0
                }
                
            except Module.DoesNotExist:
                print(f"   ❌ Module {module_num} not found")
        
        # Update overall results
        self.verification_results['total_questions'] = total_questions
        self.verification_results['multiple_choice_questions'] = total_mc_questions
        self.verification_results['short_answer_questions'] = total_sa_questions
        
        if total_questions > 0:
            self.verification_results['conversion_success_rate'] = (total_mc_questions / total_questions) * 100
        
        print(f"\n📊 OVERALL VERIFICATION RESULTS:")
        print(f"   • Total questions: {total_questions}")
        print(f"   • Multiple choice: {total_mc_questions}")
        print(f"   • Short answer remaining: {total_sa_questions}")
        print(f"   • Conversion rate: {self.verification_results['conversion_success_rate']:.1f}%")
        
        if total_sa_questions == 0:
            print(f"   ✅ ALL MODULES SUCCESSFULLY CONVERTED!")
            return True
        else:
            print(f"   ⚠️  {total_sa_questions} short-answer questions still remain")
            return False
    
    def test_quiz_passability_across_modules(self):
        """Test that quizzes are passable across all modules"""
        
        print(f"\n🧪 TESTING QUIZ PASSABILITY ACROSS ALL MODULES")
        print("=" * 60)
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        except Course.DoesNotExist:
            print(f"❌ Course not found")
            return False
        
        passability_results = []
        all_passable = True
        
        for module_num in range(1, 6):
            try:
                module = Module.objects.get(course=course, sort_order=module_num)
                print(f"\n📚 Testing Module {module_num}: {module.title}")
                
                lessons = Lesson.objects.filter(module=module).order_by('sort_order')
                
                for lesson in lessons:
                    quizzes = Quiz.objects.filter(lesson=lesson)
                    
                    for quiz in quizzes:
                        questions = Question.objects.filter(quiz=quiz)
                        mc_questions = questions.filter(question_type='multiple_choice')
                        tf_questions = questions.filter(question_type='true_false')
                        
                        # Calculate points from answerable questions (MC + TF)
                        answerable_points = sum(q.points for q in mc_questions) + sum(q.points for q in tf_questions)
                        total_points = sum(q.points for q in questions)
                        
                        if total_points > 0:
                            answerable_percentage = (answerable_points / total_points) * 100
                            is_passable = answerable_percentage >= quiz.passing_score
                            
                            status = "✅ PASSABLE" if is_passable else "❌ NOT PASSABLE"
                            print(f"   {status} {lesson.title} - {quiz.title}")
                            print(f"      📊 Answerable: {answerable_percentage:.1f}% (need {quiz.passing_score}%)")
                            
                            if not is_passable:
                                all_passable = False
                            
                            passability_results.append({
                                'module_num': module_num,
                                'module_title': module.title,
                                'lesson_title': lesson.title,
                                'quiz_title': quiz.title,
                                'total_questions': questions.count(),
                                'answerable_questions': mc_questions.count() + tf_questions.count(),
                                'answerable_percentage': answerable_percentage,
                                'passing_score': quiz.passing_score,
                                'is_passable': is_passable
                            })
                
            except Module.DoesNotExist:
                print(f"   ❌ Module {module_num} not found")
        
        print(f"\n📊 PASSABILITY SUMMARY:")
        passable_count = sum(1 for r in passability_results if r['is_passable'])
        print(f"   • Total quizzes tested: {len(passability_results)}")
        print(f"   • Passable quizzes: {passable_count}")
        print(f"   • Success rate: {(passable_count/len(passability_results)*100):.1f}%")
        
        if all_passable:
            print(f"   ✅ ALL QUIZZES ARE PASSABLE!")
        else:
            print(f"   ⚠️  Some quizzes may still have issues")
        
        return all_passable, passability_results
    
    def simulate_user_success_across_modules(self):
        """Simulate user success across all modules"""
        
        print(f"\n🎮 SIMULATING USER SUCCESS ACROSS ALL MODULES")
        print("=" * 60)
        
        try:
            user = User.objects.get(email='bomondi2727@gmail.com')
            print(f"✅ Testing with user: {user.username} ({user.email})")
        except User.DoesNotExist:
            print(f"⚠️  User not found, using simulation only")
            user = None
        
        try:
            course = Course.objects.get(slug='youth-impact-training-programme-yitp')
        except Course.DoesNotExist:
            print(f"❌ Course not found")
            return False
        
        simulation_results = []
        overall_success = True
        
        for module_num in range(1, 6):
            try:
                module = Module.objects.get(course=course, sort_order=module_num)
                print(f"\n📚 Simulating Module {module_num}: {module.title}")
                
                # Test first lesson quiz as representative
                lesson = Lesson.objects.filter(module=module).order_by('sort_order').first()
                if lesson:
                    quiz = Quiz.objects.filter(lesson=lesson).first()
                    if quiz:
                        questions = Question.objects.filter(quiz=quiz)
                        mc_questions = questions.filter(question_type='multiple_choice')
                        tf_questions = questions.filter(question_type='true_false')
                        
                        # Simulate perfect score on answerable questions
                        answerable_points = sum(q.points for q in mc_questions) + sum(q.points for q in tf_questions)
                        total_points = sum(q.points for q in questions)
                        
                        if total_points > 0:
                            simulated_score = (answerable_points / total_points) * 100
                            would_pass = simulated_score >= quiz.passing_score
                            
                            status = "✅ PASS" if would_pass else "❌ FAIL"
                            print(f"   {status} {lesson.title} - {quiz.title}")
                            print(f"      🎯 Simulated score: {simulated_score:.1f}% (need {quiz.passing_score}%)")
                            
                            if not would_pass:
                                overall_success = False
                            
                            simulation_results.append({
                                'module_num': module_num,
                                'module_title': module.title,
                                'lesson_title': lesson.title,
                                'quiz_title': quiz.title,
                                'simulated_score': simulated_score,
                                'passing_score': quiz.passing_score,
                                'would_pass': would_pass
                            })
                
            except Module.DoesNotExist:
                print(f"   ❌ Module {module_num} not found")
        
        print(f"\n📊 SIMULATION SUMMARY:")
        passing_count = sum(1 for r in simulation_results if r['would_pass'])
        print(f"   • Modules tested: {len(simulation_results)}")
        print(f"   • Modules user would pass: {passing_count}")
        print(f"   • Success rate: {(passing_count/len(simulation_results)*100):.1f}%")
        
        if overall_success:
            print(f"   ✅ USER SHOULD BE ABLE TO PASS ALL MODULES!")
        else:
            print(f"   ⚠️  User may still have issues with some modules")
        
        return overall_success, simulation_results

    def generate_comprehensive_verification_report(self, passability_results, simulation_results):
        """Generate comprehensive verification report"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"all_modules_verification_report_{timestamp}.md"

        report_content = f"""# All Modules Conversion Verification Report

## Summary
- **Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Course:** Youth Impact Training Programme (YITP)
- **Total Questions:** {self.verification_results['total_questions']}
- **Multiple Choice:** {self.verification_results['multiple_choice_questions']}
- **Short Answer Remaining:** {self.verification_results['short_answer_questions']}
- **Conversion Success Rate:** {self.verification_results['conversion_success_rate']:.1f}%

## Module-by-Module Analysis

"""

        for module_num, result in self.verification_results['modules_scanned'].items():
            status_emoji = "✅" if result['conversion_complete'] else "⚠️"
            report_content += f"""### Module {module_num}: {result['module_title']} {status_emoji}
- **Total Questions:** {result['total_questions']}
- **Multiple Choice:** {result['multiple_choice']}
- **Short Answer:** {result['short_answer']}
- **Status:** {result['status']}

"""

        # Problematic questions
        if self.verification_results['problematic_questions']:
            report_content += f"""## Remaining Problematic Questions

"""
            for problem in self.verification_results['problematic_questions']:
                report_content += f"""### Module {problem['module_num']}: {problem['question_id']}
- **Lesson:** {problem['lesson_title']}
- **Quiz:** {problem['quiz_title']}
- **Question:** {problem['question_text']}
- **Current Answer:** {problem['current_answer']}

"""

        # Passability results
        report_content += f"""## Quiz Passability Analysis

"""
        for result in passability_results:
            status = "✅ PASSABLE" if result['is_passable'] else "❌ NOT PASSABLE"
            report_content += f"""### Module {result['module_num']}: {result['lesson_title']} {status}
- **Quiz:** {result['quiz_title']}
- **Answerable Questions:** {result['answerable_questions']}/{result['total_questions']}
- **Answerable Percentage:** {result['answerable_percentage']:.1f}%
- **Required:** {result['passing_score']}%

"""

        # Simulation results
        report_content += f"""## User Success Simulation

"""
        for result in simulation_results:
            status = "✅ PASS" if result['would_pass'] else "❌ FAIL"
            report_content += f"""### Module {result['module_num']}: {result['lesson_title']} {status}
- **Quiz:** {result['quiz_title']}
- **Simulated Score:** {result['simulated_score']:.1f}%
- **Required:** {result['passing_score']}%

"""

        # Recommendations
        if self.verification_results['short_answer_questions'] == 0:
            report_content += f"""## Conclusion ✅

**CONVERSION SUCCESSFUL!** All short-answer questions have been successfully converted to multiple-choice format across all modules. Users should now be able to pass quizzes without encountering exact string matching issues.

## Recommendations

1. ✅ **Immediate Action:** Notify affected users they can retry failed quizzes
2. 📊 **Monitor:** Track quiz pass rates over the next week
3. 🔄 **Expand:** Document the conversion process for future use
4. 📝 **Update:** Revise instructor guides to reflect new question formats

"""
        else:
            report_content += f"""## Conclusion ⚠️

**CONVERSION INCOMPLETE!** {self.verification_results['short_answer_questions']} short-answer questions still remain. Additional conversion work is needed.

## Recommendations

1. 🔧 **Immediate Action:** Run conversion script again for remaining questions
2. 🔍 **Investigate:** Review why some questions were not converted
3. 📊 **Monitor:** Continue tracking user quiz attempts
4. 🆘 **Support:** Provide manual assistance to affected users

"""

        report_content += f"""---
*Report generated by verify_all_modules_conversion.py*
"""

        try:
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(report_content)

            print(f"📄 Comprehensive verification report saved: {report_filename}")
            return report_filename

        except Exception as e:
            print(f"❌ Error saving report: {e}")
            return None

def main():
    print("🔍 VERIFYING ALL MODULES CONVERSION SUCCESS")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    verifier = AllModulesConversionVerifier()

    # Step 1: Verify all conversions
    conversion_complete = verifier.verify_all_modules_conversion()

    # Step 2: Test quiz passability
    passability_success, passability_results = verifier.test_quiz_passability_across_modules()

    # Step 3: Simulate user success
    simulation_success, simulation_results = verifier.simulate_user_success_across_modules()

    # Step 4: Generate comprehensive report
    report_file = verifier.generate_comprehensive_verification_report(passability_results, simulation_results)

    # Final summary
    print(f"\n🎉 VERIFICATION COMPLETED!")
    print("=" * 60)

    if conversion_complete:
        print(f"✅ CONVERSION SUCCESS: All short-answer questions converted")
    else:
        print(f"⚠️  CONVERSION INCOMPLETE: Some short-answer questions remain")

    if passability_success:
        print(f"✅ PASSABILITY SUCCESS: All quizzes are passable")
    else:
        print(f"⚠️  PASSABILITY ISSUES: Some quizzes may still have problems")

    if simulation_success:
        print(f"✅ SIMULATION SUCCESS: Users should be able to pass all modules")
    else:
        print(f"⚠️  SIMULATION ISSUES: Users may still face difficulties")

    overall_success = conversion_complete and passability_success and simulation_success

    if overall_success:
        print(f"\n🎯 OVERALL RESULT: ✅ COMPLETE SUCCESS!")
        print(f"   • All modules converted successfully")
        print(f"   • All quizzes are passable")
        print(f"   • Users should have no more lockout issues")
    else:
        print(f"\n🎯 OVERALL RESULT: ⚠️  PARTIAL SUCCESS")
        print(f"   • Some issues remain - see report for details")

    if report_file:
        print(f"\n📄 Detailed report: {report_file}")

    print(f"\n🔄 Next Steps:")
    if overall_success:
        print(f"1. 📢 Notify users they can retry failed quizzes")
        print(f"2. 📊 Monitor quiz pass rates")
        print(f"3. 📝 Update documentation")
    else:
        print(f"1. 🔧 Address remaining conversion issues")
        print(f"2. 🔄 Re-run conversion scripts as needed")
        print(f"3. 🧪 Test again after fixes")

if __name__ == "__main__":
    main()
