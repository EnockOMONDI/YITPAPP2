"""
Course Builder Templates System
Provides prebuilt templates for courses, lessons, and assessments
"""

# Course Templates
COURSE_TEMPLATES = {
    'business_fundamentals': {
        'title': 'Business Fundamentals',
        'description': 'A comprehensive introduction to business principles and practices',
        'category': 'Business',
        'difficulty_level': 'beginner',
        'estimated_duration': 20,
        'modules': [
            {
                'title': 'Introduction to Business',
                'description': 'Understanding the basics of business operations',
                'lessons': [
                    {
                        'title': 'What is Business?',
                        'content_type': 'text',
                        'estimated_duration': 30,
                        'learning_objectives': 'Define business and understand its role in society'
                    },
                    {
                        'title': 'Types of Business Organizations',
                        'content_type': 'text',
                        'estimated_duration': 45,
                        'learning_objectives': 'Identify different business structures and their characteristics'
                    }
                ]
            },
            {
                'title': 'Business Planning',
                'description': 'Creating effective business plans',
                'lessons': [
                    {
                        'title': 'Market Research',
                        'content_type': 'text',
                        'estimated_duration': 60,
                        'learning_objectives': 'Conduct basic market research and analysis'
                    },
                    {
                        'title': 'Financial Planning',
                        'content_type': 'text',
                        'estimated_duration': 45,
                        'learning_objectives': 'Create basic financial projections and budgets'
                    }
                ]
            }
        ]
    },
    'entrepreneurship_basics': {
        'title': 'Entrepreneurship Basics',
        'description': 'Essential skills and knowledge for aspiring entrepreneurs',
        'category': 'Entrepreneurship',
        'difficulty_level': 'beginner',
        'estimated_duration': 15,
        'modules': [
            {
                'title': 'Entrepreneurial Mindset',
                'description': 'Developing the right mindset for entrepreneurship',
                'lessons': [
                    {
                        'title': 'Identifying Opportunities',
                        'content_type': 'text',
                        'estimated_duration': 30,
                        'learning_objectives': 'Recognize and evaluate business opportunities'
                    },
                    {
                        'title': 'Risk Assessment',
                        'content_type': 'text',
                        'estimated_duration': 45,
                        'learning_objectives': 'Assess and manage entrepreneurial risks'
                    }
                ]
            },
            {
                'title': 'Starting Your Business',
                'description': 'Practical steps to launch a business',
                'lessons': [
                    {
                        'title': 'Business Model Development',
                        'content_type': 'text',
                        'estimated_duration': 60,
                        'learning_objectives': 'Create a viable business model'
                    },
                    {
                        'title': 'Legal Requirements',
                        'content_type': 'text',
                        'estimated_duration': 30,
                        'learning_objectives': 'Understand legal requirements for starting a business'
                    }
                ]
            }
        ]
    },
    'leadership_development': {
        'title': 'Leadership Development',
        'description': 'Building essential leadership skills for modern organizations',
        'category': 'Leadership',
        'difficulty_level': 'intermediate',
        'estimated_duration': 25,
        'modules': [
            {
                'title': 'Leadership Foundations',
                'description': 'Core principles of effective leadership',
                'lessons': [
                    {
                        'title': 'Leadership Styles',
                        'content_type': 'text',
                        'estimated_duration': 45,
                        'learning_objectives': 'Identify different leadership styles and their applications'
                    },
                    {
                        'title': 'Emotional Intelligence',
                        'content_type': 'text',
                        'estimated_duration': 60,
                        'learning_objectives': 'Develop emotional intelligence for better leadership'
                    }
                ]
            },
            {
                'title': 'Team Leadership',
                'description': 'Leading and managing teams effectively',
                'lessons': [
                    {
                        'title': 'Team Building',
                        'content_type': 'text',
                        'estimated_duration': 45,
                        'learning_objectives': 'Build and maintain high-performing teams'
                    },
                    {
                        'title': 'Conflict Resolution',
                        'content_type': 'text',
                        'estimated_duration': 30,
                        'learning_objectives': 'Resolve conflicts and manage difficult situations'
                    }
                ]
            }
        ]
    }
}

