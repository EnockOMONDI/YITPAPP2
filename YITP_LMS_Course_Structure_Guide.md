# 📚 YITP LMS Course Structure Guide for Instructors

## **🎯 Purpose**
This guide helps instructors understand the YITP LMS structure to properly organize their course content before upload. Our system uses a specific hierarchy and terminology that may differ from other platforms.

---

## **🏗️ COURSE HIERARCHY OVERVIEW**

### **Structure Flow**
```
Course (Top Level)
├── Module 1 (Organizational Unit)
│   ├── Lesson 1.1 (Learning Unit)
│   │   ├── Content (Text, Video, Files)
│   │   ├── Quiz (Optional)
│   │   └── Assignment (Optional)
│   ├── Lesson 1.2
│   └── Lesson 1.3
├── Module 2
│   ├── Lesson 2.1
│   └── Lesson 2.2
└── Module N
    └── Lesson N.N
```

### **Key Terminology**
- **Course**: Complete learning program (e.g., "Digital Marketing Fundamentals")
- **Module**: Major topic sections (NOT "units" - we use "modules")
- **Lesson**: Individual learning sessions within modules
- **Content**: Text, videos, documents within lessons
- **Assessment**: Quizzes and assignments attached to lessons

---

## **📋 COURSE LEVEL STRUCTURE**

### **Required Course Information**
```yaml
Course Details:
  title: "Course Name (max 200 characters)"
  description: "Detailed course overview"
  learning_objectives: "What students will learn"
  prerequisites: "Required knowledge/skills"
  difficulty_level: "beginner | intermediate | advanced"
  estimated_duration: "Total hours (integer)"
  price: "Course price in USD"
  enrollment_limit: "Maximum students (optional)"
  
Course Settings:
  status: "draft | in_review | approved | published"
  is_published: true/false
  is_featured: true/false
  category: "Course category"
```

### **Course Metadata Requirements**
- **Thumbnail Image**: Course cover image (recommended: 1200x675px)
- **Category**: Must match existing categories or request new one
- **Tags**: Keywords for search and discovery
- **Instructor**: Assigned instructor profile

---

## **🗂️ MODULE LEVEL STRUCTURE**

### **Module Organization**
```yaml
Module Details:
  title: "Module Name (max 200 characters)"
  description: "Module overview and objectives"
  sort_order: "Display order (1, 2, 3...)"
  estimated_duration: "Duration in minutes"
  is_published: true/false
  
Module Settings:
  unlock_criteria: "Prerequisites for access (JSON)"
  # Example: {"previous_module_completed": true}
```

### **Module Planning Guidelines**
- **Logical Grouping**: Group related lessons by topic/theme
- **Sequential Flow**: Arrange modules in learning progression order
- **Duration Balance**: Aim for 60-180 minutes per module
- **Clear Objectives**: Each module should have specific learning goals

---

## **📖 LESSON LEVEL STRUCTURE**

### **Lesson Types & Content**
```yaml
Lesson Details:
  title: "Lesson Name (max 200 characters)"
  content_type: "text | video | presentation | exercise | quiz | assignment"
  content: "Rich text content (HTML supported)"
  sort_order: "Order within module"
  estimated_duration: "Duration in minutes"
  is_mandatory: true/false
  is_published: true/false
  
Lesson Content Options:
  content: "Rich text with formatting"
  video_url: "YouTube, Vimeo, or other video URL"
  presentation_file: "PowerPoint, PDF uploads"
  learning_objectives: "Specific lesson goals"
  resources: "Additional links and materials (JSON)"
```

### **Content Types Explained**

#### **1. Text Lessons**
- **Format**: Rich HTML content with formatting
- **Features**: Headers, lists, images, links, tables
- **Best For**: Concepts, explanations, reading materials

#### **2. Video Lessons**
- **Supported**: YouTube, Vimeo, direct video URLs
- **Features**: Embedded player, progress tracking
- **Best For**: Demonstrations, lectures, tutorials

#### **3. Presentation Lessons**
- **Formats**: PowerPoint (.pptx), PDF files
- **Features**: Downloadable, viewable in browser
- **Best For**: Slide-based content, visual materials

