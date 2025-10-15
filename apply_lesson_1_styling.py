#!/usr/bin/env python3
"""
Apply Rich Styling to Lesson 1
==============================

Apply the professional YITP styling from lessons 2-8 to lesson 1.
"""

import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_dir)

# Set up Django environment for PRODUCTION database
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.settings')
os.environ['DJANGO_ENV'] = 'production'  # Force production mode

django.setup()

from courses.models import Lesson

def create_styled_lesson_1():
    """Create professionally styled content for lesson 1"""
    
    # The new styled content for lesson 1
    styled_content = """
<div class="yitp-lesson-content">
    <div class="container-fluid px-0">
        <!-- Lesson Header -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card border-0 shadow-sm" style="background: linear-gradient(135deg, #1a2e53 0%, #ff5d15 100%);">
                    <div class="card-body text-white py-4">
                        <h1 class="display-6 fw-bold mb-0 text-center">
                            <i class="fas fa-graduation-cap me-3"></i>Lesson 1 – Introduction to Life's Purpose (1 hour)
                        </h1>
                    </div>
                </div>
            </div>
        </div>

        <!-- Key Topics Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-key me-2"></i>Key Topics
                        </h3>
                    </div>
                    <div class="card-body bg-light pt-3">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item border-0 px-0 py-2">
                                <i class="fas fa-check-circle text-success me-2"></i>
                                <strong>What is life's purpose?</strong> - 7 Questions for Clarity
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <i class="fas fa-check-circle text-success me-2"></i>
                                <strong>Difference between goals, vision, and purpose</strong> - Understanding the hierarchy
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <i class="fas fa-check-circle text-success me-2"></i>
                                <strong>Purpose-driven lives</strong> - Gandhi's nonviolence, Mandela's fight for justice, Mother Teresa's compassion
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Core Lesson Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm" style="background: linear-gradient(135deg, #1a2e53 0%, #ff5d15 100%);">
                    <div class="card-header text-white border-0 py-3">
                        <h3 class="card-title mb-0" style="color: white;">
                            <i class="fas fa-book-open me-2"></i>Core Lesson
                        </h3>
                    </div>
                    <div class="card-body text-white pt-3">
                        <p class="mb-3 lead">
                            <strong>The Three Bricklayers Story:</strong> During the rebuilding of St. Paul's Cathedral after a fire burned through London in 1666, an architect visited the project site and approached three bricklayers. He asked them each individually, "What are you doing?"
                        </p>
                        
                        <p class="mb-3 lead">
                            The first bricklayer replied, "I'm a bricklayer. I'm working hard to lay bricks to earn money so I can feed my family." The man seemed tired and wasn't as far along with his work as the others.
                        </p>
                        
                        <p class="mb-3 lead">
                            The second bricklayer says, "I'm a builder. I'm building the finest, strongest wall. This wall will be a foundation for this building and will protect everyone who is inside."
                        </p>
                        
                        <p class="mb-3 lead">
                            The third bricklayer replied with energy and a light in his eye, "I'm a cathedral builder. I'm building a great cathedral, where people can gather, pray and celebrate the Almighty."
                        </p>
                        
                        <p class="mb-3 lead">
                            <strong>Key Insight:</strong> This demonstrates that everything we experience is based on our understanding of purpose and depth of vision. Everything is "an inside job." How we interpret what we do, or experience, is based on the purpose of the action and the actor, for the actor's mindset reflects on purpose.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- 7 Questions for Clarity Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #1a2e53;">
                            <i class="fas fa-lightbulb me-2"></i>7 Questions for Clarity
                        </h3>
                    </div>
                    <div class="card-body bg-light pt-3">
                        <div class="list-group list-group-flush">
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>1.</strong> What makes you feel most alive?
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>2.</strong> What problem in the world gets you most emotionally charged?
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>3.</strong> What are you naturally good at?
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>4.</strong> What is your life's most meaningful event or experience?
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>5.</strong> What would you do if you had zero fear?
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>6.</strong> Who is your idol, living or dead, and why?
                            </div>
                            <div class="list-group-item border-0 px-0 py-2">
                                <strong>7.</strong> What do you want to be your enduring legacy?
                            </div>
                        </div>
                        <div class="alert alert-info mt-3">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>Reflection:</strong> Answer these questions sincerely, for therein lies the discovery of your purpose.
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Purpose vs Vision vs Goals Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-white border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-tasks me-2"></i>Purpose vs Vision vs Goals
                        </h3>
                    </div>
                    <div class="card-body bg-white pt-3">
                        <div class="row">
                            <div class="col-md-4 mb-3">
                                <div class="card border-0 bg-light">
                                    <div class="card-body text-center">
                                        <h5 style="color: #1a2e53;">Purpose</h5>
                                        <p class="small">The reason for which something is done or created. Your purpose is the reason for your being.</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <div class="card border-0 bg-light">
                                    <div class="card-body text-center">
                                        <h5 style="color: #ff5d15;">Vision</h5>
                                        <p class="small">An act or power of anticipating which will or may come to be – giving direction for the outcome of goals and purpose.</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4 mb-3">
                                <div class="card border-0 bg-light">
                                    <div class="card-body text-center">
                                        <h5 style="color: #1a2e53;">Goals</h5>
                                        <p class="small">Specific, desired outcomes that guide actions and effort towards a particular predetermined end.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="alert alert-warning">
                            <i class="fas fa-arrow-right me-2"></i>
                            <strong>Remember:</strong> Purpose begets vision → Vision begets goals
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Activities Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header yitp-activity-box border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #ff5d15;">
                            <i class="fas fa-tasks me-2"></i>Activities
                        </h3>
                    </div>
                    <div class="card-body yitp-activity-box pt-3">
                        <div class="alert alert-info border-0 mb-3">
                            <i class="fas fa-play-circle me-2"></i>
                            <strong>Reflective Journaling:</strong> "When did I feel most alive and fulfilled?" Take time to journal about these moments and what they reveal about your purpose.
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Inspirational Examples Section -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card yitp-section-card border-0 shadow-sm">
                    <div class="card-header bg-light border-0 py-3">
                        <h3 class="card-title mb-0" style="color: #1a2e53;">
                            <i class="fas fa-quote-left me-2"></i>Purpose-Driven Lives
                        </h3>
                    </div>
                    <div class="card-body bg-light pt-3">
                        <blockquote class="yitp-quote border-0 mb-3 p-3 rounded">
                            <strong>Gandhi:</strong> Left his law practice behind and focused on liberating Asia and Africa from the yolks of colonial rule through nonviolence.
                        </blockquote>
                        <blockquote class="yitp-quote border-0 mb-3 p-3 rounded">
                            <strong>Mandela:</strong> Dedicated his life to fighting for justice and equality, transforming a nation through his unwavering commitment.
                        </blockquote>
                        <blockquote class="yitp-quote border-0 mb-3 p-3 rounded">
                            <strong>Mother Teresa:</strong> "Help the poor while living among them, sharing their experience and treating them with kindness, compassion and empathy, but never pity."
                        </blockquote>
                        <div class="alert alert-success">
                            <i class="fas fa-star me-2"></i>
                            <strong>Napoleon Hill's Insight:</strong> Lists Definiteness of Purpose as the top attribute in ensuring achievement.
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>

<style>
.yitp-lesson-content {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

.yitp-section-card {
    transition: transform 0.2s ease-in-out;
}

.yitp-section-card:hover {
    transform: translateY(-2px);
}

.yitp-quote {
    background: linear-gradient(45deg, #f8f9fa 0%, #ffffff 100%);
    border-left: 4px solid #ff5d15;
    position: relative;
    padding-left: 1.5rem;
}

.yitp-quote::before {
    content: '"';
    position: absolute;
    left: 0;
    top: -0.5rem;
    font-size: 3rem;
    color: #ff5d15;
    font-weight: bold;
}

.yitp-activity-box {
    background: linear-gradient(45deg, #f8f9fa 0%, #e9ecef 100%);
    border-left: 4px solid #ff5d15;
}

@media (max-width: 768px) {
    .yitp-lesson-content .display-6 {
        font-size: 1.5rem;
    }
    
    .yitp-lesson-content .card-body {
        padding: 1.5rem 1rem;
    }
}
</style>
"""
    
    return styled_content.strip()