# Lesson Templates
LESSON_TEMPLATES = {
    'introduction': {
        'title': 'Introduction to [Topic]',
        'content_type': 'text',
        'estimated_duration': 30,
        'learning_objectives': 'Understand the basic concepts and importance of [topic]',
        'content': '''
<h2>Welcome to [Topic]</h2>

<p>In this lesson, we'll explore the fundamental concepts of [topic] and understand why it's important in today's world.</p>

<h3>What You'll Learn</h3>
<ul>
    <li>Key definitions and terminology</li>
    <li>Historical context and development</li>
    <li>Current applications and relevance</li>
    <li>Future trends and opportunities</li>
</ul>

<div style="background: #fff8e1; border-left: 4px solid #ff5d15; padding: 1rem; margin: 1rem 0;">
    <h4 style="color: #ff5d15; margin-top: 0;">💡 Key Takeaway</h4>
    <p>Understanding [topic] is essential for [specific benefit or application].</p>
</div>

<h3>Getting Started</h3>
<p>Let's begin by exploring the basic concepts...</p>
        '''
    },
    'case_study': {
        'title': '[Topic] Case Study',
        'content_type': 'text',
        'estimated_duration': 45,
        'learning_objectives': 'Analyze real-world applications and learn from practical examples',
        'content': '''
<h2>Case Study: [Case Study Title]</h2>

<h3>Background</h3>
<p>In this case study, we'll examine [brief description of the case].</p>

<h3>The Situation</h3>
<p>[Describe the situation, challenges, and context]</p>

<h3>Key Players</h3>
<ul>
    <li><strong>[Person/Organization 1]:</strong> [Role and significance]</li>
    <li><strong>[Person/Organization 2]:</strong> [Role and significance]</li>
</ul>

<h3>The Challenge</h3>
<p>[Describe the main challenge or problem that needed to be solved]</p>

<h3>The Solution</h3>
<p>[Explain the approach taken and solutions implemented]</p>

<div style="background: #f0f8ff; border: 2px solid #1a2e53; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
    <h4 style="color: #1a2e53; margin-top: 0;">🎯 Analysis Questions</h4>
    <ol>
        <li>What were the key factors that led to success?</li>
        <li>What challenges were encountered and how were they overcome?</li>
        <li>What lessons can be applied to similar situations?</li>
        <li>What would you have done differently?</li>
    </ol>
</div>

<h3>Results and Impact</h3>
<p>[Describe the outcomes and long-term impact]</p>

<h3>Key Lessons</h3>
<ul>
    <li>[Lesson 1]</li>
    <li>[Lesson 2]</li>
    <li>[Lesson 3]</li>
</ul>
        '''
    },
    'practical_exercise': {
        'title': '[Topic] Practical Exercise',
        'content_type': 'text',
        'estimated_duration': 60,
        'learning_objectives': 'Apply theoretical knowledge through hands-on practice',
        'content': '''
<h2>Practical Exercise: [Exercise Title]</h2>

<h3>Objective</h3>
<p>In this exercise, you will [describe what students will accomplish].</p>

<h3>Prerequisites</h3>
<ul>
    <li>[Prerequisite 1]</li>
    <li>[Prerequisite 2]</li>
</ul>

<h3>Materials Needed</h3>
<ul>
    <li>[Material 1]</li>
    <li>[Material 2]</li>
</ul>

<div style="background: #f0f8ff; border: 2px solid #1a2e53; border-radius: 8px; padding: 1rem; margin: 1rem 0;">
    <h4 style="color: #1a2e53; margin-top: 0;">📋 Step-by-Step Instructions</h4>
    <ol>
        <li><strong>Step 1:</strong> [Detailed instruction]</li>
        <li><strong>Step 2:</strong> [Detailed instruction]</li>
        <li><strong>Step 3:</strong> [Detailed instruction]</li>
        <li><strong>Step 4:</strong> [Detailed instruction]</li>
        <li><strong>Step 5:</strong> [Detailed instruction]</li>
    </ol>
</div>

<h3>Expected Outcomes</h3>
<p>Upon completion, you should have [describe expected results].</p>

<h3>Reflection Questions</h3>
<ol>
    <li>What did you learn from this exercise?</li>
    <li>What challenges did you encounter?</li>
    <li>How can you apply this knowledge in real situations?</li>
</ol>

<div style="background: #fff8e1; border-left: 4px solid #ff5d15; padding: 1rem; margin: 1rem 0;">
    <h4 style="color: #ff5d15; margin-top: 0;">💡 Pro Tip</h4>
    <p>[Helpful tip or best practice related to the exercise]</p>
</div>
        '''
    },
    'summary': {
        'title': '[Topic] Summary',
        'content_type': 'text',
        'estimated_duration': 20,
        'learning_objectives': 'Review and consolidate key concepts and takeaways',
        'content': '''
<h2>Summary: [Topic]</h2>

<p>Congratulations on completing this section on [topic]! Let's review the key concepts and takeaways.</p>

<h3>Key Concepts Covered</h3>
<ul>
    <li><strong>[Concept 1]:</strong> [Brief explanation]</li>
    <li><strong>[Concept 2]:</strong> [Brief explanation]</li>
    <li><strong>[Concept 3]:</strong> [Brief explanation]</li>
</ul>

<h3>Main Takeaways</h3>
<ol>
    <li>[Important takeaway 1]</li>
    <li>[Important takeaway 2]</li>
    <li>[Important takeaway 3]</li>
</ol>

<div style="background: #fff8e1; border-left: 4px solid #ff5d15; padding: 1rem; margin: 1rem 0;">
    <h4 style="color: #ff5d15; margin-top: 0;">🎯 Remember</h4>
    <p>[Most important point to remember from this section]</p>
</div>

<h3>Next Steps</h3>
<p>Now that you understand [topic], you're ready to:</p>
<ul>
    <li>[Next step 1]</li>
    <li>[Next step 2]</li>
    <li>[Next step 3]</li>
</ul>

<h3>Additional Resources</h3>
<ul>
    <li><a href="[URL]">[Resource 1]</a></li>
    <li><a href="[URL]">[Resource 2]</a></li>
    <li><a href="[URL]">[Resource 3]</a></li>
</ul>

<p>Keep up the great work and continue to the next section!</p>
        '''
    }
}

