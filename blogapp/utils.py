"""
YITP Blog Utilities
Excel template generation and import/export helper functions
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.datavalidation import DataValidation
from django.http import HttpResponse
from django.utils import timezone
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def create_blog_import_template():
    """
    Create a comprehensive Excel template for blog post imports
    Returns an HttpResponse with the Excel file
    """
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Blog Posts Import Template"
    
    # Define headers with descriptions
    headers = [
        ('title', 'Post Title (Required)', 'The main title of the blog post'),
        ('content', 'Content (Required)', 'Full HTML content of the blog post'),
        ('author', 'Author Name', 'Author display name (defaults to YITP Admin)'),
        ('category', 'Category', 'Category name (will be created if not exists)'),
        ('tags', 'Tags', 'Comma-separated tags (e.g., "tech, education, youth")'),
        ('user', 'User', 'Username or email of the user (optional)'),
        ('status', 'Status', 'draft, in_review, or published (default: draft)'),
        ('featured', 'Featured', 'TRUE/FALSE - Is this a featured post?'),
        ('trending', 'Trending', 'TRUE/FALSE - Is this a trending post?'),
        ('publication_date', 'Publication Date', 'YYYY-MM-DD HH:MM:SS format (optional)'),
        ('featured_image_url', 'Featured Image URL', 'URL to the featured image (optional)'),
        ('meta_description', 'Meta Description', 'SEO meta description (future use)'),
    ]
    
    # Style definitions
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1a2e53", end_color="1a2e53", fill_type="solid")  # YITP dark blue
    description_font = Font(italic=True, color="666666", size=9)
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Set column widths and headers
    for col_num, (field, header, description) in enumerate(headers, 1):
        # Set column width
        ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = 20
        
        # Header row
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = border
        
        # Description row
        desc_cell = ws.cell(row=2, column=col_num, value=description)
        desc_cell.font = description_font
        desc_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        desc_cell.border = border
    
    # Set row heights
    ws.row_dimensions[1].height = 25
    ws.row_dimensions[2].height = 40
    
    # Add data validation for status column
    status_validation = DataValidation(
        type="list",
        formula1='"draft,in_review,published"',
        allow_blank=True
    )
    status_validation.error = "Please select a valid status: draft, in_review, or published"
    status_validation.errorTitle = "Invalid Status"
    status_col = headers.index(('status', 'Status', 'draft, in_review, or published (default: draft)')) + 1
    ws.add_data_validation(status_validation)
    status_validation.add(f"{openpyxl.utils.get_column_letter(status_col)}3:{openpyxl.utils.get_column_letter(status_col)}1000")
    
    # Add data validation for boolean fields
    bool_validation = DataValidation(
        type="list",
        formula1='"TRUE,FALSE"',
        allow_blank=True
    )
    bool_validation.error = "Please enter TRUE or FALSE"
    bool_validation.errorTitle = "Invalid Boolean Value"
    
    for field_name in ['featured', 'trending']:
        field_index = next(i for i, (f, _, _) in enumerate(headers) if f == field_name)
        col_letter = openpyxl.utils.get_column_letter(field_index + 1)
        ws.add_data_validation(bool_validation)
        bool_validation.add(f"{col_letter}3:{col_letter}1000")
    
    # Add sample data rows
    sample_data = [
        {
            'title': 'Sample Blog Post 1',
            'content': '<p>This is a sample blog post content with <strong>HTML formatting</strong>.</p>',
            'author': 'John Doe',
            'category': 'Technology',
            'tags': 'tech, innovation, youth',
            'user': '',
            'status': 'draft',
            'featured': 'FALSE',
            'trending': 'FALSE',
            'publication_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'featured_image_url': 'https://example.com/image1.jpg',
            'meta_description': 'Sample meta description for SEO',
        },
        {
            'title': 'Sample Blog Post 2',
            'content': '<p>Another sample post about <em>youth empowerment</em> and education.</p>',
            'author': 'Jane Smith',
            'category': 'Education',
            'tags': 'education, empowerment, skills',
            'user': '',
            'status': 'published',
            'featured': 'TRUE',
            'trending': 'TRUE',
            'publication_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'featured_image_url': 'https://example.com/image2.jpg',
            'meta_description': 'Educational content for youth development',
        }
    ]
    
    # Add sample data
    for row_num, sample in enumerate(sample_data, 3):
        for col_num, (field, _, _) in enumerate(headers, 1):
            value = sample.get(field, '')
            cell = ws.cell(row=row_num, column=col_num, value=value)
            cell.border = border
            if row_num == 3:  # First sample row
                cell.fill = PatternFill(start_color="E8F4FD", end_color="E8F4FD", fill_type="solid")
    
    # Add instructions worksheet
    instructions_ws = wb.create_sheet("Instructions")
    instructions_ws.column_dimensions['A'].width = 80
    
    instructions = [
        "YITP Blog Import Template - Instructions",
        "",
        "OVERVIEW:",
        "This template allows you to import multiple blog posts into the YITP blog system.",
        "Fill in the data starting from row 3 (sample data provided).",
        "",
        "REQUIRED FIELDS:",
        "• title: The main title of your blog post",
        "• content: Full content of the blog post (HTML formatting supported)",
        "",
        "OPTIONAL FIELDS:",
        "• author: Author name (defaults to 'YITP Admin' if empty)",
        "• category: Category name (will be created automatically if it doesn't exist)",
        "• tags: Comma-separated list of tags",
        "• user: Username or email of the WordPress user (optional)",
        "• status: Must be 'draft', 'in_review', or 'published' (defaults to 'draft')",
        "• featured: TRUE or FALSE (defaults to FALSE)",
        "• trending: TRUE or FALSE (defaults to FALSE)",
        "• publication_date: Format YYYY-MM-DD HH:MM:SS (defaults to current time)",
        "• featured_image_url: URL to the featured image",
        "• meta_description: SEO meta description (for future use)",
        "",
        "TIPS:",
        "1. Remove the sample data rows before importing your actual data",
        "2. Categories will be created automatically if they don't exist",
        "3. Tags will be created automatically if they don't exist",
        "4. HTML formatting is supported in the content field",
        "5. Boolean fields accept: TRUE/FALSE, 1/0, YES/NO",
        "6. Leave optional fields empty if not needed",
        "",
        "IMPORT PROCESS:",
        "1. Fill in your blog post data",
        "2. Save the file as .xlsx format",
        "3. Go to Django Admin > Blog Posts",
        "4. Click 'Import' button",
        "5. Upload your file and review the preview",
        "6. Confirm the import",
        "",
        "For support, contact: youthimpactglobal3@gmail.com"
    ]
    
    for row_num, instruction in enumerate(instructions, 1):
        cell = instructions_ws.cell(row=row_num, column=1, value=instruction)
        if row_num == 1:  # Title
            cell.font = Font(bold=True, size=14, color="1a2e53")
        elif instruction.endswith(":"):  # Section headers
            cell.font = Font(bold=True, color="ff5d15")
        cell.alignment = Alignment(wrap_text=True, vertical='top')
    
    # Save to BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    # Create HTTP response
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="YITP_Blog_Import_Template_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    
    logger.info("Generated blog import template")
    return response


def validate_import_file(file):
    """
    Validate uploaded Excel file before processing
    """
    errors = []
    
    # Check file size (max 10MB)
    if file.size > 10 * 1024 * 1024:
        errors.append("File size must be less than 10MB")
    
    # Check file extension
    if not file.name.lower().endswith(('.xlsx', '.xls')):
        errors.append("File must be an Excel file (.xlsx or .xls)")
    
    try:
        # Try to open the file
        wb = openpyxl.load_workbook(file, read_only=True)
        ws = wb.active
        
        # Check if file has data
        if ws.max_row < 3:  # Header + description + at least one data row
            errors.append("File must contain at least one data row")
        
        # Check required columns
        required_columns = ['title', 'content']
        header_row = [cell.value for cell in ws[1]]
        
        for required_col in required_columns:
            if not any(required_col.lower() in str(header).lower() for header in header_row if header):
                errors.append(f"Required column '{required_col}' not found")
        
    except Exception as e:
        errors.append(f"Invalid Excel file: {str(e)}")
    
    return errors