#### **4. Exercise Lessons**
- **Format**: Interactive activities and practice
- **Features**: Self-paced learning, skill application
- **Best For**: Hands-on practice, skill building

---

## **🎯 ASSESSMENT SYSTEM**

### **Quiz Structure**
```yaml
Quiz Configuration:
  title: "Quiz Name"
  description: "Quiz purpose and scope"
  instructions: "Student instructions"
  time_limit: "Minutes (optional)"
  max_attempts: "Number of attempts allowed"
  passing_score: "Minimum percentage to pass (default: 70%)"
  is_randomized: true/false
  show_results: true/false
  is_published: true/false
```

### **Question Types Available**

#### **1. Multiple Choice**
```yaml
Question:
  question_text: "Question content"
  question_type: "multiple_choice"
  options: ["Option A", "Option B", "Option C", "Option D"]
  correct_answer: "Option B"
  explanation: "Why this answer is correct"
  points: 10
```

#### **2. True/False**
```yaml
Question:
  question_text: "Statement to evaluate"
  question_type: "true_false"
  correct_answer: true/false
  explanation: "Explanation of correct answer"
  points: 5
```

#### **3. Fill in the Blank**
```yaml
Question:
  question_text: "Complete this sentence: The capital of France is ____"
  question_type: "fill_blank"
  correct_answer: "Paris"
  explanation: "Additional context"
  points: 5
```

#### **4. Short Answer**
```yaml
Question:
  question_text: "Explain the concept in 2-3 sentences"
  question_type: "short_answer"
  sample_answer: "Example of good answer"
  grading_criteria: "Manual grading guidelines"
  points: 15
```

#### **5. Matching**
```yaml
Question:
  question_text: "Match the terms with definitions"
  question_type: "matching"
  pairs: [
    {"term": "Term 1", "definition": "Definition 1"},
    {"term": "Term 2", "definition": "Definition 2"}
  ]
  points: 20
```

### **Assignment Structure**
```yaml
Assignment Configuration:
  title: "Assignment Name"
  description: "Assignment overview"
  instructions: "Detailed instructions"
  assignment_type: "essay | project | research | reflection | presentation | practical"
  submission_format: "text | file | url"
  due_date: "Deadline (optional)"
  max_score: "Total points possible"
  max_file_size: "File size limit in bytes"
  allowed_file_types: ["pdf", "docx", "txt"]
  
Grading Configuration:
  rubric: "Grading criteria (JSON format)"
  # Example rubric structure:
  rubric:
    criteria:
      - name: "Content Quality"
        points: 40
        levels:
          - score: 4
            description: "Excellent content"
          - score: 3
            description: "Good content"
```

---

## **🔄 PEER REVIEW SYSTEM**

### **Peer Review Configuration**
```yaml
Peer Review Setup:
  assignment: "Linked assignment"
  reviewer_count: 3
  review_criteria: "Evaluation guidelines (JSON)"
  review_deadline: "Review completion deadline"
  is_anonymous: true/false
  
Review Criteria Example:
  criteria:
    - aspect: "Clarity of Ideas"
      weight: 30
      description: "How clearly are ideas presented?"
    - aspect: "Evidence Support"
      weight: 40
      description: "How well are claims supported?"
    - aspect: "Organization"
      weight: 30
      description: "How well is content organized?"
```

---

## **📊 GRADING & PROGRESSION SYSTEM**

### **Grading Mechanisms**

#### **Automatic Grading**
- **Quiz Questions**: Multiple choice, true/false, fill-in-blank, matching
- **Immediate Feedback**: Instant results and explanations
- **Score Calculation**: Percentage-based with decimal precision

#### **Manual Grading**
- **Assignments**: Essays, projects, presentations
- **Rubric Support**: Structured grading criteria
- **Instructor Feedback**: Comments and suggestions

### **Progression Requirements**

#### **Lesson Completion**
```yaml
Requirements:
  - View all required content
  - Complete mandatory assessments
  - Achieve minimum scores (if specified)
  - Spend minimum time (tracked automatically)
```

