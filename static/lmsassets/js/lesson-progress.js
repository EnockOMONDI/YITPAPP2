/**
 * YITP LMS Lesson Progress Management
 * Handles lesson completion, progress tracking, and navigation
 */

class YITPLessonProgress {
    constructor() {
        this.courseSlug = null;
        this.currentLessonId = null;
        this.csrfToken = null;
        this.init();
    }

    init() {
        // Get CSRF token
        this.csrfToken = this.getCSRFToken();
        
        // Get course and lesson info from page
        this.extractPageInfo();
        
        // Bind event listeners
        this.bindEvents();
        
        // Initialize progress tracking
        this.initProgressTracking();
        
        console.log('YITP Lesson Progress initialized');
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : null;
    }

    extractPageInfo() {
        // Extract from URL or data attributes
        const path = window.location.pathname;
        const courseMatch = path.match(/\/lms\/courses\/([^\/]+)\//);
        const lessonMatch = path.match(/\/lessons\/(\d+)\//);
        
        if (courseMatch) {
            this.courseSlug = courseMatch[1];
        }
        
        if (lessonMatch) {
            this.currentLessonId = parseInt(lessonMatch[1]);
        }
        
        // Also check data attributes
        const courseElement = document.querySelector('[data-course-slug]');
        const lessonElement = document.querySelector('[data-lesson-id]');
        
        if (courseElement) {
            this.courseSlug = courseElement.dataset.courseSlug;
        }
        
        if (lessonElement) {
            this.currentLessonId = parseInt(lessonElement.dataset.lessonId);
        }
    }

    bindEvents() {
        // Lesson completion buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-complete-lesson')) {
                e.preventDefault();
                this.markLessonComplete(e.target);
            }
            
            if (e.target.matches('.btn-start-lesson')) {
                e.preventDefault();
                this.startLesson(e.target);
            }
            
            if (e.target.matches('.btn-next-lesson')) {
                e.preventDefault();
                this.goToNextLesson(e.target);
            }
        });