# Quiz Templates
QUIZ_TEMPLATES = {
    'knowledge_check': {
        'title': '[Topic] Knowledge Check',
        'description': 'Test your understanding of key concepts',
        'instructions': 'Answer all questions to the best of your ability. You have unlimited attempts.',
        'time_limit': None,
        'max_attempts': 3,
        'passing_score': 70,
        'is_randomized': False,
        'show_results': True,
        'questions': [
            {
                'question_text': 'What is the primary purpose of [concept]?',
                'question_type': 'multiple_choice',
                'options': ['Option A', 'Option B', 'Option C', 'Option D'],
                'correct_answer': '0',
                'points': 2,
                'explanation': 'The correct answer is A because...',
                'sort_order': 1
            },
            {
                'question_text': '[Statement about topic] is true.',
                'question_type': 'true_false',
                'options': [],
                'correct_answer': 'true',
                'points': 1,
                'explanation': 'This statement is true because...',
                'sort_order': 2
            }
        ]
    },
    'comprehensive_assessment': {
        'title': '[Topic] Comprehensive Assessment',
        'description': 'Comprehensive evaluation of your understanding',
        'instructions': 'This assessment covers all major topics. Take your time and answer carefully.',
        'time_limit': 60,
        'max_attempts': 2,
        'passing_score': 75,
        'is_randomized': True,
        'show_results': False,
        'questions': [
            {
                'question_text': 'Explain the relationship between [concept A] and [concept B].',
                'question_type': 'short_answer',
                'options': [],
                'correct_answer': 'Sample answer: The relationship between concept A and B is...',
                'points': 5,
                'explanation': 'A good answer should include...',
                'sort_order': 1
            }
        ]
    }
}