#### **Module Completion**
```yaml
Requirements:
  - Complete all mandatory lessons
  - Pass all required quizzes (70% default)
  - Submit all required assignments
  - Meet unlock criteria for next module
```

#### **Course Completion**
```yaml
Requirements:
  - Complete all modules
  - Achieve 80% overall progress
  - Pass all mandatory assessments
  - Meet minimum time requirements
```

### **Grading Scale Options**
```yaml
Standard Scale:
  A: 90-100%
  B: 80-89%
  C: 70-79%
  D: 60-69%
  F: Below 60%

Pass/Fail Scale:
  Pass: 70% and above
  Fail: Below 70%

Custom Scales:
  # Can be configured per course
```

---

## **📱 CONTENT MANAGEMENT**

### **Supported Content Types**

#### **Text Content**
- **Format**: Rich HTML with CKEditor5
- **Features**: Formatting, images, links, tables, lists
- **Best Practices**: Clear headings, bullet points, visual breaks

#### **Video Content**
- **Platforms**: YouTube, Vimeo, direct uploads
- **Features**: Progress tracking, playback speed control
- **Recommendations**: 5-15 minutes per video, clear audio

#### **Document Content**
- **Formats**: PDF, PowerPoint, Word documents
- **Features**: Download, in-browser viewing
- **Size Limits**: 10MB default (configurable)

#### **Interactive Content**
- **Types**: Exercises, simulations, external tools
- **Integration**: Embedded content, external links
- **Tracking**: Completion status, time spent

### **Media Guidelines**
- **Images**: JPG, PNG, GIF (max 5MB each)
- **Videos**: MP4 recommended, hosted externally preferred
- **Documents**: PDF preferred for compatibility
- **Audio**: MP3, embedded or linked

---

## **🎮 GAMIFICATION FEATURES**

### **Available Elements**
```yaml
Progress Tracking:
  - Completion percentages
  - Learning streaks
  - Time spent tracking
  - Module progress bars

Achievement System:
  - Course completion badges
  - Perfect quiz scores
  - Consistent participation
  - Peer review contributions

Leaderboards:
  - Course progress rankings
  - Quiz performance
  - Assignment scores
  - Participation metrics
```

---

## **📧 COMMUNICATION FEATURES**

### **Automated Notifications**
- **Enrollment Confirmation**: Welcome emails
- **Progress Updates**: Milestone achievements
- **Assignment Reminders**: Due date notifications
- **Completion Certificates**: Automatic generation

### **Instructor Communication**
- **Announcements**: Course-wide messages
- **Individual Feedback**: Assignment comments
- **Discussion Forums**: Q&A and peer interaction
- **Office Hours**: Scheduled support sessions

---

## **📋 CONTENT PREPARATION CHECKLIST**

### **Before Upload**
- [ ] Convert "units" to "modules" in your structure
- [ ] Organize content into Course → Module → Lesson hierarchy
- [ ] Prepare all media files (videos, documents, images)
- [ ] Write clear learning objectives for each level
- [ ] Design assessments with appropriate question types
- [ ] Create rubrics for assignments requiring manual grading
- [ ] Plan progression requirements and prerequisites
- [ ] Prepare course metadata (description, objectives, prerequisites)

### **Content Quality Standards**
- [ ] Clear, concise lesson titles
- [ ] Consistent formatting and style
- [ ] Appropriate content length (5-20 minutes per lesson)
- [ ] Engaging multimedia elements
- [ ] Regular assessment checkpoints
- [ ] Practical application opportunities
- [ ] Clear instructions for all activities

---

## **🚀 NEXT STEPS**

### **Content Restructuring Process**
1. **Map Your Content**: Identify current "units" and convert to "modules"
2. **Organize Hierarchy**: Arrange in Course → Module → Lesson structure
3. **Prepare Assessments**: Design quizzes and assignments per our format
4. **Create Metadata**: Write descriptions, objectives, and prerequisites
5. **Review Guidelines**: Ensure compliance with our content standards
6. **Submit for Upload**: Provide organized content for LMS implementation