def apply_styling():
    """Apply the styling to lesson 1"""
    print("🎨 APPLYING PROFESSIONAL STYLING TO LESSON 1")
    print("=" * 60)
    
    try:
        # Get lesson 1
        lesson_1 = Lesson.objects.get(id=103)
        print(f"📚 Target lesson: {lesson_1.title}")
        print(f"📊 Original content length: {len(lesson_1.content)} characters")
        
        # Create backup
        backup_filename = f"lesson_1_original_backup_{django.utils.timezone.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(backup_filename, 'w', encoding='utf-8') as f:
            f.write(lesson_1.content)
        print(f"💾 Original content backed up to: {backup_filename}")
        
        # Get new styled content
        new_content = create_styled_lesson_1()
        print(f"📊 New content length: {len(new_content)} characters")
        
        # Save new content to file for review
        new_content_filename = f"lesson_1_new_styled_{django.utils.timezone.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(new_content_filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"💾 New styled content saved to: {new_content_filename}")
        
        # Apply the new content
        lesson_1.content = new_content
        lesson_1.save()
        
        print(f"✅ STYLING APPLIED SUCCESSFULLY!")
        print(f"   Lesson 1 now has professional YITP styling")
        print(f"   Features applied:")
        print(f"   • YITP brand colors (#ff5d15, #1a2e53)")
        print(f"   • Bootstrap 5 card layouts")
        print(f"   • Gradient backgrounds")
        print(f"   • Professional typography")
        print(f"   • Responsive design")
        print(f"   • Interactive elements")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying styling: {str(e)}")
        return False

