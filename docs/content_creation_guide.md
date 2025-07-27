# YITP Content Creation Guide - CKEditor 5

## Overview

The YITP Learning Management System now features **CKEditor 5**, a modern, secure, and feature-rich content editor that provides instructors and content creators with powerful tools for creating engaging educational content.

## Key Features

### 🔒 **Enhanced Security**
- **Modern Architecture**: CKEditor 5 eliminates security vulnerabilities present in CKEditor 4
- **Secure File Uploads**: Enhanced file upload security with proper validation
- **XSS Protection**: Built-in protection against cross-site scripting attacks

### 🎨 **YITP-Branded Interface**
- **Custom Styling**: Editor interface matches YITP brand colors (#ff5d15 orange, #1a2e53 dark blue)
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Accessibility**: Enhanced keyboard navigation and screen reader support

## Content Editor Configurations

### 📝 **Default Configuration**
Used for: Blog posts, static content, general text editing

**Available Tools:**
- **Headings**: H1, H2, H3, H4 for content structure
- **Text Formatting**: Bold, italic, underline, strikethrough
- **Colors**: Font color and background color options
- **Alignment**: Left, center, right, justify
- **Lists**: Numbered and bulleted lists with indent/outdent
- **Links**: Smart link insertion with external link detection
- **Media**: Image insertion with alignment options
- **Tables**: Full table editing with merge capabilities
- **Special Elements**: Horizontal lines, block quotes
- **Code Blocks**: Syntax-highlighted code blocks
- **History**: Undo/redo functionality
- **Source Editing**: Direct HTML editing when needed

### 🎓 **Lesson Content Configuration**
Used for: Course lessons, educational materials, detailed content

**Enhanced Features:**
- **All Default Tools** plus:
- **Highlight Markers**: Yellow, green, and pink highlighting
- **Code Syntax**: Support for Python, JavaScript, HTML, CSS, SQL, JSON
- **Special Characters**: Extended character set for educational content
- **Advanced Tables**: Enhanced table editing capabilities

### ⚡ **Basic Configuration**
Used for: Comments, quick notes, simple text areas

**Simplified Tools:**
- **Essential Formatting**: Bold, italic, underline
- **Lists**: Basic numbered and bulleted lists
- **Links**: Simple link insertion
- **Cleanup**: Remove formatting and source editing

## Content Creation Best Practices

### 📚 **Educational Content Structure**

#### 1. **Use Proper Headings**
```
# Lesson Title (H1)
## Learning Objectives (H2)
### Key Concepts (H3)
#### Detailed Points (H4)
```

#### 2. **Highlight Important Information**
- **Yellow Marker**: Key concepts and definitions
- **Green Marker**: Success tips and best practices
- **Pink Marker**: Warnings and important notes

#### 3. **Code Examples**
Use code blocks with appropriate syntax highlighting:
- **Python**: For programming examples
- **HTML/CSS**: For web development content
- **SQL**: For database queries
- **JSON**: For data structure examples

### 🎯 **Content Organization**

#### **Learning Objectives**
Start each lesson with clear learning objectives:
1. What students will learn
2. Skills they will develop
3. Knowledge they will gain

#### **Content Flow**
- **Introduction**: Brief overview
- **Main Content**: Detailed explanation with examples
- **Practice**: Hands-on exercises
- **Summary**: Key takeaways
- **Next Steps**: What comes next

#### **Visual Elements**
- **Images**: Use relevant, high-quality images
- **Tables**: Organize data and comparisons
- **Block Quotes**: Highlight important quotes or principles
- **Horizontal Lines**: Separate content sections

## File Upload Guidelines

### 📁 **Supported File Types**
- **Images**: JPG, PNG, GIF, WebP
- **Documents**: PDF (for reference materials)
- **Media**: Video files (for embedded content)

### 📏 **File Size Limits**
- **Images**: Maximum 5MB per file
- **Documents**: Maximum 10MB per file
- **Total Upload**: 50MB per lesson

### 🖼️ **Image Best Practices**
- **Resolution**: Use appropriate resolution for web (72-150 DPI)
- **Dimensions**: Optimize for responsive display
- **Alt Text**: Always provide descriptive alt text for accessibility
- **File Names**: Use descriptive, SEO-friendly file names

## Accessibility Features

### ♿ **Built-in Accessibility**
- **Keyboard Navigation**: Full keyboard support for all features
- **Screen Reader Support**: Compatible with assistive technologies
- **High Contrast**: Supports high contrast mode
- **Focus Indicators**: Clear visual focus indicators

### 📝 **Content Accessibility**
- **Heading Structure**: Use proper heading hierarchy
- **Link Text**: Use descriptive link text
- **Image Alt Text**: Provide meaningful alt text
- **Color Contrast**: Ensure sufficient color contrast
- **Table Headers**: Use proper table headers

## Troubleshooting

### 🔧 **Common Issues**

#### **Editor Not Loading**
1. Clear browser cache
2. Disable browser extensions
3. Check JavaScript console for errors
4. Try a different browser

#### **File Upload Failures**
1. Check file size limits
2. Verify file type is supported
3. Ensure stable internet connection
4. Contact admin if issues persist

#### **Formatting Issues**
1. Use "Remove Format" tool to clean up
2. Switch to source editing mode
3. Copy content to plain text editor first
4. Paste as plain text and reformat

### 📞 **Getting Help**
- **Documentation**: Refer to this guide
- **Admin Support**: Contact system administrators
- **Training**: Request additional training sessions
- **Feedback**: Report bugs or feature requests

## Advanced Features

### 🔗 **Link Management**
- **External Links**: Automatically open in new tabs
- **Internal Links**: Link to other courses or content
- **Email Links**: Create mailto links
- **Anchor Links**: Link to specific sections

### 📊 **Table Features**
- **Responsive Tables**: Tables adapt to screen size
- **Cell Merging**: Combine cells for complex layouts
- **Header Rows**: Designate header rows for accessibility
- **Table Styling**: Basic styling options available

### 💾 **Content Backup**
- **Auto-Save**: Content is automatically saved as you type
- **Version History**: Previous versions are maintained
- **Export Options**: Export content for backup
- **Import**: Import content from other sources

---

**Last Updated**: January 26, 2025  
**CKEditor Version**: 5.x  
**YITP Platform**: Learning Management System  
**Support**: Contact YITP Technical Team