        // Auto-save progress on scroll
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.updateScrollProgress();
            }, 1000);
        });

        // Track time spent on lesson
        this.startTimeTracking();
    }

    initProgressTracking() {
        // Update progress bars on page load
        this.updateProgressBars();
        
        // Check if lesson should be auto-marked as started
        if (this.currentLessonId) {
            this.markLessonStarted(this.currentLessonId);
        }
    }

    async markLessonComplete(button) {
        if (!this.currentLessonId) {
            console.error('No current lesson ID found');
            return;
        }

        // Show loading state
        const originalText = button.textContent;
        button.textContent = 'Completing...';
        button.disabled = true;

        try {
            const response = await fetch(`/lms/api/lessons/${this.currentLessonId}/complete/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    lesson_id: this.currentLessonId,
                    completion_time: new Date().toISOString()
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Update button state
                button.textContent = 'Completed ✓';
                button.classList.remove('btn-primary-yitp');
                button.classList.add('btn-success');
                
                // Update progress
                this.updateProgressBars();
                
                // Show next lesson button
                this.showNextLessonButton();
                
                // Show completion message
                this.showCompletionMessage(data.message || 'Lesson completed successfully!');
                
            } else {
                throw new Error('Failed to mark lesson as complete');
            }
        } catch (error) {
            console.error('Error completing lesson:', error);
            button.textContent = originalText;
            button.disabled = false;
            this.showErrorMessage('Failed to mark lesson as complete. Please try again.');
        }
    }

    async startLesson(button) {
        if (!this.currentLessonId) {
            console.error('No current lesson ID found');
            return;
        }

        try {
            const response = await fetch(`/lms/api/lessons/${this.currentLessonId}/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    lesson_id: this.currentLessonId,
                    start_time: new Date().toISOString()
                })
            });

            if (response.ok) {
                // Update button to show in progress
                button.textContent = 'In Progress';
                button.classList.remove('btn-secondary-yitp');
                button.classList.add('btn-warning');
                
                // Show complete button
                this.showCompleteButton();
            }
        } catch (error) {
            console.error('Error starting lesson:', error);
        }
    }

    async markLessonStarted(lessonId) {
        try {
            await fetch(`/lms/api/lessons/${lessonId}/start/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken
                },
                body: JSON.stringify({
                    lesson_id: lessonId,
                    start_time: new Date().toISOString(),
                    auto_start: true
                })
            });
        } catch (error) {
            console.error('Error auto-starting lesson:', error);
        }
    }

    goToNextLesson(button) {
        const nextLessonUrl = button.dataset.nextLessonUrl;
        if (nextLessonUrl) {
            window.location.href = nextLessonUrl;
        }
    }

    updateProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar[data-progress]');
        progressBars.forEach(bar => {
            const progress = parseFloat(bar.dataset.progress);
            bar.style.width = `${progress}%`;
            
            // Update progress text
            const progressText = bar.closest('.progress-container')?.querySelector('.progress-percentage');
            if (progressText) {
                progressText.textContent = `${Math.round(progress)}%`;
            }
        });
    }

    updateScrollProgress() {
        if (!this.currentLessonId) return;

        const scrollPercent = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
        
        // Send scroll progress to server
        fetch(`/lms/api/lessons/${this.currentLessonId}/progress/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                scroll_progress: Math.min(scrollPercent, 100),
                timestamp: new Date().toISOString()
            })
        }).catch(error => {
            console.error('Error updating scroll progress:', error);
        });
    }

    startTimeTracking() {
        this.startTime = Date.now();
        
        // Send time updates every 30 seconds
        this.timeTrackingInterval = setInterval(() => {
            this.updateTimeSpent();
        }, 30000);
        
        // Send final time on page unload
        window.addEventListener('beforeunload', () => {
            this.updateTimeSpent();
        });
    }

    updateTimeSpent() {
        if (!this.currentLessonId || !this.startTime) return;

        const timeSpent = Math.floor((Date.now() - this.startTime) / 1000);
        
        fetch(`/lms/api/lessons/${this.currentLessonId}/time/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            },
            body: JSON.stringify({
                time_spent: timeSpent,
                timestamp: new Date().toISOString()
            })
        }).catch(error => {
            console.error('Error updating time spent:', error);
        });
    }

    showCompleteButton() {
        const completeButton = document.querySelector('.btn-complete-lesson');
        if (completeButton) {
            completeButton.style.display = 'inline-block';
        }
    }

    showNextLessonButton() {
        const nextButton = document.querySelector('.btn-next-lesson');
        if (nextButton) {
            nextButton.style.display = 'inline-block';
        }
    }

    showCompletionMessage(message) {
        // Create or update completion message
        let messageEl = document.querySelector('.lesson-completion-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.className = 'alert alert-success lesson-completion-message';
            messageEl.innerHTML = `
                <i class="fas fa-check-circle"></i>
                <span class="message-text">${message}</span>
            `;
            
            const container = document.querySelector('.lesson-actions') || document.querySelector('.lesson-content');
            if (container) {
                container.appendChild(messageEl);
            }
        } else {
            messageEl.querySelector('.message-text').textContent = message;
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            messageEl.style.opacity = '0';
            setTimeout(() => {
                messageEl.remove();
            }, 300);
        }, 5000);
    }

    showErrorMessage(message) {
        // Create error message
        const errorEl = document.createElement('div');
        errorEl.className = 'alert alert-danger lesson-error-message';
        errorEl.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            <span class="message-text">${message}</span>
        `;
        
        const container = document.querySelector('.lesson-actions') || document.querySelector('.lesson-content');
        if (container) {
            container.appendChild(errorEl);
        }
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorEl.style.opacity = '0';
            setTimeout(() => {
                errorEl.remove();
            }, 300);
        }, 5000);
    }

    destroy() {
        if (this.timeTrackingInterval) {
            clearInterval(this.timeTrackingInterval);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.yitpLessonProgress = new YITPLessonProgress();
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.yitpLessonProgress) {
        window.yitpLessonProgress.destroy();
    }
});