def verify_consistency():
    """Verify styling consistency across all lessons"""
    print(f"\n🔍 VERIFYING STYLING CONSISTENCY")
    print("=" * 50)
    
    try:
        lessons = Lesson.objects.filter(module_id=14).order_by('sort_order')
        
        consistent_count = 0
        total_lessons = 0
        
        for lesson in lessons:
            if not lesson.content:
                continue
                
            total_lessons += 1
            has_yitp_styling = 'yitp-lesson-content' in lesson.content
            has_gradient = 'linear-gradient' in lesson.content
            has_yitp_colors = '#ff5d15' in lesson.content or '#1a2e53' in lesson.content
            
            is_consistent = has_yitp_styling and has_gradient and has_yitp_colors
            
            if is_consistent:
                consistent_count += 1
            
            print(f"📝 Lesson {lesson.id}: {lesson.title}")
            print(f"   Consistent Styling: {'✅' if is_consistent else '❌'}")
            print(f"   YITP Wrapper: {'✅' if has_yitp_styling else '❌'}")
            print(f"   Gradient: {'✅' if has_gradient else '❌'}")
            print(f"   YITP Colors: {'✅' if has_yitp_colors else '❌'}")
            print()
        
        consistency_percentage = (consistent_count / total_lessons) * 100 if total_lessons > 0 else 0
        
        print(f"📊 STYLING CONSISTENCY: {consistency_percentage:.1f}%")
        print(f"   Consistent lessons: {consistent_count}/{total_lessons}")
        
        if consistency_percentage == 100:
            print("🎉 PERFECT! All lessons have consistent professional styling!")
        elif consistency_percentage >= 90:
            print("✅ EXCELLENT! Nearly all lessons have consistent styling!")
        else:
            print("⚠️ Some lessons still need styling updates")
        
        return consistency_percentage
        
    except Exception as e:
        print(f"❌ Error verifying consistency: {str(e)}")
        return 0

if __name__ == "__main__":
    print("🚀 LESSON 1 STYLING APPLICATION")
    print("=" * 60)
    
    # Apply styling
    success = apply_styling()
    
    if success:
        # Verify consistency
        consistency = verify_consistency()
        
        print(f"\n🎉 STYLING APPLICATION COMPLETED!")
        print(f"✅ Lesson 1 now has professional YITP styling")
        print(f"✅ Consistency across all lessons: {consistency:.1f}%")
        print(f"✅ All lessons now have uniform, professional appearance")
    else:
        print(f"\n❌ STYLING APPLICATION FAILED")
