# YITP Course System Architecture & Structure

## Database Schema Overview

### Core Course Models

#### 1. Course Model
```python
# Primary course entity
- title: CharField(200) - Course title
- slug: SlugField(200) - URL-friendly identifier
- description: TextField - Course description
- learning_objectives: TextField - What students will learn
- prerequisites: TextField - Required knowledge/skills
- difficulty_level: CharField(20) - beginner/intermediate/advanced
- estimated_duration: IntegerField - Duration in hours
- thumbnail: ImageField - Course thumbnail image
- status: CharField(20) - draft/in_review/approved/published/rejected/archived
- is_published: BooleanField - Publication status
- is_featured: BooleanField - Featured course flag
- enrollment_limit: IntegerField - Maximum students
- price: DecimalField(10,2) - Course price in USD
- instructor: ForeignKey(User) - Course instructor
- category: ForeignKey(Category) - Course category
```

#### 2. Module Model
```python
# Course organizational units
- course: ForeignKey(Course) - Parent course
- title: CharField(200) - Module title
- description: TextField - Module description
- sort_order: IntegerField - Display order
- is_published: BooleanField - Publication status
- unlock_criteria: JSONField - Conditions for unlocking
- estimated_duration: IntegerField - Duration in minutes
```

#### 3. Lesson Model
```python
# Individual learning units
- module: ForeignKey(Module) - Parent module
- title: CharField(200) - Lesson title
- content_type: CharField(20) - text/video/presentation/exercise/quiz/assignment
- content: CKEditor5Field - Rich text content with formatting
- video_url: URLField - YouTube, Vimeo, or other video URL
- presentation_file: FileField - Presentation file upload
- sort_order: IntegerField - Display order
- is_published: BooleanField - Publication status
- is_mandatory: BooleanField - Required for completion
- estimated_duration: IntegerField - Duration in minutes
- learning_objectives: TextField - Lesson objectives
- resources: JSONField - Additional resources and links
```

### Content System Models

#### 4. ContentItem Model
```python
# Reusable content items
- title: CharField(200) - Content title
- content_type: CharField(30) - text/video/audio/presentation/document/interactive/image/infographic
- content: TextField - Text content or description
- file_path: FileField - File upload path
- external_url: URLField - External resource URL
- metadata: JSONField - Additional content metadata
- tags: JSONField - Content tags for search
- is_public: BooleanField - Available to all users
```

#### 5. LessonContent Model
```python
# Links lessons to content items
- lesson: ForeignKey(Lesson) - Target lesson
- content_item: ForeignKey(ContentItem) - Content item
- sort_order: IntegerField - Display order
- is_required: BooleanField - Required content flag
```

### Assessment System Models

#### 6. Quiz Model
```python
# Quiz assessments
- lesson: ForeignKey(Lesson) - Parent lesson
- title: CharField(200) - Quiz title
- description: TextField - Quiz description
- instructions: TextField - Quiz instructions
- time_limit: IntegerField - Time limit in minutes
- max_attempts: IntegerField - Maximum attempts allowed
- passing_score: IntegerField - Minimum score to pass (percentage)
- is_randomized: BooleanField - Randomize question order
- show_results: BooleanField - Show results immediately
- is_published: BooleanField - Publication status
```

#### 7. Question Model
```python
# Quiz questions
- quiz: ForeignKey(Quiz) - Parent quiz
- question_text: TextField - Question content
- question_type: CharField(20) - multiple_choice/true_false/short_answer/essay/matching/fill_blank
- options: JSONField - Options for multiple choice
- correct_answer: TextField - Correct answer or answer key
- explanation: TextField - Explanation for correct answer
- points: IntegerField - Points for correct answer
- sort_order: IntegerField - Display order
```

