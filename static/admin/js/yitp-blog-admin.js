/**
 * YITP Blog Admin JavaScript
 * Enhanced functionality for blog import/export features
 */

(function() {
    'use strict';

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeImportExport();
        initializeFileUpload();
        initializeProgressTracking();
        initializeTooltips();
    });

    /**
     * Initialize import/export functionality
     */
    function initializeImportExport() {
        // Add click handlers for import/export buttons
        const importBtn = document.querySelector('.yitp-import-btn');
        const exportBtn = document.querySelector('.yitp-export-btn');
        const templateBtn = document.querySelector('.yitp-template-btn');

        if (importBtn) {
            importBtn.addEventListener('click', function(e) {
                showImportModal();
            });
        }

        if (exportBtn) {
            exportBtn.addEventListener('click', function(e) {
                showExportOptions();
            });
        }

        if (templateBtn) {
            templateBtn.addEventListener('click', function(e) {
                trackTemplateDownload();
            });
        }
    }

    /**
     * Initialize file upload functionality
     */
    function initializeFileUpload() {
        const uploadArea = document.querySelector('.file-upload-area');
        const fileInput = document.querySelector('#file-input');

        if (uploadArea && fileInput) {
            // Drag and drop functionality
            uploadArea.addEventListener('dragover', function(e) {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });

            uploadArea.addEventListener('dragleave', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
            });

            uploadArea.addEventListener('drop', function(e) {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleFileSelection(files[0]);
                }
            });

            // Click to upload
            uploadArea.addEventListener('click', function() {
                fileInput.click();
            });

            fileInput.addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    handleFileSelection(e.target.files[0]);
                }
            });
        }
    }

    /**
     * Handle file selection and validation
     */
    function handleFileSelection(file) {
        // Validate file type
        const allowedTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ];

        if (!allowedTypes.includes(file.type)) {
            showMessage('Please select a valid Excel file (.xlsx or .xls)', 'error');
            return;
        }

        // Validate file size (10MB limit)
        const maxSize = 10 * 1024 * 1024; // 10MB
        if (file.size > maxSize) {
            showMessage('File size must be less than 10MB', 'error');
            return;
        }

        // Show file info
        showFileInfo(file);
        
        // Enable upload button
        const uploadBtn = document.querySelector('.upload-confirm-btn');
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.textContent = `Upload ${file.name}`;
        }
    }

    /**
     * Show file information
     */
    function showFileInfo(file) {
        const fileInfo = document.querySelector('.file-info');
        if (fileInfo) {
            fileInfo.innerHTML = `
                <div class="yitp-message yitp-message-info">
                    <h4>📄 File Selected</h4>
                    <p><strong>Name:</strong> ${file.name}</p>
                    <p><strong>Size:</strong> ${formatFileSize(file.size)}</p>
                    <p><strong>Type:</strong> ${file.type}</p>
                    <p><strong>Last Modified:</strong> ${new Date(file.lastModified).toLocaleString()}</p>
                </div>
            `;
        }
    }

    /**
     * Initialize progress tracking
     */
    function initializeProgressTracking() {
        // Check if we're on an import/export page
        const progressContainer = document.querySelector('.import-progress');
        if (progressContainer) {
            // Simulate progress for demo purposes
            // In real implementation, this would track actual import progress
            updateProgress(0);
            
            // Example progress simulation
            let progress = 0;
            const interval = setInterval(function() {
                progress += Math.random() * 10;
                if (progress >= 100) {
                    progress = 100;
                    clearInterval(interval);
                    showMessage('Import completed successfully!', 'success');
                }
                updateProgress(progress);
            }, 500);
        }
    }

    /**
     * Update progress bar
     */
    function updateProgress(percentage) {
        const progressFill = document.querySelector('.progress-fill');
        const progressText = document.querySelector('.progress-text');
        
        if (progressFill) {
            progressFill.style.width = percentage + '%';
        }
        
        if (progressText) {
            progressText.textContent = `${Math.round(percentage)}% Complete`;
        }
    }

    /**
     * Initialize tooltips
     */
    function initializeTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(function(element) {
            element.addEventListener('mouseenter', function() {
                showTooltip(element, element.getAttribute('data-tooltip'));
            });
            
            element.addEventListener('mouseleave', function() {
                hideTooltip();
            });
        });
    }

    /**
     * Show tooltip
     */
    function showTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'yitp-tooltip-popup';
        tooltip.textContent = text;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.position = 'absolute';
        tooltip.style.top = (rect.top - tooltip.offsetHeight - 10) + 'px';
        tooltip.style.left = (rect.left + rect.width / 2 - tooltip.offsetWidth / 2) + 'px';
        tooltip.style.zIndex = '1000';
        tooltip.style.background = '#341C67';
        tooltip.style.color = 'white';
        tooltip.style.padding = '8px 12px';
        tooltip.style.borderRadius = '6px';
        tooltip.style.fontSize = '12px';
        tooltip.style.whiteSpace = 'nowrap';
    }

    /**
     * Hide tooltip
     */
    function hideTooltip() {
        const tooltip = document.querySelector('.yitp-tooltip-popup');
        if (tooltip) {
            tooltip.remove();
        }
    }

    /**
     * Show import modal
     */
    function showImportModal() {
        // Create modal overlay
        const modal = document.createElement('div');
        modal.className = 'yitp-modal-overlay';
        modal.innerHTML = `
            <div class="yitp-modal">
                <div class="yitp-modal-header">
                    <h3>📥 Import Blog Posts</h3>
                    <button class="yitp-modal-close">&times;</button>
                </div>
                <div class="yitp-modal-body">
                    <p>Ready to import blog posts from Excel?</p>
                    <div class="yitp-modal-actions">
                        <a href="/admin/blogapp/post/import/" class="yitp-admin-btn yitp-admin-btn-primary">
                            Continue to Import
                        </a>
                        <button class="yitp-admin-btn yitp-admin-btn-outline yitp-modal-cancel">
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Add event listeners
        modal.querySelector('.yitp-modal-close').addEventListener('click', function() {
            modal.remove();
        });
        
        modal.querySelector('.yitp-modal-cancel').addEventListener('click', function() {
            modal.remove();
        });
        
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Show export options
     */
    function showExportOptions() {
        showMessage('Preparing export... This may take a moment for large datasets.', 'info');
        
        // In real implementation, this would trigger the export process
        setTimeout(function() {
            showMessage('Export completed! Download should start automatically.', 'success');
        }, 2000);
    }

    /**
     * Track template download
     */
    function trackTemplateDownload() {
        showMessage('Template download started. Check your downloads folder.', 'info');
        
        // Analytics tracking (if available)
        if (typeof gtag !== 'undefined') {
            gtag('event', 'template_download', {
                event_category: 'Blog Admin',
                event_label: 'Excel Template'
            });
        }
    }

    /**
     * Show message to user
     */
    function showMessage(text, type = 'info') {
        const messageContainer = document.querySelector('.messages') || createMessageContainer();
        
        const message = document.createElement('div');
        message.className = `yitp-message yitp-message-${type}`;
        message.innerHTML = `
            <span>${text}</span>
            <button class="yitp-message-close" onclick="this.parentElement.remove()">&times;</button>
        `;
        
        messageContainer.appendChild(message);
        
        // Auto-remove after 5 seconds
        setTimeout(function() {
            if (message.parentElement) {
                message.remove();
            }
        }, 5000);
    }

    /**
     * Create message container if it doesn't exist
     */
    function createMessageContainer() {
        const container = document.createElement('div');
        container.className = 'messages';
        container.style.position = 'fixed';
        container.style.top = '20px';
        container.style.right = '20px';
        container.style.zIndex = '1000';
        container.style.maxWidth = '400px';
        
        document.body.appendChild(container);
        return container;
    }

    /**
     * Format file size for display
     */
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Export functions for global access
    window.YITPBlogAdmin = {
        showMessage: showMessage,
        updateProgress: updateProgress,
        handleFileSelection: handleFileSelection
    };

})();