### **Support Available**
- **Technical Guidance**: LMS structure and feature explanations
- **Content Review**: Pre-upload content organization review
- **Assessment Design**: Quiz and assignment creation assistance
- **Media Preparation**: File format and optimization guidance

---

## **🔧 TECHNICAL SPECIFICATIONS**

### **Database Model Relationships**
```yaml
Course Model Fields:
  - title: CharField(200)
  - slug: SlugField(200) - Auto-generated from title
  - description: TextField
  - learning_objectives: TextField
  - prerequisites: TextField
  - difficulty_level: beginner/intermediate/advanced
  - estimated_duration: IntegerField (hours)
  - thumbnail: ImageField
  - status: draft/in_review/approved/published/rejected/archived
  - is_published: BooleanField
  - is_featured: BooleanField
  - enrollment_limit: IntegerField (optional)
  - price: DecimalField(10,2)
  - instructor: ForeignKey(User)
  - category: ForeignKey(Category)

Module Model Fields:
  - course: ForeignKey(Course)
  - title: CharField(200)
  - description: TextField
  - sort_order: IntegerField
  - is_published: BooleanField
  - unlock_criteria: JSONField
  - estimated_duration: IntegerField (minutes)

Lesson Model Fields:
  - module: ForeignKey(Module)
  - title: CharField(200)
  - content_type: text/video/presentation/exercise/quiz/assignment
  - content: CKEditor5Field (rich text)
  - video_url: URLField
  - presentation_file: FileField
  - sort_order: IntegerField
  - is_published: BooleanField
  - is_mandatory: BooleanField
  - estimated_duration: IntegerField (minutes)
  - learning_objectives: TextField
  - resources: JSONField
```

### **Assessment Model Specifications**
```yaml
Quiz Model:
  - lesson: ForeignKey(Lesson)
  - title: CharField(200)
  - description: TextField
  - instructions: TextField
  - time_limit: IntegerField (minutes, optional)
  - max_attempts: IntegerField (default: 1)
  - passing_score: IntegerField (default: 70%)
  - is_randomized: BooleanField
  - show_results: BooleanField
  - is_published: BooleanField

Question Model:
  - quiz: ForeignKey(Quiz)
  - question_text: TextField
  - question_type: multiple_choice/true_false/fill_blank/short_answer/matching
  - options: JSONField (for multiple choice)
  - correct_answer: TextField
  - explanation: TextField
  - points: IntegerField
  - sort_order: IntegerField

Assignment Model:
  - lesson: ForeignKey(Lesson)
  - title: CharField(200)
  - description: TextField
  - instructions: TextField
  - assignment_type: essay/project/research/reflection/presentation/practical
  - submission_format: text/file/url
  - max_file_size: IntegerField (bytes)
  - allowed_file_types: JSONField
  - due_date: DateTimeField (optional)
  - max_score: IntegerField
  - rubric: JSONField
  - is_published: BooleanField
```

### **Progress Tracking Models**
```yaml
Enrollment Model:
  - student: ForeignKey(User)
  - course: ForeignKey(Course)
  - enrollment_date: DateTimeField
  - completion_date: DateTimeField (optional)
  - status: active/completed/suspended/withdrawn
  - progress_percentage: DecimalField(5,2)
  - last_accessed: DateTimeField
  - certificate_issued: BooleanField

LessonProgress Model:
  - enrollment: ForeignKey(Enrollment)
  - lesson: ForeignKey(Lesson)
  - status: not_started/in_progress/completed
  - started_at: DateTimeField
  - completed_at: DateTimeField
  - time_spent: IntegerField (seconds)
  - attempts: IntegerField
  - score: DecimalField(5,2)

QuizAttempt Model:
  - student: ForeignKey(User)
  - quiz: ForeignKey(Quiz)
  - enrollment: ForeignKey(Enrollment)
  - attempt_number: IntegerField
  - started_at: DateTimeField
  - completed_at: DateTimeField
  - score: DecimalField(5,2)
  - answers: JSONField
  - is_passed: BooleanField
  - time_taken: IntegerField (seconds)
```

---

## **📊 CONTENT ANALYTICS & REPORTING**