#### 8. Assignment Model
```python
# Assignment assessments
- lesson: ForeignKey(Lesson) - Parent lesson
- title: CharField(200) - Assignment title
- description: TextField - Assignment description
- instructions: TextField - Assignment instructions
- assignment_type: CharField(30) - business_plan/swot_analysis/case_study/reflection/presentation/project/research
- submission_format: CharField(20) - text/file/both
- max_file_size: IntegerField - Maximum file size in bytes
- allowed_file_types: JSONField - Allowed file extensions
- due_date: DateTimeField - Assignment due date
- max_score: IntegerField - Maximum score
- rubric: JSONField - Grading rubric
```

### Progress Tracking Models

#### 9. Enrollment Model
```python
# Student course enrollment
- student: ForeignKey(User) - Enrolled student
- course: ForeignKey(Course) - Enrolled course
- enrollment_date: DateTimeField - Enrollment date
- completion_date: DateTimeField - Course completion date
- status: CharField(20) - active/completed/dropped/suspended
- progress_percentage: DecimalField(5,2) - Progress percentage
- last_accessed: DateTimeField - Last access timestamp
- certificate_issued: BooleanField - Certificate issued flag
- privacy_settings: JSONField - Privacy settings
```

#### 10. LessonProgress Model
```python
# Individual lesson progress
- enrollment: ForeignKey(Enrollment) - Student enrollment
- lesson: ForeignKey(Lesson) - Target lesson
- status: CharField(20) - not_started/in_progress/completed/skipped
- started_at: DateTimeField - Start timestamp
- completed_at: DateTimeField - Completion timestamp
- time_spent: IntegerField - Time spent in seconds
- attempts: IntegerField - Number of attempts
- score: DecimalField(5,2) - Lesson score
```

#### 11. QuizAttempt Model
```python
# Quiz attempt tracking
- student: ForeignKey(User) - Student
- quiz: ForeignKey(Quiz) - Target quiz
- enrollment: ForeignKey(Enrollment) - Student enrollment
- attempt_number: IntegerField - Attempt number
- started_at: DateTimeField - Start timestamp
- completed_at: DateTimeField - Completion timestamp
- score: DecimalField(5,2) - Quiz score
- answers: JSONField - Student answers
- is_passed: BooleanField - Pass/fail status
- time_taken: IntegerField - Time taken in seconds
```

#### 12. Certificate Model
```python
# Course completion certificates
- enrollment: OneToOneField(Enrollment) - Student enrollment
- certificate_type: CharField(20) - completion/achievement/participation
- certificate_id: CharField(100) - Unique certificate ID
- issued_date: DateTimeField - Issue date
- final_score: DecimalField(5,2) - Final course score
- certificate_data: JSONField - Certificate template data
- is_verified: BooleanField - Verification status
- verification_code: CharField(50) - Verification code
```

## Content Format Support

### Supported Content Types

1. **Text Content**
   - Rich text with CKEditor5 formatting
   - Images, links, and interactive elements
   - Unlimited length

2. **Video Content**
   - YouTube integration via URL
   - Vimeo integration via URL
   - External video platform support
   - No file size limitations for external videos

3. **Presentation Content**
   - File upload support for presentations
   - PowerPoint, PDF, and other formats
   - File size limit: 10MB default (configurable)

4. **Document Content**
   - PDF documents
   - Word documents
   - Text files
   - File size limit: 10MB default (configurable)

5. **Interactive Content**
   - Custom interactive elements
   - Embedded content
   - External tool integration

6. **Image Content**
   - JPEG, PNG, GIF support
   - Thumbnail generation
   - Image optimization

7. **Audio Content**
   - MP3, WAV support
   - External audio platform integration

### File Upload Capabilities

- **Storage System**: Django FileField with configurable storage
- **Upload Path**: Organized by content type (presentations/, content/, resources/)
- **File Size Limits**: Configurable per content type (default 10MB)
- **Allowed Formats**: Configurable via JSONField in Assignment model
- **Security**: File type validation and secure upload handling

## Assessment System Analysis

### Quiz Types Supported