# Assignment Templates
ASSIGNMENT_TEMPLATES = {
    'business_plan': {
        'title': 'Business Plan Development',
        'assignment_type': 'business_plan',
        'description': 'Create a comprehensive business plan for a new venture',
        'instructions': '''
<h2>Business Plan Assignment</h2>

<h3>Objective</h3>
<p>Develop a comprehensive business plan for a new business venture of your choice.</p>

<h3>Requirements</h3>
<p>Your business plan should include the following sections:</p>

<ol>
    <li><strong>Executive Summary</strong> (1-2 pages)</li>
    <li><strong>Company Description</strong> (1 page)</li>
    <li><strong>Market Analysis</strong> (2-3 pages)</li>
    <li><strong>Organization & Management</strong> (1 page)</li>
    <li><strong>Service or Product Line</strong> (1-2 pages)</li>
    <li><strong>Marketing & Sales</strong> (2 pages)</li>
    <li><strong>Financial Projections</strong> (2-3 pages)</li>
    <li><strong>Funding Request</strong> (1 page, if applicable)</li>
</ol>

<h3>Submission Guidelines</h3>
<ul>
    <li>Length: 10-15 pages (excluding appendices)</li>
    <li>Format: Professional business document</li>
    <li>Include charts, graphs, and financial tables where appropriate</li>
    <li>Cite all sources using APA format</li>
</ul>

<h3>Evaluation Criteria</h3>
<p>Your business plan will be evaluated based on:</p>
<ul>
    <li>Completeness and thoroughness of analysis</li>
    <li>Feasibility and realism of the business concept</li>
    <li>Quality of market research and financial projections</li>
    <li>Professional presentation and organization</li>
    <li>Creativity and innovation</li>
</ul>
        ''',
        'submission_format': 'file',
        'max_score': 100,
        'due_date': None,
        'max_file_size': 20,
        'allowed_file_types': 'pdf,doc,docx',
        'peer_review_enabled': False,
        'rubric_criteria': [
            {
                'name': 'Content Quality',
                'description': 'Depth and accuracy of business plan content',
                'max_points': 30,
                'weight': 30,
                'sort_order': 1
            },
            {
                'name': 'Market Analysis',
                'description': 'Quality of market research and competitive analysis',
                'max_points': 25,
                'weight': 25,
                'sort_order': 2
            },
            {
                'name': 'Financial Projections',
                'description': 'Accuracy and realism of financial forecasts',
                'max_points': 25,
                'weight': 25,
                'sort_order': 3
            },
            {
                'name': 'Presentation',
                'description': 'Professional formatting and organization',
                'max_points': 20,
                'weight': 20,
                'sort_order': 4
            }
        ]
    },
    'swot_analysis': {
        'title': 'SWOT Analysis Assignment',
        'assignment_type': 'swot_analysis',
        'description': 'Conduct a comprehensive SWOT analysis for a chosen organization',
        'instructions': '''
<h2>SWOT Analysis Assignment</h2>

<h3>Objective</h3>
<p>Conduct a thorough SWOT (Strengths, Weaknesses, Opportunities, Threats) analysis for an organization of your choice.</p>

<h3>Instructions</h3>
<ol>
    <li>Choose a real organization (company, non-profit, government agency, etc.)</li>
    <li>Research the organization thoroughly using multiple sources</li>
    <li>Identify and analyze at least 5 items in each SWOT category</li>
    <li>Provide specific examples and evidence for each point</li>
    <li>Develop strategic recommendations based on your analysis</li>
</ol>

<h3>Format Requirements</h3>
<ul>
    <li>Length: 5-7 pages</li>
    <li>Include a visual SWOT matrix/diagram</li>
    <li>Use credible sources and cite them properly</li>
    <li>Professional formatting and presentation</li>
</ul>

<h3>Sections to Include</h3>
<ol>
    <li><strong>Introduction</strong> - Brief overview of the organization</li>
    <li><strong>SWOT Analysis</strong> - Detailed analysis of each category</li>
    <li><strong>Strategic Recommendations</strong> - Actionable strategies based on SWOT</li>
    <li><strong>Conclusion</strong> - Summary of key insights</li>
    <li><strong>References</strong> - List of sources used</li>
</ol>
        ''',
        'submission_format': 'both',
        'max_score': 100,
        'due_date': None,
        'max_file_size': 15,
        'allowed_file_types': 'pdf,doc,docx,ppt,pptx',
        'peer_review_enabled': True,
        'rubric_criteria': [
            {
                'name': 'Analysis Depth',
                'description': 'Thoroughness and insight of SWOT analysis',
                'max_points': 35,
                'weight': 35,
                'sort_order': 1
            },
            {
                'name': 'Research Quality',
                'description': 'Use of credible sources and evidence',
                'max_points': 25,
                'weight': 25,
                'sort_order': 2
            },
            {
                'name': 'Strategic Thinking',
                'description': 'Quality of recommendations and strategic insights',
                'max_points': 25,
                'weight': 25,
                'sort_order': 3
            },
            {
                'name': 'Presentation',
                'description': 'Organization, formatting, and visual elements',
                'max_points': 15,
                'weight': 15,
                'sort_order': 4
            }
        ]
    }
}