### **Available Metrics**
```yaml
Course Analytics:
  - Enrollment numbers and trends
  - Completion rates by module/lesson
  - Average time spent per section
  - Quiz performance statistics
  - Assignment submission rates
  - Student engagement patterns

Student Progress:
  - Individual progress tracking
  - Time spent per lesson/module
  - Quiz scores and attempts
  - Assignment grades and feedback
  - Learning streak tracking
  - Achievement unlocks

Instructor Dashboard:
  - Course performance overview
  - Student progress summaries
  - Assessment results analysis
  - Content engagement metrics
  - Feedback and review compilation
```

---

## **🎓 CERTIFICATION SYSTEM**

### **Certificate Generation**
```yaml
Certificate Requirements:
  - Course completion (80% minimum progress)
  - All mandatory assessments passed
  - Minimum time requirements met
  - Final grade above passing threshold

Certificate Features:
  - Automated PDF generation
  - Unique verification codes
  - Digital signatures
  - Blockchain verification (planned)
  - Social media sharing
  - Employer verification portal

Certificate Content:
  - Student name and details
  - Course title and description
  - Completion date
  - Final grade/score
  - Instructor signature
  - Institution branding
  - Verification QR code
```

---

## **🔒 CONTENT SECURITY & ACCESS**

### **Access Control**
```yaml
Course Access:
  - Enrollment-based access
  - Payment verification required
  - Sequential lesson unlocking
  - Module prerequisite enforcement
  - Time-based content release

Content Protection:
  - Video streaming protection
  - Document download controls
  - Screenshot prevention (where possible)
  - Session timeout management
  - IP-based access restrictions (optional)

Privacy Settings:
  - Student progress visibility
  - Peer interaction controls
  - Data sharing preferences
  - Communication settings
  - Profile visibility options
```

---

## **📱 MOBILE & ACCESSIBILITY**

### **Mobile Optimization**
```yaml
Responsive Design:
  - Bootstrap 5 framework
  - Mobile-first approach
  - Touch-friendly interfaces
  - Optimized media loading
  - Offline content caching (planned)

Accessibility Features:
  - Screen reader compatibility
  - Keyboard navigation support
  - High contrast mode
  - Font size adjustment
  - Audio descriptions for videos
  - Closed captioning support
```

---

## **🔄 CONTENT VERSIONING & UPDATES**

### **Version Control**
```yaml
Content Updates:
  - Draft/published states
  - Version history tracking
  - Rollback capabilities
  - Change notifications
  - Student impact assessment

Update Process:
  - Instructor content editing
  - Admin review and approval
  - Staged deployment
  - Student notification
  - Progress preservation
```

---

## **📞 SUPPORT & RESOURCES**

### **Instructor Support**
- **Platform Training**: Comprehensive LMS usage training
- **Content Guidelines**: Best practices for course creation
- **Technical Assistance**: Upload and configuration support
- **Quality Review**: Pre-launch content evaluation
- **Ongoing Support**: Post-launch optimization assistance

### **Student Support**
- **Platform Navigation**: How to use the LMS effectively
- **Technical Issues**: Troubleshooting and problem resolution
- **Learning Support**: Study strategies and time management
- **Assessment Help**: Quiz and assignment guidance
- **Certificate Assistance**: Verification and sharing support

### **Contact Information**
- **Technical Support**: support@youthimpactglobal.com
- **Content Review**: content@youthimpactglobal.com
- **Instructor Training**: training@youthimpactglobal.com
- **Student Support**: students@youthimpactglobal.com

---

**🎯 FINAL NOTE**

This comprehensive guide ensures your course content aligns perfectly with our YITP LMS structure. By following these specifications, your course will provide an optimal learning experience with full platform feature utilization.

**Key Reminders:**
- Convert "units" to "modules" in your structure
- Follow the Course → Module → Lesson hierarchy
- Prepare assessments according to our question types
- Include clear learning objectives at every level
- Plan for sequential progression and prerequisites
- Design content for mobile and accessibility compliance

Your course success depends on proper structure alignment with our LMS capabilities!