1. **Multiple Choice Questions**
   - Single correct answer
   - Multiple options (stored in JSONField)
   - Automatic grading

2. **True/False Questions**
   - Binary choice questions
   - Automatic grading

3. **Short Answer Questions**
   - Text-based responses
   - Manual or keyword-based grading

4. **Essay Questions**
   - Long-form text responses
   - Manual grading required

5. **Matching Questions**
   - Match items between two lists
   - Automatic grading

6. **Fill in the Blank**
   - Complete sentences or phrases
   - Automatic or manual grading

### Assignment Types Supported

1. **Business Plan** - Comprehensive business planning assignments
2. **SWOT Analysis** - Strengths, Weaknesses, Opportunities, Threats analysis
3. **Case Study Analysis** - Real-world scenario analysis
4. **Reflection Paper** - Personal reflection assignments
5. **Presentation** - Presentation-based assignments
6. **Project Work** - Hands-on project assignments
7. **Research Assignment** - Research-based assignments

### Grading and Feedback

- **Automatic Grading**: For objective questions (multiple choice, true/false)
- **Manual Grading**: For subjective content (essays, assignments)
- **Rubric Support**: JSONField-based rubric system
- **Score Tracking**: Decimal precision scoring
- **Passing Scores**: Configurable passing thresholds
- **Attempt Limits**: Configurable maximum attempts
- **Time Limits**: Optional time constraints

## Learning Flow Architecture

### Course Hierarchy
```
Course
├── Module 1
│   ├── Lesson 1.1 (with Quiz/Assignment)
│   ├── Lesson 1.2 (with Content Items)
│   └── Lesson 1.3
├── Module 2
│   ├── Lesson 2.1
│   └── Lesson 2.2
└── Module N
    └── Lesson N.N
```

### Sequential Progression System

1. **Course Level**: Students must enroll before accessing content
2. **Module Level**: Modules can have unlock criteria (JSONField)
3. **Lesson Level**: Sequential access within modules
4. **Assessment Level**: Quizzes/assignments linked to specific lessons

### Completion Requirements

1. **Lesson Completion**: 
   - View all required content
   - Complete mandatory assessments
   - Meet minimum score requirements

2. **Module Completion**:
   - Complete all mandatory lessons
   - Pass all required assessments

3. **Course Completion**:
   - Complete all modules
   - Achieve minimum overall progress (80%)
   - Pass all mandatory assessments

### Certification Process

1. **Eligibility Check**: 80% progress + course completion
2. **Certificate Generation**: Automatic upon eligibility
3. **Unique Identification**: Certificate ID and verification code
4. **Verification System**: Public verification via verification code
5. **Email Notifications**: Automatic certificate delivery

## Current Capabilities

### Strengths
- Comprehensive course hierarchy (Course → Module → Lesson)
- Rich content support (text, video, presentations, documents)
- Robust assessment system (quizzes, assignments, multiple question types)
- Progress tracking and analytics
- Certificate generation and verification
- Gamification features (points, achievements, streaks)
- Sequential learning flow with prerequisites
- File upload and external content integration

### Limitations Identified
- No built-in video hosting (relies on external platforms)
- File size limitations for uploads
- Manual grading required for subjective assessments
- Limited multimedia interaction features
- No real-time collaboration tools
- Basic content versioning

## Recommendations for Content Creation

1. **Use Rich Text Editor**: Leverage CKEditor5 for formatted content
2. **External Video Hosting**: Use YouTube/Vimeo for video content
3. **Modular Design**: Break content into digestible lessons
4. **Assessment Integration**: Include quizzes after each lesson
5. **Progressive Difficulty**: Structure content from basic to advanced
6. **Resource Links**: Use JSONField resources for additional materials
7. **Clear Objectives**: Define learning objectives for each lesson
8. **Estimated Duration**: Provide realistic time estimates
9. **Sequential Flow**: Design logical progression through content
10. **Certificate Worthy**: Ensure content meets certification standards
