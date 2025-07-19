// Course Builder JavaScript
class CourseBuilder {
    constructor() {
        this.currentStep = parseInt(document.getElementById('currentStep')?.value || 1);
        this.sessionId = document.getElementById('sessionId')?.value || null;
        this.courseId = document.getElementById('courseId')?.value || null;
        this.autoSaveInterval = null;
        this.courseData = {};
        
        this.init();
    }
    
    init() {
        this.setupAutoSave();
        this.setupDragAndDrop();
        this.loadSessionData();
        
        // Setup form validation
        this.setupFormValidation();
        
        // Setup event listeners
        this.setupEventListeners();
    }
    
    setupAutoSave() {
        // Auto-save every 30 seconds
        this.autoSaveInterval = setInterval(() => {
            this.saveSession();
        }, 30000);
        
        // Save on form changes
        document.addEventListener('input', (e) => {
            if (e.target.form) {
                clearTimeout(this.saveTimeout);
                this.saveTimeout = setTimeout(() => {
                    this.saveSession();
                }, 2000);
            }
        });
    }
    
    setupDragAndDrop() {
        // Setup sortable for modules
        const moduleContainer = document.getElementById('courseStructure');
        if (moduleContainer) {
            new Sortable(moduleContainer, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: () => {
                    this.updateModuleOrder();
                }
            });
        }
    }
    
    setupEventListeners() {
        // Course title and description preview updates
        const titleInput = document.getElementById('courseTitle');
        const descInput = document.getElementById('courseDescription');
        const priceInput = document.getElementById('coursePrice');
        const durationInput = document.getElementById('estimatedDuration');
        
        if (titleInput) {
            titleInput.addEventListener('input', (e) => {
                document.getElementById('previewTitle').textContent = e.target.value || 'Course Title';
            });
        }
        
        if (descInput) {
            descInput.addEventListener('input', (e) => {
                document.getElementById('previewDescription').textContent = e.target.value || 'Course description will appear here...';
            });
        }
        
        if (priceInput) {
            priceInput.addEventListener('input', (e) => {
                const price = parseFloat(e.target.value) || 0;
                document.getElementById('previewPrice').textContent = price > 0 ? `$${price}` : 'Free';
            });
        }
        
        if (durationInput) {
            durationInput.addEventListener('input', (e) => {
                document.getElementById('previewDuration').textContent = `${e.target.value || 10} hours`;
            });
        }
    }
    
    setupFormValidation() {
        // Add Bootstrap validation classes
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }
    
    async saveSession() {
        try {
            const sessionData = this.collectSessionData();

            const formData = new FormData();
            formData.append('action', 'save_session');
            formData.append('session_data', JSON.stringify(sessionData));
            formData.append('current_step', this.currentStep);
            formData.append('session_id', this.sessionId || '');
            formData.append('csrfmiddlewaretoken', this.getCSRFToken());

            const response = await fetch('/course-builder/api/', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.sessionId = result.session_id;
                const sessionIdInput = document.getElementById('sessionId');
                if (sessionIdInput) {
                    sessionIdInput.value = this.sessionId;
                }
                this.showAutoSaveIndicator();
                return result;
            } else {
                throw new Error(result.error || 'Failed to save session');
            }
        } catch (error) {
            console.error('Auto-save failed:', error);
            throw error;
        }
    }
    
    collectSessionData() {
        const data = {};

        // Collect data based on current step
        if (this.currentStep === 1) {
            // Try multiple ways to get form data
            const form = document.getElementById('courseBasicsForm');
            if (form) {
                const formData = new FormData(form);
                data.basics = {
                    title: formData.get('title') || document.getElementById('courseTitle')?.value || '',
                    description: formData.get('description') || document.getElementById('courseDescription')?.value || '',
                    category: formData.get('category') || document.getElementById('courseCategory')?.value || '',
                    difficulty_level: formData.get('difficulty_level') || document.getElementById('difficultyLevel')?.value || 'beginner',
                    estimated_duration: parseInt(formData.get('estimated_duration') || document.getElementById('estimatedDuration')?.value) || 10
                };
            } else {
                // Fallback to direct element access
                data.basics = {
                    title: document.getElementById('courseTitle')?.value || '',
                    description: document.getElementById('courseDescription')?.value || '',
                    category: document.getElementById('courseCategory')?.value || '',
                    difficulty_level: document.getElementById('difficultyLevel')?.value || 'beginner',
                    estimated_duration: parseInt(document.getElementById('estimatedDuration')?.value) || 10
                };
            }
        } else if (this.currentStep === 2) {
            data.structure = this.collectStructureData();
        } else if (this.currentStep === 3) {
            data.content = this.collectContentData();
        } else if (this.currentStep === 4) {
            data.assessments = this.collectAssessmentData();
        } else if (this.currentStep === 5) {
            const form = document.getElementById('publishingForm');
            if (form) {
                data.publishing = {
                    price: parseFloat(form.price?.value) || 0,
                    enrollment_limit: form.enrollment_limit?.value || null,
                    is_featured: form.is_featured?.checked || false
                };
            }
        }

        return data;
    }
    
    collectStructureData() {
        const modules = [];
        const moduleElements = document.querySelectorAll('.module-item');

        moduleElements.forEach((moduleEl, index) => {
            const moduleData = {
                title: moduleEl.querySelector('.module-title')?.value || '',
                description: moduleEl.querySelector('.module-description')?.value || '',
                sort_order: index,
                lessons: []
            };

            const lessonElements = moduleEl.querySelectorAll('.lesson-item');
            lessonElements.forEach((lessonEl, lessonIndex) => {
                moduleData.lessons.push({
                    title: lessonEl.querySelector('.lesson-title')?.value || '',
                    content_type: lessonEl.querySelector('.lesson-type')?.value || 'text',
                    sort_order: lessonIndex
                });
            });

            modules.push(moduleData);
        });

        return modules;
    }

    collectContentData() {
        const content = {};
        const lessonId = document.getElementById('lessonSelector')?.value;

        if (lessonId && typeof tinymce !== 'undefined' && tinymce.get('lessonContent')) {
            content[lessonId] = {
                content: tinymce.get('lessonContent').getContent(),
                video_url: document.getElementById('videoUrl')?.value || '',
                duration: parseInt(document.getElementById('lessonDuration')?.value) || 30
            };
        }

        return content;
    }

    collectAssessmentData() {
        const assessments = {};
        // Collect quiz data if any
        // This would be expanded based on the quiz creation interface
        return assessments;
    }
    
    showAutoSaveIndicator() {
        const indicator = document.getElementById('autoSaveIndicator');
        if (indicator) {
            indicator.classList.add('show');
            setTimeout(() => {
                indicator.classList.remove('show');
            }, 2000);
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
    
    loadSessionData() {
        // Load existing session data if available
        if (this.sessionId) {
            fetch('/course-builder/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `action=get_session&session_id=${this.sessionId}&csrfmiddlewaretoken=${this.getCSRFToken()}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.success && data.session_data) {
                    this.populateFormData(data.session_data);
                }
            })
            .catch(error => console.error('Error loading session data:', error));
        }
    }

    populateFormData(sessionData) {
        // Populate Step 1 data
        if (sessionData.basics) {
            const basics = sessionData.basics;
            if (document.getElementById('courseTitle')) {
                document.getElementById('courseTitle').value = basics.title || '';
            }
            if (document.getElementById('courseDescription')) {
                document.getElementById('courseDescription').value = basics.description || '';
            }
            if (document.getElementById('courseCategory')) {
                document.getElementById('courseCategory').value = basics.category || '';
            }
            if (document.getElementById('difficultyLevel')) {
                document.getElementById('difficultyLevel').value = basics.difficulty_level || 'beginner';
            }
            if (document.getElementById('estimatedDuration')) {
                document.getElementById('estimatedDuration').value = basics.estimated_duration || 10;
            }
        }

        // Populate Step 2 data
        if (sessionData.structure && this.currentStep === 2) {
            this.populateStructureData(sessionData.structure);
        }

        // Populate Step 3 data
        if (sessionData.content && this.currentStep === 3) {
            this.populateLessonSelector(sessionData.structure);
        }
    }

    populateStructureData(structureData) {
        const container = document.getElementById('courseStructure');
        if (container && structureData.length > 0) {
            container.innerHTML = '';
            structureData.forEach((module, index) => {
                addModule(module);
            });
        }
    }

    populateLessonSelector(structureData) {
        const selector = document.getElementById('lessonSelector');
        if (selector && structureData) {
            selector.innerHTML = '<option value="">Choose a lesson...</option>';
            structureData.forEach((module, moduleIndex) => {
                if (module.lessons) {
                    module.lessons.forEach((lesson, lessonIndex) => {
                        const option = document.createElement('option');
                        option.value = `${moduleIndex}-${lessonIndex}`;
                        option.textContent = `${module.title} - ${lesson.title}`;
                        selector.appendChild(option);
                    });
                }
            });
        }
    }
    
    updateModuleOrder() {
        // Update module order after drag and drop
        const moduleElements = document.querySelectorAll('.module-item');
        moduleElements.forEach((el, index) => {
            el.dataset.order = index;
        });
        this.saveSession();
    }

    validateCurrentStep() {
        if (this.currentStep === 1) {
            const title = document.getElementById('courseTitle')?.value?.trim();
            const description = document.getElementById('courseDescription')?.value?.trim();
            const category = document.getElementById('courseCategory')?.value;

            if (!title) {
                alert('Please enter a course title.');
                document.getElementById('courseTitle')?.focus();
                return false;
            }

            if (!description) {
                alert('Please enter a course description.');
                document.getElementById('courseDescription')?.focus();
                return false;
            }

            if (!category) {
                alert('Please select a course category.');
                document.getElementById('courseCategory')?.focus();
                return false;
            }
        }

        return true;
    }
}

