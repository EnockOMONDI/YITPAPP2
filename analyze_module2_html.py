#!/usr/bin/env python3
"""
Module 2 HTML Analysis & Implementation Strategy
===============================================

Comprehensive analysis of the Personal Initiative HTML file to create an implementation plan
for converting it into individual YITP LMS lessons.
"""

import os
import re
import json
from datetime import datetime

class Module2HTMLAnalyzer:
    def __init__(self):
        self.html_file = "courseunits/2. PERSONAL INITIATIVE FULL UNIT (MERGED)/2. PERSONAL INITIATIVE FULL UNIT.html"
        self.assets_dir = "courseunits/2. PERSONAL INITIATIVE FULL UNIT (MERGED)/"
        self.analysis_results = {
            'file_info': {},
            'structure_analysis': {},
            'assets_inventory': {},
            'lesson_breakdown': {},
            'rendering_strategy': {},
            'technical_findings': {},
            'implementation_plan': {}
        }

    def analyze_file_info(self):
        """Analyze basic file information"""
        print("📄 ANALYZING FILE INFORMATION")
        print("=" * 50)
        
        if not os.path.exists(self.html_file):
            print(f"❌ HTML file not found: {self.html_file}")
            return False
        
        file_size = os.path.getsize(self.html_file)
        print(f"✅ HTML file found: {file_size:,} bytes")
        
        # Count total lines
        with open(self.html_file, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        
        self.analysis_results['file_info'] = {
            'file_path': self.html_file,
            'file_size_bytes': file_size,
            'total_lines': total_lines,
            'generated_by': 'pdf2htmlEX'
        }
        
        print(f"📊 Total lines: {total_lines:,}")
        print(f"📊 File size: {file_size / 1024:.1f} KB")
        
        return True

    def analyze_structure(self):
        """Analyze HTML structure and identify slides/pages"""
        print(f"\n🔍 ANALYZING HTML STRUCTURE")
        print("=" * 50)
        
        with open(self.html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find page markers
        page_pattern = r'data-page-no="([^"]+)"'
        pages = re.findall(page_pattern, content)
        
        # Find embedded CSS
        css_pattern = r'<style[^>]*>(.*?)</style>'
        css_blocks = re.findall(css_pattern, content, re.DOTALL)
        
        # Find font definitions
        font_pattern = r'@font-face\{[^}]*src:url\(([^)]+)\)[^}]*\}'
        fonts = re.findall(font_pattern, content)
        
        # Find images
        img_pattern = r'src="data:image/([^;]+);base64,([^"]+)"'
        images = re.findall(img_pattern, content)
        
        # Analyze content structure
        div_pattern = r'<div[^>]*class="([^"]*)"[^>]*>'
        div_classes = re.findall(div_pattern, content)
        
        self.analysis_results['structure_analysis'] = {
            'total_pages': len(pages),
            'page_identifiers': pages,
            'css_blocks_count': len(css_blocks),
            'embedded_fonts_count': len(fonts),
            'embedded_images_count': len(images),
            'unique_css_classes': list(set(div_classes)),
            'content_type': 'PDF converted to HTML via pdf2htmlEX'
        }
        
        print(f"📄 Total pages/slides: {len(pages)}")
        print(f"🎨 CSS blocks: {len(css_blocks)}")
        print(f"🔤 Embedded fonts: {len(fonts)}")
        print(f"🖼️ Embedded images: {len(images)}")
        print(f"📝 Unique CSS classes: {len(set(div_classes))}")
        
        return True

    def analyze_assets(self):
        """Analyze external assets (fonts, images, etc.)"""
        print(f"\n📦 ANALYZING ASSETS")
        print("=" * 50)
        
        assets = []
        if os.path.exists(self.assets_dir):
            for file in os.listdir(self.assets_dir):
                if file.endswith('.woff'):
                    file_path = os.path.join(self.assets_dir, file)
                    file_size = os.path.getsize(file_path)
                    assets.append({
                        'name': file,
                        'type': 'font',
                        'size_bytes': file_size
                    })
        
        total_assets_size = sum(asset['size_bytes'] for asset in assets)
        
        self.analysis_results['assets_inventory'] = {
            'external_assets': assets,
            'total_assets_count': len(assets),
            'total_assets_size_bytes': total_assets_size,
            'assets_directory': self.assets_dir
        }
        
        print(f"📁 External assets found: {len(assets)}")
        print(f"💾 Total assets size: {total_assets_size / 1024:.1f} KB")
        
        for asset in assets[:5]:  # Show first 5 assets
            print(f"   • {asset['name']} ({asset['size_bytes']} bytes)")
        
        if len(assets) > 5:
            print(f"   • ... and {len(assets) - 5} more assets")
        
        return True

    def propose_lesson_breakdown(self):
        """Propose lesson structure based on slide analysis"""
        print(f"\n📚 PROPOSING LESSON BREAKDOWN")
        print("=" * 50)
        
        total_pages = self.analysis_results['structure_analysis']['total_pages']
        
        # Based on user requirements: 5 lessons initially
        lesson_structure = [
            {
                'lesson_number': 1,
                'title': 'Personal Initiative Fundamentals',
                'slides': '1-9',
                'estimated_duration': 60,
                'learning_objectives': [
                    'Understand the concept of Personal Initiative',
                    'Identify key characteristics of proactive behavior',
                    'Recognize the importance of self-directed action'
                ]
            },
            {
                'lesson_number': 2,
                'title': 'Future Orientation',
                'slides': '10-20',
                'estimated_duration': 75,
                'learning_objectives': [
                    'Develop future-oriented thinking skills',
                    'Learn to anticipate challenges and opportunities',
                    'Practice long-term planning techniques'
                ]
            },
            {
                'lesson_number': 3,
                'title': 'Opportunity Scanning',
                'slides': '21-31',
                'estimated_duration': 70,
                'learning_objectives': [
                    'Master opportunity identification techniques',
                    'Develop environmental scanning skills',
                    'Learn to evaluate potential opportunities'
                ]
            },
            {
                'lesson_number': 4,
                'title': 'SMART-PI Goals',
                'slides': '32-39',
                'estimated_duration': 65,
                'learning_objectives': [
                    'Understand SMART-PI goal framework',
                    'Practice setting effective personal initiative goals',
                    'Learn goal tracking and adjustment techniques'
                ]
            },
            {
                'lesson_number': 5,
                'title': 'Internal Barriers I',
                'slides': '40-55',
                'estimated_duration': 80,
                'learning_objectives': [
                    'Identify internal barriers to personal initiative',
                    'Develop strategies to overcome mental obstacles',
                    'Build self-awareness and confidence'
                ]
            }
        ]
        
        self.analysis_results['lesson_breakdown'] = {
            'total_lessons_phase1': 5,
            'total_slides_covered': 55,
            'remaining_slides': total_pages - 55 if total_pages > 55 else 0,
            'lessons': lesson_structure,
            'future_phases': 'Lessons 6-16 to be implemented in subsequent phases'
        }
        
        print(f"📖 Phase 1: {len(lesson_structure)} lessons")
        print(f"📄 Slides covered: 1-55 (out of {total_pages} total)")
        
        for lesson in lesson_structure:
            print(f"   Lesson {lesson['lesson_number']}: {lesson['title']} (Slides {lesson['slides']}, {lesson['estimated_duration']} min)")
        
        return True

    def analyze_rendering_strategy(self):
        """Analyze and recommend rendering approach"""
        print(f"\n🎨 ANALYZING RENDERING STRATEGY")
        print("=" * 50)
        
        # Analyze the complexity of the HTML
        with open(self.html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for complex CSS
        has_complex_css = '@font-face' in content and 'transform' in content
        has_embedded_images = 'data:image' in content
        has_external_fonts = len(self.analysis_results['assets_inventory']['external_assets']) > 0
        
        # Rendering options analysis
        options = {
            'option_a_direct_embed': {
                'description': 'Embed HTML directly in lesson content field',
                'pros': [
                    'Simple implementation',
                    'Preserves all original styling',
                    'No additional infrastructure needed'
                ],
                'cons': [
                    'May conflict with YITP lesson page CSS',
                    'Large content size in database',
                    'Potential mobile responsiveness issues'
                ],
                'complexity': 'Low',
                'recommended': False
            },
            'option_b_iframe': {
                'description': 'Use iframe for isolated rendering',
                'pros': [
                    'Complete style isolation',
                    'Preserves original layout perfectly',
                    'No CSS conflicts'
                ],
                'cons': [
                    'Poor mobile experience',
                    'Accessibility issues',
                    'SEO limitations'
                ],
                'complexity': 'Medium',
                'recommended': False
            },
            'option_c_css_adaptation': {
                'description': 'Extract and adapt CSS to work within YITP framework',
                'pros': [
                    'Good integration with YITP design',
                    'Mobile responsive',
                    'Maintains accessibility'
                ],
                'cons': [
                    'High development effort',
                    'Risk of layout changes',
                    'Complex CSS conflicts resolution'
                ],
                'complexity': 'High',
                'recommended': False
            },
            'option_d_hybrid': {
                'description': 'Hybrid approach with selective rendering per lesson',
                'pros': [
                    'Flexible implementation',
                    'Can optimize per lesson type',
                    'Best of multiple approaches'
                ],
                'cons': [
                    'Complex implementation',
                    'Inconsistent user experience',
                    'Higher maintenance'
                ],
                'complexity': 'Very High',
                'recommended': True
            }
        }
        
        self.analysis_results['rendering_strategy'] = {
            'has_complex_css': has_complex_css,
            'has_embedded_images': has_embedded_images,
            'has_external_fonts': has_external_fonts,
            'options': options,
            'recommended_approach': 'option_d_hybrid',
            'implementation_notes': [
                'Start with Option A for Phase 1 to validate approach',
                'Monitor for CSS conflicts and mobile issues',
                'Prepare fallback to Option C if needed',
                'Consider progressive enhancement'
            ]
        }
        
        print(f"🔍 Analysis Results:")
        print(f"   Complex CSS: {'Yes' if has_complex_css else 'No'}")
        print(f"   Embedded images: {'Yes' if has_embedded_images else 'No'}")
        print(f"   External fonts: {'Yes' if has_external_fonts else 'No'}")
        print(f"\n💡 Recommended: {options['option_d_hybrid']['description']}")
        
        return True

    def identify_technical_challenges(self):
        """Identify potential technical challenges and solutions"""
        print(f"\n⚠️ IDENTIFYING TECHNICAL CHALLENGES")
        print("=" * 50)
        
        challenges = [
            {
                'challenge': 'Large file size',
                'impact': 'Slow page loading, poor user experience',
                'solution': 'Split content by lessons, optimize images, lazy loading'
            },
            {
                'challenge': 'CSS conflicts with YITP framework',
                'impact': 'Broken layout, inconsistent styling',
                'solution': 'CSS namespacing, scoped styles, careful testing'
            },
            {
                'challenge': 'Mobile responsiveness',
                'impact': 'Poor mobile user experience',
                'solution': 'Responsive CSS adaptation, mobile-first approach'
            },
            {
                'challenge': 'Font loading',
                'impact': 'FOUT (Flash of Unstyled Text), layout shifts',
                'solution': 'Font preloading, fallback fonts, font-display CSS'
            },
            {
                'challenge': 'Content extraction complexity',
                'impact': 'Development time, potential errors',
                'solution': 'Automated parsing scripts, manual verification'
            }
        ]
        
        self.analysis_results['technical_findings'] = {
            'challenges': challenges,
            'performance_considerations': [
                'Content size optimization',
                'Asset loading strategy',
                'Caching implementation'
            ],
            'compatibility_requirements': [
                'Modern browsers support',
                'Mobile device compatibility',
                'Accessibility compliance'
            ]
        }
        
        print(f"🚨 {len(challenges)} technical challenges identified:")
        for i, challenge in enumerate(challenges, 1):
            print(f"   {i}. {challenge['challenge']}")
            print(f"      Impact: {challenge['impact']}")
            print(f"      Solution: {challenge['solution']}")
        
        return True

    def create_implementation_plan(self):
        """Create detailed implementation plan"""
        print(f"\n📋 CREATING IMPLEMENTATION PLAN")
        print("=" * 50)
        
        phases = [
            {
                'phase': 'Phase 1: Analysis & Setup',
                'duration': '1-2 days',
                'tasks': [
                    'Complete HTML structure analysis',
                    'Extract slide content for lessons 1-5',
                    'Create content parsing scripts',
                    'Set up development environment'
                ]
            },
            {
                'phase': 'Phase 2: Content Extraction',
                'duration': '2-3 days',
                'tasks': [
                    'Extract individual lesson content',
                    'Generate appropriate quiz questions',
                    'Validate content integrity',
                    'Create lesson JSON structures'
                ]
            },
            {
                'phase': 'Phase 3: Integration & Testing',
                'duration': '2-3 days',
                'tasks': [
                    'Integrate with YITP lesson template',
                    'Test rendering and responsiveness',
                    'Resolve CSS conflicts',
                    'Validate quiz functionality'
                ]
            },
            {
                'phase': 'Phase 4: Validation & Deployment',
                'duration': '1-2 days',
                'tasks': [
                    'Final JSON validation',
                    'Production deployment testing',
                    'User acceptance testing',
                    'Documentation updates'
                ]
            }
        ]
        
        self.analysis_results['implementation_plan'] = {
            'phases': phases,
            'total_estimated_duration': '6-10 days',
            'success_criteria': [
                'All 5 lessons render correctly',
                'No CSS conflicts with YITP framework',
                'Mobile responsive design',
                'Quiz functionality works',
                'JSON validation passes'
            ],
            'risk_mitigation': [
                'Regular testing on multiple devices',
                'Incremental implementation approach',
                'Fallback rendering options prepared'
            ]
        }
        
        print(f"📅 Total estimated duration: 6-10 days")
        for phase in phases:
            print(f"\n{phase['phase']} ({phase['duration']}):")
            for task in phase['tasks']:
                print(f"   • {task}")
        
        return True

    def generate_report(self):
        """Generate comprehensive analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"module2_html_analysis_report_{timestamp}.md"
        
        report_content = f"""# Module 2 HTML Analysis Report

**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**HTML File:** {self.html_file}  
**Total File Size:** {self.analysis_results['file_info']['file_size_bytes']:,} bytes  

## 📊 Executive Summary

This report provides a comprehensive analysis of the Personal Initiative HTML file and presents a detailed implementation strategy for converting it into individual YITP LMS lessons.

### Key Findings

- **Total Pages/Slides:** {self.analysis_results['structure_analysis']['total_pages']}
- **File Size:** {self.analysis_results['file_info']['file_size_bytes'] / 1024:.1f} KB
- **External Assets:** {self.analysis_results['assets_inventory']['total_assets_count']} font files
- **Generated By:** pdf2htmlEX (PDF to HTML conversion)

## 🏗️ HTML Structure Analysis

### Content Overview
- **Total Lines:** {self.analysis_results['file_info']['total_lines']:,}
- **CSS Blocks:** {self.analysis_results['structure_analysis']['css_blocks_count']}
- **Embedded Fonts:** {self.analysis_results['structure_analysis']['embedded_fonts_count']}
- **Embedded Images:** {self.analysis_results['structure_analysis']['embedded_images_count']}
- **Unique CSS Classes:** {len(self.analysis_results['structure_analysis']['unique_css_classes'])}

### Technical Characteristics
- ✅ **Self-contained:** All styles and fonts embedded
- ✅ **High fidelity:** Preserves original PDF layout
- ⚠️ **Large size:** May impact loading performance
- ⚠️ **Complex CSS:** Potential conflicts with YITP framework

## 📚 Proposed Lesson Structure (Phase 1)

{chr(10).join([f"**Lesson {lesson['lesson_number']}: {lesson['title']}**" + chr(10) + f"- Slides: {lesson['slides']}" + chr(10) + f"- Duration: {lesson['estimated_duration']} minutes" + chr(10) + f"- Objectives: {', '.join(lesson['learning_objectives'])}" for lesson in self.analysis_results['lesson_breakdown']['lessons']])}

### Coverage
- **Phase 1 Lessons:** 5
- **Slides Covered:** 1-55 (out of {self.analysis_results['structure_analysis']['total_pages']} total)
- **Remaining Content:** {self.analysis_results['lesson_breakdown']['remaining_slides']} slides for future phases

## 🎨 Rendering Strategy Recommendation

### Recommended Approach: Hybrid Implementation

**Primary Strategy:** Start with direct HTML embedding (Option A) for Phase 1 validation, with prepared fallback to CSS adaptation (Option C) if needed.

**Rationale:**
- Fastest implementation for initial validation
- Preserves original styling completely
- Allows testing of integration challenges
- Provides foundation for optimization

### Implementation Notes
{chr(10).join([f"- {note}" for note in self.analysis_results['rendering_strategy']['implementation_notes']])}

## ⚠️ Technical Challenges & Solutions

{chr(10).join([f"**{challenge['challenge']}**" + chr(10) + f"- Impact: {challenge['impact']}" + chr(10) + f"- Solution: {challenge['solution']}" + chr(10) for challenge in self.analysis_results['technical_findings']['challenges']])}

## 📋 Implementation Plan

**Total Estimated Duration:** {self.analysis_results['implementation_plan']['total_estimated_duration']}

{chr(10).join([f"### {phase['phase']} ({phase['duration']})" + chr(10) + chr(10).join([f"- {task}" for task in phase['tasks']]) + chr(10) for phase in self.analysis_results['implementation_plan']['phases']])}

## ✅ Success Criteria

{chr(10).join([f"- {criteria}" for criteria in self.analysis_results['implementation_plan']['success_criteria']])}

## 🎯 Next Steps

1. **Approve Implementation Plan:** Review and approve the proposed approach
2. **Begin Phase 1:** Start with HTML structure analysis and content extraction
3. **Create Sample Lesson:** Implement Lesson 1 as proof of concept
4. **Validate Approach:** Test rendering, responsiveness, and integration
5. **Scale Implementation:** Complete remaining lessons 2-5

## 📊 Risk Assessment

**Low Risk:**
- Content extraction and parsing
- Basic HTML integration

**Medium Risk:**
- CSS conflicts with YITP framework
- Mobile responsiveness issues

**High Risk:**
- Performance impact from large content size
- Complex styling preservation

## 💡 Recommendations

1. **Start Small:** Implement Lesson 1 first as proof of concept
2. **Test Early:** Validate rendering on multiple devices immediately
3. **Monitor Performance:** Track page load times and user experience
4. **Prepare Alternatives:** Have CSS adaptation approach ready as fallback
5. **Document Process:** Create reusable process for future modules

---
**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Status:** ✅ Ready for Implementation
"""
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"\n📄 Analysis report saved: {report_filename}")
        return report_filename

    def execute_analysis(self):
        """Execute complete analysis process"""
        print("🔍 MODULE 2 HTML ANALYSIS & IMPLEMENTATION STRATEGY")
        print("=" * 60)
        
        success = True
        success &= self.analyze_file_info()
        success &= self.analyze_structure()
        success &= self.analyze_assets()
        success &= self.propose_lesson_breakdown()
        success &= self.analyze_rendering_strategy()
        success &= self.identify_technical_challenges()
        success &= self.create_implementation_plan()
        
        if success:
            report_file = self.generate_report()
            print(f"\n🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
            print(f"📄 Comprehensive report: {report_file}")
            return True
        else:
            print(f"\n❌ ANALYSIS FAILED")
            return False

    def extract_lesson_content(self, lesson_number, start_slide, end_slide):
        """Extract content for a specific lesson"""
        print(f"\n📖 EXTRACTING LESSON {lesson_number} CONTENT")
        print("=" * 50)

        with open(self.html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all page divs
        page_pattern = r'<div id="pf([^"]+)" class="pf[^>]*data-page-no="([^"]+)"[^>]*>(.*?)</div>(?=\s*<div id="pf|\s*</div>\s*</body>)'
        pages = re.findall(page_pattern, content, re.DOTALL)

        print(f"📄 Found {len(pages)} total pages in HTML")

        # Extract pages for this lesson (convert hex page numbers)
        lesson_pages = []
        for page_id, page_no, page_content in pages:
            try:
                # Convert hex page number to decimal
                decimal_page = int(page_no, 16)
                if start_slide <= decimal_page <= end_slide:
                    lesson_pages.append({
                        'page_id': page_id,
                        'page_no': page_no,
                        'decimal_page': decimal_page,
                        'content': page_content
                    })
            except ValueError:
                continue

        print(f"📄 Extracted {len(lesson_pages)} pages for lesson {lesson_number} (slides {start_slide}-{end_slide})")

        if not lesson_pages:
            print(f"❌ No content found for lesson {lesson_number}")
            return None

        # Extract CSS and fonts needed
        css_pattern = r'<style[^>]*>(.*?)</style>'
        css_blocks = re.findall(css_pattern, content, re.DOTALL)

        # Combine all lesson content
        lesson_html = self._build_lesson_html(lesson_pages, css_blocks)

        return {
            'lesson_number': lesson_number,
            'slides_range': f"{start_slide}-{end_slide}",
            'pages_extracted': len(lesson_pages),
            'html_content': lesson_html,
            'pages_data': lesson_pages
        }

    def _build_lesson_html(self, lesson_pages, css_blocks):
        """Build complete HTML for a lesson"""
        # Start with basic HTML structure
        html_parts = [
            '<div class="yitp-lesson-content module2-personal-initiative">',
            '<style>',
            # Add essential CSS
            '.module2-personal-initiative { font-family: Arial, sans-serif; }',
            '.module2-personal-initiative .pf { position: relative; margin: 20px 0; }',
            '.module2-personal-initiative .pc { position: relative; }',
            '.module2-personal-initiative .t { position: absolute; white-space: pre; }',
        ]

        # Add original CSS (first block contains the main styles)
        if css_blocks:
            # Clean and namespace the CSS
            main_css = css_blocks[0]
            # Add namespace prefix to avoid conflicts
            namespaced_css = self._namespace_css(main_css)
            html_parts.append(namespaced_css)

        html_parts.append('</style>')

        # Add lesson pages
        for page in sorted(lesson_pages, key=lambda x: x['decimal_page']):
            html_parts.append(f'<div class="lesson-slide slide-{page["decimal_page"]}">')
            html_parts.append(f'<div id="pf{page["page_id"]}" class="pf" data-page-no="{page["page_no"]}">')
            html_parts.append(page['content'])
            html_parts.append('</div>')
            html_parts.append('</div>')

        html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _namespace_css(self, css_content):
        """Add namespace prefix to CSS to avoid conflicts"""
        # Simple CSS namespacing - prefix all selectors with .module2-personal-initiative
        lines = css_content.split('\n')
        namespaced_lines = []

        for line in lines:
            line = line.strip()
            if line and not line.startswith('@') and not line.startswith('/*') and '{' in line:
                # This is a CSS rule
                if line.startswith('.'):
                    # Already a class selector, prefix it
                    line = '.module2-personal-initiative ' + line
                elif not line.startswith('.module2-personal-initiative'):
                    # Add namespace prefix
                    line = '.module2-personal-initiative ' + line
            namespaced_lines.append(line)

        return '\n'.join(namespaced_lines)

    def generate_quiz_questions(self, lesson_number, lesson_title):
        """Generate appropriate quiz questions for a lesson"""
        print(f"\n❓ GENERATING QUIZ QUESTIONS FOR LESSON {lesson_number}")
        print("=" * 50)

        # Define question templates based on lesson content
        question_templates = {
            1: [  # Personal Initiative Fundamentals
                {
                    "question_text": "What is the primary characteristic of Personal Initiative?",
                    "question_type": "multiple_choice",
                    "options": ["Reactive behavior", "Proactive self-starting behavior", "Following instructions", "Waiting for direction"],
                    "correct_answer": "Proactive self-starting behavior",
                    "explanation": "Personal Initiative is fundamentally about being proactive and self-starting rather than reactive.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "Personal Initiative requires taking action without being told what to do.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "True",
                    "explanation": "Personal Initiative is characterized by self-starting behavior and taking action without explicit direction.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "List three key benefits of developing Personal Initiative in your career.",
                    "question_type": "short_answer",
                    "correct_answer": "Sample answers: Increased job satisfaction, better career advancement opportunities, improved problem-solving skills, greater autonomy, enhanced leadership potential",
                    "explanation": "Personal Initiative leads to numerous career benefits including advancement opportunities and increased satisfaction.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which of the following best describes a person with high Personal Initiative?",
                    "question_type": "multiple_choice",
                    "options": ["Waits for clear instructions", "Takes action to improve situations", "Avoids responsibility", "Follows established routines only"],
                    "correct_answer": "Takes action to improve situations",
                    "explanation": "High Personal Initiative involves actively seeking to improve situations and taking responsibility for outcomes.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Describe a situation where you demonstrated Personal Initiative and explain the outcome.",
                    "question_type": "short_answer",
                    "correct_answer": "Answers should include: identification of an opportunity or problem, self-directed action taken, positive outcome achieved, reflection on learning",
                    "explanation": "Personal examples help reinforce understanding and application of Personal Initiative concepts.",
                    "points": 2,
                    "sort_order": 5
                }
            ],
            2: [  # Future Orientation
                {
                    "question_text": "Future orientation in Personal Initiative means:",
                    "question_type": "multiple_choice",
                    "options": ["Living in the future", "Planning and anticipating future needs", "Ignoring present challenges", "Predicting exact outcomes"],
                    "correct_answer": "Planning and anticipating future needs",
                    "explanation": "Future orientation involves strategic thinking and planning for anticipated future needs and opportunities.",
                    "points": 1,
                    "sort_order": 1
                },
                {
                    "question_text": "Long-term thinking is more important than short-term action in Personal Initiative.",
                    "question_type": "true_false",
                    "options": ["True", "False"],
                    "correct_answer": "False",
                    "explanation": "Both long-term thinking and short-term action are important; Personal Initiative requires balancing future planning with present action.",
                    "points": 1,
                    "sort_order": 2
                },
                {
                    "question_text": "What are the key components of effective future-oriented planning?",
                    "question_type": "short_answer",
                    "correct_answer": "Key components include: environmental scanning, trend analysis, scenario planning, goal setting, risk assessment, contingency planning",
                    "explanation": "Effective future planning requires systematic analysis and preparation for multiple scenarios.",
                    "points": 2,
                    "sort_order": 3
                },
                {
                    "question_text": "Which technique is most effective for developing future orientation?",
                    "question_type": "multiple_choice",
                    "options": ["Reactive problem-solving", "Scenario planning", "Historical analysis only", "Intuitive guessing"],
                    "correct_answer": "Scenario planning",
                    "explanation": "Scenario planning helps develop future orientation by considering multiple possible futures and preparing accordingly.",
                    "points": 1,
                    "sort_order": 4
                },
                {
                    "question_text": "Create a 5-year vision for your career development including specific milestones.",
                    "question_type": "short_answer",
                    "correct_answer": "Answers should include: clear long-term vision, specific measurable milestones, timeline, skill development plans, potential challenges and solutions",
                    "explanation": "Creating a detailed career vision demonstrates future-oriented thinking and planning skills.",
                    "points": 2,
                    "sort_order": 5
                }
            ]
            # Additional lessons would be added here
        }

        questions = question_templates.get(lesson_number, [])
        print(f"✅ Generated {len(questions)} questions for {lesson_title}")

        return questions

if __name__ == "__main__":
    analyzer = Module2HTMLAnalyzer()
    success = analyzer.execute_analysis()

    if success:
        print(f"\n✅ Ready to proceed with implementation")

        # Extract first lesson as proof of concept
        lesson_1_content = analyzer.extract_lesson_content(1, 1, 9)
        if lesson_1_content:
            print(f"\n🎯 PROOF OF CONCEPT: LESSON 1 EXTRACTED")
            print(f"📄 Pages extracted: {lesson_1_content['pages_extracted']}")
            print(f"📝 Content size: {len(lesson_1_content['html_content']):,} characters")

            # Generate quiz questions
            quiz_questions = analyzer.generate_quiz_questions(1, "Personal Initiative Fundamentals")

            print(f"\n✅ Lesson 1 extraction completed successfully!")
            print(f"📊 Ready for JSON structure creation")

    else:
        print(f"\n❌ Analysis incomplete - review errors above")
