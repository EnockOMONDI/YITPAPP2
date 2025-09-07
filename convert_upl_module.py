#!/usr/bin/env python3
"""
UPL 101 Module Converter for YITP Course Builder
Converts the Understanding Purpose in Life module into structured course data
"""

import json
import re
from datetime import datetime
import docx

class UPLModuleConverter:
    def __init__(self):
        self.course_data = {
            "course_title": "Understanding Purpose in Life (UPL 101)",
            "course_description": "A comprehensive 8-session course exploring the foundations of purpose, service, and meaningful living through African wisdom, personal development principles, and practical applications.",
            "course_category": "Personal Development",
            "difficulty_level": "beginner",
            "estimated_duration": 10,  # hours total
            "methodology": "Interactive teaching, African proverbs, folktales, personal testimonies, peer exercises, and journaling",
            "price": 39.00,
            "currency": "USD",
            "weeks": 2,
            "total_sessions": 8,
            "modules": []
        }
        
        # Complete session mapping for all 8 sessions
        self.session_mapping = {
            1: {"title": "Introduction to Life's Purpose", "duration": 60, "week": 1},
            2: {"title": "The Foundations of Purpose", "duration": 90, "week": 1},
            3: {"title": "Purpose and Service", "duration": 60, "week": 1},
            4: {"title": "Overcoming Obstacles to Purpose", "duration": 60, "week": 1},
            5: {"title": "Practical Tools for Defining Your Purpose", "duration": 90, "week": 2},
            6: {"title": "Purpose in Action", "duration": 90, "week": 2},
            7: {"title": "Sharing and Sustaining Your Purpose", "duration": 90, "week": 2},
            8: {"title": "Reflection and Forward Planning", "duration": 60, "week": 2}
        }

        # Week structure
        self.week_structure = {
            1: {
                "title": "Discovering the Foundations of Purpose",
                "description": "Explore the fundamental concepts of purpose through stories, principles, and overcoming obstacles",
                "sessions": [1, 2, 3, 4]
            },
            2: {
                "title": "Living, Sharing, and Sustaining Your Purpose",
                "description": "Apply purpose in daily life, share with others, and create sustainable practices for long-term growth",
                "sessions": [5, 6, 7, 8]
            }
        }
        
        # Content templates for rich HTML formatting
        self.html_templates = {
            "story_box": '<div style="background: #f8f9fa; border-left: 4px solid #1a2e53; padding: 1.5rem; margin: 1.5rem 0; border-radius: 0 8px 8px 0;"><h4 style="color: #1a2e53; margin-top: 0;"><i class="fas fa-book-open"></i> {title}</h4>{content}</div>',
            "key_takeaway": '<div style="background: #fff8e1; border-left: 4px solid #ff5d15; padding: 1rem; margin: 1rem 0;"><h4 style="color: #ff5d15; margin-top: 0;">💡 Key Takeaway</h4><p>{content}</p></div>',
            "activity_box": '<div style="background: #f0f8ff; border: 2px solid #1a2e53; border-radius: 8px; padding: 1rem; margin: 1rem 0;"><h4 style="color: #1a2e53; margin-top: 0;">🎯 Activity</h4>{content}</div>',
            "quote_box": '<div style="background: #f5f5f5; border-left: 4px solid #6c757d; padding: 1rem; margin: 1rem 0; font-style: italic;"><p style="margin: 0; font-size: 1.1em;">"{quote}"</p><p style="margin: 0.5rem 0 0 0; text-align: right; font-weight: bold;">— {author}</p></div>',
            "questions_list": '<div style="background: #e8f4fd; border: 1px solid #bee5eb; border-radius: 8px; padding: 1rem; margin: 1rem 0;"><h4 style="color: #0c5460; margin-top: 0;">🤔 Reflection Questions</h4><ol>{questions}</ol></div>'
        }

    def extract_content_from_docx(self, file_path):
        """Extract content from the Word document"""
        try:
            doc = docx.Document(file_path)
            content = []
            for para in doc.paragraphs:
                if para.text.strip():
                    content.append(para.text.strip())
            return content
        except Exception as e:
            print(f"Error reading document: {e}")
            return []

    def parse_session_content(self, content_lines, session_num):
        """Parse content for a specific session"""
        session_info = self.session_mapping.get(session_num)
        if not session_info:
            return None
            
        # Find session boundaries
        session_start = f"Session {session_num}"
        session_content = []
        capturing = False
        
        for line in content_lines:
            if session_start in line:
                capturing = True
                session_content.append(line)
            elif capturing and (line.startswith("Session ") and f"Session {session_num}" not in line):
                break
            elif capturing:
                session_content.append(line)
                
        return self.convert_session_to_html(session_content, session_num)

    def convert_session_to_html(self, session_content, session_num):
        """Convert session content to rich HTML with creative content for sessions 4-8"""
        session_info = self.session_mapping.get(session_num)
        if not session_info:
            return ""

        # For sessions 1-3, use extracted content
        if session_num <= 3 and session_content:
            return self._parse_extracted_content(session_content, session_num)

        # For sessions 4-8, create rich interactive content based on themes
        return self._create_interactive_content(session_num)

    def _parse_extracted_content(self, session_content, session_num):
        """Parse extracted content for sessions 1-3"""
        html_content = []

        for line in session_content:
            # Session title
            if f"Session {session_num}" in line and "–" in line:
                title = line.split("–")[1].strip() if "–" in line else line
                html_content.append(f'<h2 style="color: #1a2e53; border-bottom: 2px solid #ff5d15; padding-bottom: 0.5rem;">{title}</h2>')

            # Objective
            elif line.startswith("Objective:"):
                objective = line.replace("Objective:", "").strip()
                html_content.append(self.html_templates["key_takeaway"].format(content=f"<strong>Learning Objective:</strong> {objective}"))

            # Stories and examples
            elif "Story of" in line or "Proverb:" in line:
                story_title = line.replace("The Story of", "").replace("Proverb:", "").strip()
                html_content.append(f'<h3 style="color: #ff5d15; margin-top: 2rem;">📖 {story_title}</h3>')

            # Key Topics
            elif line == "Key Topics:":
                html_content.append('<h3 style="color: #1a2e53; margin-top: 2rem;">🔑 Key Topics</h3>')

            # Activities
            elif line.startswith("Activity:"):
                activity = line.replace("Activity:", "").strip()
                html_content.append(self.html_templates["activity_box"].format(content=f"<p>{activity}</p>"))

            # Questions (7 Questions for Clarity)
            elif "Questions for Clarity:" in line:
                html_content.append('<h4 style="color: #0c5460;">🤔 7 Questions for Clarity</h4>')

            # Regular content
            else:
                # Handle quotes
                if line.startswith('"') and line.endswith('"') and "–" in line:
                    parts = line.rsplit("–", 1)
                    quote = parts[0].strip().strip('"')
                    author = parts[1].strip()
                    html_content.append(self.html_templates["quote_box"].format(quote=quote, author=author))
                else:
                    # Regular paragraph
                    if line.strip():
                        html_content.append(f'<p>{line}</p>')

        return "\n".join(html_content)

    def _create_interactive_content(self, session_num):
        """Create rich interactive content for sessions 4-8"""
        session_info = self.session_mapping[session_num]
        title = f"Session {session_num}: {session_info['title']}"

        content_map = {
            4: self._create_session_4_content(),
            5: self._create_session_5_content(),
            6: self._create_session_6_content(),
            7: self._create_session_7_content(),
            8: self._create_session_8_content()
        }

        base_html = f'<h2 style="color: #1a2e53; border-bottom: 2px solid #ff5d15; padding-bottom: 0.5rem;">{title} ({session_info["duration"]} minutes)</h2>'

        return base_html + "\n" + content_map.get(session_num, "")

    def _create_session_4_content(self):
        """Session 4: Overcoming Obstacles to Purpose"""
        return f'''
{self.html_templates["key_takeaway"].format(content="<strong>Learning Objective:</strong> Identify and overcome common obstacles that prevent you from living your purpose.")}

<h3 style="color: #ff5d15; margin-top: 2rem;">📖 The Tortoise and the Heavy Load</h3>
<p>An African folktale tells of a tortoise who volunteered to carry supplies to a distant village during a drought. Other animals laughed, saying he was too slow. The tortoise replied, "I may be slow, but I believe each step takes me closer to home."</p>
<p>For days, the tortoise carried his heavy load. When faster animals gave up due to the weight, the tortoise continued. He arrived last but was the only one who completed the journey. The village elder said, "Speed without purpose is meaningless. Purpose with persistence conquers all obstacles."</p>

<h3 style="color: #1a2e53; margin-top: 2rem;">🔑 Key Topics</h3>
<p><strong>Common Obstacles to Purpose:</strong></p>
<ul>
<li>Fear of failure and rejection</li>
<li>Lack of clarity and direction</li>
<li>External pressures and expectations</li>
<li>Past failures and limiting beliefs</li>
<li>Resource constraints and practical challenges</li>
</ul>

{self.html_templates["quote_box"].format(quote="Courage is not the absence of fear, but action in spite of it", author="Nelson Mandela")}

<p><strong>Building Inner Clarity:</strong> Gandhi's approach to overcoming opposition through inner strength and unwavering commitment to principles.</p>

<p><strong>Napoleon Hill's Faith vs. Fear:</strong> Understanding how faith in your purpose can overcome the fear that holds you back.</p>

{self.html_templates["activity_box"].format(content="<p><strong>Obstacle Mapping Exercise:</strong> List your top 3 obstacles to living your purpose. For each obstacle, write one specific action you can take this week to address it. Then, practice a visualization exercise where you see yourself successfully breaking through each barrier.</p>")}

<h4 style="color: #0c5460;">🤔 Reflection Questions</h4>
<ul>
<li>What fear has been holding you back from pursuing your purpose?</li>
<li>How can you reframe past failures as learning experiences?</li>
<li>What would you attempt if you knew you could not fail?</li>
</ul>
'''

    def _create_session_5_content(self):
        """Session 5: Practical Tools for Defining Your Purpose"""
        return f'''
{self.html_templates["key_takeaway"].format(content="<strong>Learning Objective:</strong> Use practical tools and techniques to clearly define and articulate your life purpose.")}

<h3 style="color: #ff5d15; margin-top: 2rem;">📖 The Fisherman and the Merchant</h3>
<p>A wealthy merchant found a fisherman resting by his boat. "Why aren't you fishing?" asked the merchant. "I caught enough for today," replied the fisherman. "But you could catch more, sell them, buy a bigger boat, hire workers, and become rich!" The fisherman asked, "Then what?" "Then you could relax and enjoy life," said the merchant. The fisherman smiled, "But I'm already doing that."</p>
<p>This story reminds us that purpose isn't always about accumulation—sometimes it's about recognizing what truly fulfills us.</p>

<h3 style="color: #1a2e53; margin-top: 2rem;">🔑 Key Topics</h3>
<p><strong>Success Afrika Techniques for Purpose Discovery:</strong></p>
<ul>
<li>Passion identification exercises</li>
<li>Strengths assessment and mapping</li>
<li>Values clarification activities</li>
<li>Life experiences analysis</li>
</ul>

{self.html_templates["quote_box"].format(quote="Your purpose in life is to find your purpose and give your whole heart and soul to it", author="Buddha")}

<p><strong>Crafting Your Purpose Statement:</strong></p>
<ul>
<li>Elements of a powerful purpose statement</li>
<li>Aligning purpose with personal values</li>
<li>Making it specific and actionable</li>
<li>Testing for authenticity and resonance</li>
</ul>

{self.html_templates["activity_box"].format(content="<p><strong>Purpose Statement Workshop:</strong> Using the Success Afrika framework, complete the passion and strengths assessments. Then craft your first draft purpose statement in 2-3 sentences. Share with a peer for feedback and refinement.</p>")}

<h4 style="color: #0c5460;">🤔 Purpose Clarity Questions</h4>
<ul>
<li>What activities make you lose track of time?</li>
<li>What problems in the world do you feel called to solve?</li>
<li>How do you want to be remembered?</li>
<li>What unique combination of skills and passions do you possess?</li>
</ul>
'''

    def _create_session_6_content(self):
        """Session 6: Purpose in Action"""
        return f'''
{self.html_templates["key_takeaway"].format(content="<strong>Learning Objective:</strong> Transform your purpose from concept to daily practice through actionable strategies.")}

<h3 style="color: #ff5d15; margin-top: 2rem;">📖 The Child and the Village</h3>
<p>An African proverb states: "The child who is not embraced by the village will burn it down to feel its warmth." This teaches us that purpose thrives not in isolation, but in connection and contribution to our communities.</p>
<p>When we act on our purpose, we create warmth and light for others, building the very village that embraces us all.</p>

<h3 style="color: #1a2e53; margin-top: 2rem;">🔑 Key Topics</h3>
<p><strong>Og Mandino's Purposeful Habits:</strong></p>
<ul>
<li>Daily practices for meaningful living</li>
<li>Building character through consistent action</li>
<li>The compound effect of small purposeful acts</li>
</ul>

{self.html_templates["quote_box"].format(quote="I will form good habits and become their slave", author="Og Mandino")}

<p><strong>Time Management for Meaningful Living:</strong></p>
<ul>
<li>Aligning your schedule with your purpose</li>
<li>Prioritizing activities that serve your mission</li>
<li>Creating boundaries to protect purposeful time</li>
</ul>

<p><strong>African Leaders in Action:</strong> Examples of contemporary African entrepreneurs and leaders who demonstrate purpose-driven action in business, politics, and social change.</p>

{self.html_templates["activity_box"].format(content="<p><strong>Purpose Integration Exercise:</strong> Create a weekly schedule that aligns with your purpose. Identify 3 daily habits that support your mission. Design one small action you can take this week to move closer to your purpose.</p>")}

<h4 style="color: #0c5460;">🤔 Action-Oriented Questions</h4>
<ul>
<li>How can you integrate your purpose into your current work or studies?</li>
<li>What daily habit would most support your purpose?</li>
<li>Who in your community could benefit from your unique gifts?</li>
</ul>
'''

    def _create_session_7_content(self):
        """Session 7: Sharing and Sustaining Your Purpose"""
        return f'''
{self.html_templates["key_takeaway"].format(content="<strong>Learning Objective:</strong> Learn how to share your purpose with others and create sustainable practices for long-term growth.")}

<h3 style="color: #ff5d15; margin-top: 2rem;">📖 The Clay Lamp</h3>
<p>In a village, there was a small clay lamp that burned brightly. One night, many people came asking for light. The lamp worried, "If I light all these other lamps, will my flame grow smaller?" But as the lamp lit one candle after another, its flame remained strong. Soon the whole village glowed with light, and the original lamp realized: sharing your light doesn't diminish it—it multiplies it.</p>

<h3 style="color: #1a2e53; margin-top: 2rem;">🔑 Key Topics</h3>
<p><strong>Zig Ziglar's Principle:</strong> "Help others get what they want, and you'll get what you want." Understanding how serving others amplifies your own purpose.</p>

{self.html_templates["quote_box"].format(quote="A life not lived for others is not a life", author="Mother Teresa")}

<p><strong>Gandhi's Enduring Influence:</strong> How purpose-driven lives continue to impact others long after we're gone. The ripple effect of authentic purpose.</p>

<p><strong>Building Your Support Network:</strong></p>
<ul>
<li>Finding mentors and accountability partners</li>
<li>Creating communities around shared purpose</li>
<li>Ongoing growth through Success Afrika and other resources</li>
</ul>

<p><strong>Sustaining Purpose Through Challenges:</strong></p>
<ul>
<li>Maintaining motivation during difficult times</li>
<li>Adapting your purpose as you grow</li>
<li>Learning from setbacks and failures</li>
</ul>

{self.html_templates["activity_box"].format(content="<p><strong>Community Impact Project:</strong> Design a small community project that reflects your purpose. Create a plan to share your purpose with 3 people this month. Identify resources (books, courses, mentors) for ongoing growth.</p>")}

<h4 style="color: #0c5460;">🤔 Sharing and Sustainability Questions</h4>
<ul>
<li>How can you use your purpose to serve others?</li>
<li>What legacy do you want to leave through your purpose?</li>
<li>Who could you mentor or inspire on their purpose journey?</li>
</ul>
'''

    def _create_session_8_content(self):
        """Session 8: Reflection and Forward Planning"""
        return f'''
{self.html_templates["key_takeaway"].format(content="<strong>Learning Objective:</strong> Consolidate your learning, refine your purpose, and create a concrete plan for moving forward.")}

<h3 style="color: #ff5d15; margin-top: 2rem;">📖 The River and the Stone</h3>
<p>A young person asked an elder, "How does the river carve through the hardest rock?" The elder replied, "Not through force, but through persistence. Drop by drop, day by day, the water shapes even the mightiest stone. Your purpose is like that river—gentle but persistent, it will shape your life and the world around you."</p>

<h3 style="color: #1a2e53; margin-top: 2rem;">🔑 Key Topics</h3>
<p><strong>Consolidating Your Learning:</strong></p>
<ul>
<li>Reviewing and refining your purpose statement</li>
<li>Identifying key insights from the 8-session journey</li>
<li>Recognizing growth and transformation</li>
</ul>

{self.html_templates["quote_box"].format(quote="The best time to plant a tree was 20 years ago. The second best time is now", author="Chinese Proverb")}

<p><strong>Creating Your Action Plan:</strong></p>
<ul>
<li>Setting 90-day, 6-month, and 1-year goals</li>
<li>Identifying resources and support systems</li>
<li>Building accountability measures</li>
</ul>

<p><strong>Strategies for Resilience:</strong></p>
<ul>
<li>Maintaining purpose during challenging times</li>
<li>Adapting and evolving your purpose</li>
<li>Learning from setbacks and course corrections</li>
</ul>

<p><strong>Inspiring Others:</strong> How to become a beacon of purpose for others through your example and story.</p>

{self.html_templates["activity_box"].format(content="<p><strong>Final Integration Activity:</strong> Present your refined purpose statement and one-year action plan to the group. Create a personal mission statement that incorporates everything you've learned. Write a letter to yourself to open in 6 months, describing your purpose journey and commitments.</p>")}

<h4 style="color: #0c5460;">🤔 Forward-Looking Questions</h4>
<ul>
<li>How has your understanding of purpose evolved through this course?</li>
<li>What is your biggest commitment moving forward?</li>
<li>How will you measure progress on your purpose journey?</li>
<li>What support do you need to stay on track?</li>
</ul>

{self.html_templates["key_takeaway"].format(content="<strong>Course Completion:</strong> Congratulations on completing Understanding Purpose in Life! You now have the tools, insights, and community to live a purpose-driven life. Remember: your purpose is not a destination—it's a journey of continuous growth and service.")}
'''

    def generate_quiz_questions(self, session_num, content):
        """Generate true/false quiz questions based on session content"""
        questions = []

        # Session 1 questions - Introduction to Life's Purpose
        if session_num == 1:
            questions = [
                {
                    "question_text": "According to the story of the three builders, the third bricklayer saw himself as building a cathedral.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The third bricklayer replied with energy that he was building a great cathedral where people could gather, pray and celebrate.",
                    "sort_order": 1
                },
                {
                    "question_text": "Purpose and vision are the same thing according to the course material.",
                    "question_type": "true_false", 
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Purpose is the reason for which something exists, while vision is the power of anticipating what will come to be.",
                    "sort_order": 2
                },
                {
                    "question_text": "Gandhi's main purpose in life was to live rightly, think rightly, and act rightly.",
                    "question_type": "true_false",
                    "correct_answer": "true", 
                    "points": 2,
                    "explanation": "True. Gandhi stated: 'The main purpose of life is to live rightly, think rightly, act rightly.'",
                    "sort_order": 3
                },
                {
                    "question_text": "Napoleon Hill lists Definiteness of Purpose as the second most important success principle.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Napoleon Hill lists Definiteness of Purpose as the TOP attribute in ensuring achievement.",
                    "sort_order": 4
                },
                {
                    "question_text": "The course suggests that discovering your purpose requires answering seven specific questions sincerely.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The course presents 7 Questions for Clarity and states that answering them sincerely leads to discovering your purpose.",
                    "sort_order": 5
                }
            ]
        
        # Session 2 questions  
        elif session_num == 2:
            questions = [
                {
                    "question_text": "The baobab tree is known as the 'tree of life' because it sustains communities through fruit, shelter, and water storage.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The baobab tree is called the 'tree of life' because it provides fruit, shelter, and water storage to communities.",
                    "sort_order": 1
                },
                {
                    "question_text": "According to Zig Ziglar's Wheel of Life, if one spoke is weak, it doesn't affect the other areas of life.",
                    "question_type": "true_false",
                    "correct_answer": "false", 
                    "points": 2,
                    "explanation": "False. Ziglar taught that if one part of the wheel is flat, your ride through life will be bumpy, showing that all areas are interconnected.",
                    "sort_order": 2
                },
                {
                    "question_text": "Og Mandino believed that meaningful living is about chasing material things.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Og Mandino believed meaningful living is not about chasing things; it's about becoming more through daily habits.",
                    "sort_order": 3
                },
                {
                    "question_text": "The course teaches that your minor purposes should feed into your major purpose, not out of it.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The baobab tree lesson teaches that minor purposes must feed into your major purpose for coherent life direction.",
                    "sort_order": 4
                },
                {
                    "question_text": "Definiteness of purpose requires only knowing what you want, without needing a burning desire.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Definiteness of purpose requires both knowing exactly what you want AND developing a burning desire for it.",
                    "sort_order": 5
                }
            ]
            
        # Session 3 questions
        elif session_num == 3:
            questions = [
                {
                    "question_text": "The elevator proverb teaches that when you succeed, you should help others climb too.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The proverb 'When you take the elevator up, send it back down for others' teaches about helping others succeed.",
                    "sort_order": 1
                },
                {
                    "question_text": "Mother Teresa was famous primarily because of her wealth and position of power.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Mother Teresa was remembered for her deep compassion and small acts done with great love, not wealth or power.",
                    "sort_order": 2
                },
                {
                    "question_text": "Nelson Mandela spent 27 years in prison because he refused to compromise on equality.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. Mandela was imprisoned for 27 years because he stood firm for justice and refused to compromise on equality.",
                    "sort_order": 3
                },
                {
                    "question_text": "According to the course, humility means keeping score and expecting returns for your service.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The course teaches that true service means serving without expecting return and not keeping score.",
                    "sort_order": 4
                },
                {
                    "question_text": "Wangari Maathai planted trees for future generations, not just for herself.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The course mentions that Wangari Maathai planted trees not for herself but for future generations.",
                    "sort_order": 5
                }
            ]

        # Session 4 questions - Overcoming Obstacles to Purpose
        elif session_num == 4:
            questions = [
                {
                    "question_text": "The folktale of the tortoise teaches that steady progress is more important than speed when overcoming obstacles.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The tortoise carried a heavy load for days because he believed each step took him closer to home, demonstrating steady progress despite obstacles.",
                    "sort_order": 1
                },
                {
                    "question_text": "According to Napoleon Hill, fear is stronger than faith in achieving purpose.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Napoleon Hill teaches about overcoming fear with faith, emphasizing that faith is essential for achieving one's definite purpose.",
                    "sort_order": 2
                },
                {
                    "question_text": "Gandhi demonstrated courage by facing opposition without compromising his principles.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. Gandhi showed remarkable courage in the face of opposition while maintaining his commitment to non-violence and justice.",
                    "sort_order": 3
                },
                {
                    "question_text": "Building inner clarity is unnecessary when you have external support for your purpose.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. Inner clarity is essential for maintaining purpose regardless of external circumstances or support.",
                    "sort_order": 4
                },
                {
                    "question_text": "Visualization exercises can help you break through major barriers to achieving your purpose.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session includes visualization activities where you picture yourself breaking through major barriers.",
                    "sort_order": 5
                }
            ]

        # Session 5 questions - Practical Tools for Defining Your Purpose
        elif session_num == 5:
            questions = [
                {
                    "question_text": "The fisherman and merchant story teaches that true purpose is always about accumulating wealth.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The story shows that true purpose isn't about riches but fulfillment - the fisherman was content with his simple life.",
                    "sort_order": 1
                },
                {
                    "question_text": "Success Afrika techniques focus on identifying both passions and strengths when defining purpose.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session covers Success Afrika techniques for identifying passions and strengths as part of purpose definition.",
                    "sort_order": 2
                },
                {
                    "question_text": "Your purpose statement should be aligned with your personal values.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session emphasizes aligning purpose with values as a key component of crafting a meaningful purpose statement.",
                    "sort_order": 3
                },
                {
                    "question_text": "Peer feedback is discouraged when developing your purpose statement.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The session activity specifically includes getting peer feedback on your first draft purpose statement.",
                    "sort_order": 4
                },
                {
                    "question_text": "A well-crafted purpose statement should be written in the first draft and never revised.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The session focuses on writing a 'first draft' of your purpose statement, implying it will be refined over time.",
                    "sort_order": 5
                }
            ]

        # Session 6 questions - Purpose in Action
        elif session_num == 6:
            questions = [
                {
                    "question_text": "The proverb about the child and the village teaches that purpose thrives in isolation.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The proverb 'The child who is not embraced by the village will burn it down to feel its warmth' teaches that purpose thrives in connection and contribution.",
                    "sort_order": 1
                },
                {
                    "question_text": "Og Mandino's teachings emphasize developing purposeful daily habits.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session covers Og Mandino's approach to purposeful habits as essential for meaningful living.",
                    "sort_order": 2
                },
                {
                    "question_text": "Time management for meaningful living involves aligning your schedule with your purpose.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session includes creating a weekly schedule aligned with your purpose as a key activity.",
                    "sort_order": 3
                },
                {
                    "question_text": "African leaders and entrepreneurs are not relevant examples for purpose-driven action.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The session specifically highlights African leaders and entrepreneurs as examples of acting on purpose.",
                    "sort_order": 4
                },
                {
                    "question_text": "Integrating purpose into everyday life requires creating a structured weekly schedule.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session activity involves creating a weekly schedule aligned with your purpose to integrate it into daily life.",
                    "sort_order": 5
                }
            ]

        # Session 7 questions - Sharing and Sustaining Your Purpose
        elif session_num == 7:
            questions = [
                {
                    "question_text": "The clay lamp story teaches that sharing your light diminishes your own flame.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The story teaches that a small lamp lit many others without losing its flame - sharing your light strengthens it.",
                    "sort_order": 1
                },
                {
                    "question_text": "Zig Ziglar's principle is 'help others get what they want' and you'll get what you want.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. This is one of Zig Ziglar's most famous principles about helping others achieve their goals.",
                    "sort_order": 2
                },
                {
                    "question_text": "Gandhi's influence ended when his life ended.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The session discusses Gandhi's enduring influence, showing how purpose-driven lives continue to impact others long after death.",
                    "sort_order": 3
                },
                {
                    "question_text": "Designing a community project is an effective way to share your purpose with others.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session activity involves designing a small community project that reflects your purpose.",
                    "sort_order": 4
                },
                {
                    "question_text": "Ongoing growth through resources like Success Afrika is discouraged once you find your purpose.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The session emphasizes ongoing growth via Success Afrika and other resources as essential for sustaining purpose.",
                    "sort_order": 5
                }
            ]

        # Session 8 questions - Reflection and Forward Planning
        elif session_num == 8:
            questions = [
                {
                    "question_text": "The river and stone allegory teaches that purpose shapes life through sudden dramatic changes.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The allegory teaches that purpose shapes life through steady persistence, like water gradually shaping the hardest rock.",
                    "sort_order": 1
                },
                {
                    "question_text": "Reviewing and refining your purpose statement is an important part of forward planning.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session includes reviewing purpose statements as a key component of consolidating learning.",
                    "sort_order": 2
                },
                {
                    "question_text": "Resilience strategies are unnecessary once you have a clear purpose.",
                    "question_type": "true_false",
                    "correct_answer": "false",
                    "points": 2,
                    "explanation": "False. The session specifically covers strategies for resilience as essential for maintaining purpose over time.",
                    "sort_order": 3
                },
                {
                    "question_text": "Inspiring others through example is more powerful than inspiring through words alone.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session emphasizes inspiring others through example as a key way to share and sustain your purpose.",
                    "sort_order": 4
                },
                {
                    "question_text": "Creating a one-year action plan is part of the final session activities.",
                    "question_type": "true_false",
                    "correct_answer": "true",
                    "points": 2,
                    "explanation": "True. The session activity includes presenting purpose statements and one-year action plans.",
                    "sort_order": 5
                }
            ]

        return questions

    def create_lesson_json(self, session_num):
        """Create complete lesson JSON for a session"""
        session_info = self.session_mapping.get(session_num)
        if not session_info:
            return None
            
        # Extract content from document
        content_lines = self.extract_content_from_docx('UPL 101 YITP-MODULE-1.docx')
        
        # Parse session content
        html_content = self.parse_session_content(content_lines, session_num)
        
        # Generate quiz questions
        quiz_questions = self.generate_quiz_questions(session_num, content_lines)
        
        lesson_data = {
            "lesson_id": f"upl_session_{session_num}",
            "title": f"Session {session_num}: {session_info['title']}",
            "content_type": "enhanced",
            "estimated_duration": session_info["duration"],
            "learning_objectives": self.get_learning_objectives(session_num),
            "primary_content": html_content,
            "additional_resources": [
                {
                    "type": "document",
                    "title": f"Session {session_num} PDF Download",
                    "url": f"https://ucarecdn.com/session-{session_num}-pdf/",
                    "description": f"Complete Session {session_num} content in PDF format"
                }
            ],
            "assessment": {
                "quiz": {
                    "title": f"Session {session_num} Knowledge Check",
                    "description": "Test your understanding of key concepts from this session",
                    "instructions": "Answer all true/false questions based on the session content. You have 3 attempts to achieve the passing score.",
                    "time_limit": None,
                    "max_attempts": 3,
                    "passing_score": 70,
                    "is_randomized": False,
                    "show_results": True,
                    "questions": quiz_questions
                }
            }
        }
        
        return lesson_data

    def get_learning_objectives(self, session_num):
        """Get learning objectives for each session"""
        objectives = {
            1: "Understand the concept of purpose and why it matters in life. Explore the difference between goals, vision, and purpose through real-world examples.",
            2: "Explore foundational principles for finding purpose including Napoleon Hill's Definiteness of Purpose, Zig Ziglar's Wheel of Life, and Og Mandino's habits for meaningful living.",
            3: "Understand how purpose is linked to serving others through lessons from great leaders and the importance of humility and selflessness in service.",
            4: "Identify and overcome common obstacles that prevent you from living your purpose. Develop strategies for building inner clarity and resilience.",
            5: "Use practical tools and techniques to clearly define and articulate your life purpose. Create a personal purpose statement aligned with your values.",
            6: "Transform your purpose from concept to daily practice through actionable strategies. Learn to integrate purpose into everyday life and work.",
            7: "Learn how to share your purpose with others and create sustainable practices for long-term growth. Build support networks and community impact.",
            8: "Consolidate your learning, refine your purpose, and create a concrete plan for moving forward. Develop strategies for resilience and continuous growth."
        }
        return objectives.get(session_num, "")

    def process_all_sessions(self):
        """Process all 8 sessions and create complete course structure"""
        print("🚀 Starting UPL 101 Complete Module Conversion (8 Sessions)...")
        print("=" * 70)

        # Process Week 1 sessions (1-4)
        print("\n📅 WEEK 1: Discovering the Foundations of Purpose")
        for session_num in [1, 2, 3, 4]:
            print(f"📚 Processing Session {session_num}: {self.session_mapping[session_num]['title']}...")
            lesson_data = self.create_lesson_json(session_num)

            if lesson_data:
                # Save individual lesson file
                filename = f"upl_session_{session_num}_lesson.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(lesson_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Session {session_num} converted successfully -> {filename}")
            else:
                print(f"❌ Failed to process Session {session_num}")

        # Process Week 2 sessions (5-8)
        print("\n📅 WEEK 2: Living, Sharing, and Sustaining Your Purpose")
        for session_num in [5, 6, 7, 8]:
            print(f"📚 Processing Session {session_num}: {self.session_mapping[session_num]['title']}...")
            lesson_data = self.create_lesson_json(session_num)

            if lesson_data:
                # Save individual lesson file
                filename = f"upl_session_{session_num}_lesson.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(lesson_data, f, indent=2, ensure_ascii=False)
                print(f"✅ Session {session_num} converted successfully -> {filename}")
            else:
                print(f"❌ Failed to process Session {session_num}")

        print("\n" + "=" * 70)
        print("🎉 UPL 101 Complete Module Conversion FINISHED!")
        print(f"📊 Total Sessions Converted: 8")
        print(f"📊 Total Quiz Questions: 40 (5 per session)")
        print(f"📊 Course Duration: {sum(s['duration'] for s in self.session_mapping.values())} minutes")
        print("\n📋 Next Steps:")
        print("1. Generate PDF versions for all 8 sessions")
        print("2. Create complete Course Builder session JSON")
        print("3. Upload PDFs to Uploadcare")
        print("4. Import complete course into YITP Course Builder")

if __name__ == "__main__":
    converter = UPLModuleConverter()
    converter.process_all_sessions()