// Global functions for template usage
function nextStep() {
    const builder = window.courseBuilder;
    if (builder && builder.currentStep < 5) {
        if (builder.validateCurrentStep()) {
            // Save current step data before navigating
            builder.saveSession().then(() => {
                const sessionParam = builder.sessionId ? `?session=${builder.sessionId}` : '';
                window.location.href = `/course-builder/wizard/step/${builder.currentStep + 1}/${sessionParam}`;
            }).catch(error => {
                console.error('Error saving session:', error);
                // Navigate anyway if save fails
                const sessionParam = builder.sessionId ? `?session=${builder.sessionId}` : '';
                window.location.href = `/course-builder/wizard/step/${builder.currentStep + 1}/${sessionParam}`;
            });
        }
    }
}

function previousStep() {
    const builder = window.courseBuilder;
    if (builder && builder.currentStep > 1) {
        const sessionParam = builder.sessionId ? `?session=${builder.sessionId}` : '';
        window.location.href = `/course-builder/wizard/step/${builder.currentStep - 1}/${sessionParam}`;
    }
}

function saveDraft() {
    const builder = window.courseBuilder;
    if (builder) {
        builder.saveSession().then(() => {
            showNotification('Draft saved successfully!', 'success');
        }).catch(error => {
            showNotification('Failed to save draft', 'error');
        });
    }
}

