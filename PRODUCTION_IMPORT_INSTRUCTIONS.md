
# YITP Introductory Course - Production Import Instructions

## Method 1: Using Django Migration (Recommended)

1. Deploy the code with the migration file to production
2. Run migrations in production:
   ```bash
   python manage.py migrate
   ```

## Method 2: Using Django Fixtures (Alternative)

1. Upload the intro_course_complete.json file to production
2. Import the data:
   ```bash
   python manage.py loaddata intro_course_complete.json
   ```

## Method 3: Using Management Command (Direct)

1. Run the management command directly in production:
   ```bash
   python manage.py create_intro_course
   ```

## Verification Steps

After deployment, verify the course:

1. Check course exists:
   ```bash
   python manage.py shell -c "
   from courses.models import Course
   course = Course.objects.get(title__icontains='Introduction to YITP')
   print(f'Course: {course.title}')
   print(f'Instructor: {course.instructor.username}')
   print(f'Price: ${course.price}')
   print(f'Status: {course.status}')
   "
   ```

2. Check quiz questions:
   ```bash
   python manage.py shell -c "
   from assessments.models import Quiz
   quiz = Quiz.objects.get(title__icontains='YITP Platform Knowledge')
   print(f'Quiz: {quiz.title}')
   print(f'Questions: {quiz.total_questions}')
   print(f'Passing Score: {quiz.passing_score}%')
   "
   ```

3. Test instructor login:
   - Username: yitpteam
   - Password: sLXSxmMg3tVeV64
   - Email: enockomondike@gmail.com

## Production URLs

- Admin: https://www.youthimpactglobal.com/admin/
- Course Catalog: https://www.youthimpactglobal.com/courses/
- Course should appear as "Introduction to YITP: Your Learning Journey Begins"

## Course Details

- Title: Introduction to YITP: Your Learning Journey Begins
- Type: Mandatory first course for all new students
- Duration: 25 minutes
- Price: Free ($0.00)
- Quiz: 8 questions, 70% passing score
- Instructor: yitpteam (enockomondike@gmail.com)