function publishCourse() {
    const builder = window.courseBuilder;
    if (builder) {
        if (confirm('Are you sure you want to publish this course? This will make it available to students.')) {
            // Save current step data first
            builder.saveSession().then(() => {
                // Call publish API
                const formData = new FormData();
                formData.append('action', 'publish_course');
                formData.append('session_id', builder.sessionId);
                formData.append('csrfmiddlewaretoken', getCSRFToken());

                fetch('/course-builder/api/', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Course published successfully!', 'success');
                        setTimeout(() => {
                            window.location.href = data.course_url || '/course-builder/';
                        }, 2000);
                    } else {
                        showNotification('Error: ' + data.error, 'error');
                    }
                })
                .catch(error => {
                    console.error('Publish error:', error);
                    showNotification('Failed to publish course', 'error');
                });
            });
        }
    }
}

function addModule(moduleData = null) {
    const container = document.getElementById('courseStructure');
    const moduleCount = container.children.length;

    const title = moduleData ? moduleData.title : '';
    const description = moduleData ? moduleData.description : '';

    const moduleHTML = `
        <div class="module-item" data-order="${moduleCount}">
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-grip-vertical drag-handle"></i>
                <h5 class="mb-0 ms-2">Module ${moduleCount + 1}</h5>
                <button type="button" class="btn btn-sm btn-outline-danger ms-auto" onclick="removeModule(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <input type="text" class="form-control module-title" placeholder="Module title" value="${title}" required>
                </div>
                <div class="col-md-6">
                    <input type="text" class="form-control module-description" placeholder="Module description" value="${description}">
                </div>
            </div>
            <div class="lessons-container mt-3">
                <!-- Lessons will be added here -->
            </div>
            <button type="button" class="btn btn-add-lesson mt-2" onclick="addLesson(this)">
                <i class="fas fa-plus me-2"></i>
                Add Lesson
            </button>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', moduleHTML);

    // Setup sortable for lessons in this module
    const newModule = container.lastElementChild;
    const lessonsContainer = newModule.querySelector('.lessons-container');
    new Sortable(lessonsContainer, {
        handle: '.drag-handle',
        animation: 150
    });

    // Add lessons if provided
    if (moduleData && moduleData.lessons) {
        moduleData.lessons.forEach(lessonData => {
            addLesson(newModule.querySelector('.btn-add-lesson'), lessonData);
        });
    }

    // Auto-save after adding module
    if (window.courseBuilder) {
        window.courseBuilder.saveSession();
    }
}

function addLesson(button, lessonData = null) {
    const lessonsContainer = button.previousElementSibling;
    const lessonCount = lessonsContainer.children.length;

    const title = lessonData ? lessonData.title : '';
    const contentType = lessonData ? lessonData.content_type : 'text';

    const lessonHTML = `
        <div class="lesson-item">
            <div class="d-flex align-items-center mb-2">
                <i class="fas fa-grip-vertical drag-handle"></i>
                <span class="ms-2">Lesson ${lessonCount + 1}</span>
                <button type="button" class="btn btn-sm btn-outline-danger ms-auto" onclick="removeLesson(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <input type="text" class="form-control lesson-title" placeholder="Lesson title" value="${title}" required>
                </div>
                <div class="col-md-6">
                    <select class="form-select lesson-type">
                        <option value="text" ${contentType === 'text' ? 'selected' : ''}>Text Content</option>
                        <option value="video" ${contentType === 'video' ? 'selected' : ''}>Video</option>
                        <option value="document" ${contentType === 'document' ? 'selected' : ''}>Document</option>
                        <option value="quiz" ${contentType === 'quiz' ? 'selected' : ''}>Quiz</option>
                    </select>
                </div>
            </div>
        </div>
    `;

    lessonsContainer.insertAdjacentHTML('beforeend', lessonHTML);

    // Auto-save after adding lesson
    if (window.courseBuilder) {
        window.courseBuilder.saveSession();
    }
}

function removeModule(button) {
    if (confirm('Are you sure you want to remove this module?')) {
        button.closest('.module-item').remove();
    }
}

function removeLesson(button) {
    if (confirm('Are you sure you want to remove this lesson?')) {
        button.closest('.lesson-item').remove();
    }
}

function loadTemplate(templateId) {
    // Implementation for loading course template
    console.log('Loading template:', templateId);
}

// Media and Template Functions
function openMediaLibrary() {
    window.open('/course-builder/media/', 'mediaLibrary', 'width=1000,height=700,scrollbars=yes');
}

function insertMediaIntoEditor(url, type) {
    // Insert media into TinyMCE editor
    if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
        if (type.startsWith('image/')) {
            tinymce.activeEditor.insertContent(`<img src="${url}" alt="Course Image" style="max-width: 100%; height: auto;">`);
        } else if (type.startsWith('video/')) {
            tinymce.activeEditor.insertContent(`<video controls style="max-width: 100%;"><source src="${url}" type="${type}">Your browser does not support the video tag.</video>`);
        } else {
            tinymce.activeEditor.insertContent(`<a href="${url}" target="_blank">Download File</a>`);
        }
    }
}

function insertTemplate(templateId) {
    // Fetch template content and insert into editor
    fetch(`/course-builder/api/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `action=get_template&template_id=${templateId}&csrfmiddlewaretoken=${getCSRFToken()}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && typeof tinymce !== 'undefined' && tinymce.activeEditor) {
            tinymce.activeEditor.insertContent(data.content);
        }
    })
    .catch(error => console.error('Error inserting template:', error));
}

function saveLessonContent() {
    const lessonId = document.getElementById('lessonSelector')?.value;
    if (!lessonId) {
        alert('Please select a lesson first');
        return;
    }

    let content = '';
    if (typeof tinymce !== 'undefined' && tinymce.get('lessonContent')) {
        content = tinymce.get('lessonContent').getContent();
    } else {
        content = document.getElementById('lessonContent')?.value || '';
    }

    const videoUrl = document.getElementById('videoUrl')?.value || '';
    const duration = document.getElementById('lessonDuration')?.value || 30;

    // Save via AJAX
    const formData = new FormData();
    formData.append('action', 'add_content');
    formData.append('lesson_id', lessonId);
    formData.append('content', content);
    formData.append('video_url', videoUrl);
    formData.append('duration', duration);
    formData.append('csrfmiddlewaretoken', getCSRFToken());

    fetch('/course-builder/api/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Content saved successfully!', 'success');
        } else {
            showNotification('Error: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Save error:', error);
        showNotification('Failed to save content', 'error');
    });
}

function loadLessonContent() {
    const lessonId = document.getElementById('lessonSelector')?.value;
    const editor = document.getElementById('lessonContentEditor');

    if (lessonId && editor) {
        editor.style.display = 'block';
        // Load existing content if available
        // This would fetch lesson content from the server
    } else if (editor) {
        editor.style.display = 'none';
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    notification.style.position = 'fixed';
    notification.style.top = '120px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';

    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
}

// Bulk Content Import Functions
function importFromWord() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.doc,.docx';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            // Implementation for Word import
            console.log('Importing Word document:', file.name);
            showNotification('Word import feature coming soon!', 'info');
        }
    };
    input.click();
}

function importFromPDF() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf';
    input.onchange = function(e) {
        const file = e.target.files[0];
        if (file) {
            // Implementation for PDF import
            console.log('Importing PDF:', file.name);
            showNotification('PDF import feature coming soon!', 'info');
        }
    };
    input.click();
}

// Enhanced Course Structure Functions
function duplicateModule(moduleElement) {
    const clone = moduleElement.cloneNode(true);
    const moduleTitle = clone.querySelector('.module-title');
    if (moduleTitle) {
        moduleTitle.value = moduleTitle.value + ' (Copy)';
    }
    moduleElement.parentNode.insertBefore(clone, moduleElement.nextSibling);
    updateModuleNumbers();
}

function duplicateLesson(lessonElement) {
    const clone = lessonElement.cloneNode(true);
    const lessonTitle = clone.querySelector('.lesson-title');
    if (lessonTitle) {
        lessonTitle.value = lessonTitle.value + ' (Copy)';
    }
    lessonElement.parentNode.insertBefore(clone, lessonElement.nextSibling);
    updateLessonNumbers();
}

function updateModuleNumbers() {
    const modules = document.querySelectorAll('.module-item');
    modules.forEach((module, index) => {
        const header = module.querySelector('h5');
        if (header) {
            header.textContent = `Module ${index + 1}`;
        }
    });
}

function updateLessonNumbers() {
    const modules = document.querySelectorAll('.module-item');
    modules.forEach(module => {
        const lessons = module.querySelectorAll('.lesson-item');
        lessons.forEach((lesson, index) => {
            const header = lesson.querySelector('span');
            if (header) {
                header.textContent = `Lesson ${index + 1}`;
            }
        });
    });
}

// Initialize course builder when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing Course Builder...');
    window.courseBuilder = new CourseBuilder();
    console.log('Course Builder initialized:', window.courseBuilder);

    // Add debug info
    console.log('Current step:', window.courseBuilder.currentStep);
    console.log('Session ID:', window.courseBuilder.sessionId);
});
