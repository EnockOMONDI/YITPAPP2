/**
 * YITP Admin Custom JavaScript
 * Custom functionality for Django admin interface
 */

(function($) {
    'use strict';

    // Initialize when DOM is ready
    $(document).ready(function() {
        
        // Add YITP branding to admin
        initYITPBranding();
        
        // Enhance payment admin interface
        enhancePaymentAdmin();
        
        // Add custom admin functionality
        initCustomAdminFeatures();
    });

    function initYITPBranding() {
        // Add YITP colors to admin header
        if ($('#header').length) {
            $('#header').css({
                'background-color': '#341C67',
                'border-bottom': '3px solid #ff5d15'
            });
        }
        
        // Style admin title
        if ($('#site-name').length) {
            $('#site-name').css({
                'color': '#ff5d15',
                'font-weight': 'bold'
            });
        }
    }

    function enhancePaymentAdmin() {
        // Highlight confirmed payments in green
        $('.field-status').each(function() {
            var statusText = $(this).text().toLowerCase();
            if (statusText.includes('confirmed')) {
                $(this).css({
                    'background-color': '#d4edda',
                    'color': '#155724',
                    'padding': '4px 8px',
                    'border-radius': '4px',
                    'font-weight': 'bold'
                });
            } else if (statusText.includes('pending')) {
                $(this).css({
                    'background-color': '#fff3cd',
                    'color': '#856404',
                    'padding': '4px 8px',
                    'border-radius': '4px'
                });
            } else if (statusText.includes('failed')) {
                $(this).css({
                    'background-color': '#f8d7da',
                    'color': '#721c24',
                    'padding': '4px 8px',
                    'border-radius': '4px'
                });
            }
        });
        
        // Enhance amount display
        $('.field-amount_display').each(function() {
            $(this).css({
                'font-weight': 'bold',
                'color': '#ff5d15'
            });
        });
    }

    function initCustomAdminFeatures() {
        // Add quick actions for payments
        if (window.location.pathname.includes('/payments/payment/')) {
            addPaymentQuickActions();
        }
        
        // Add enrollment quick view
        if (window.location.pathname.includes('/progress/enrollment/')) {
            addEnrollmentQuickView();
        }
    }

    function addPaymentQuickActions() {
        // Add quick action buttons for payment management
        var quickActions = $('<div class="yitp-quick-actions" style="margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;"></div>');
        
        quickActions.append('<h4 style="margin: 0 0 10px 0; color: #341C67;">Quick Actions</h4>');
        
        // Add buttons based on payment status
        var confirmBtn = $('<button type="button" class="btn btn-success btn-sm" style="margin-right: 5px;">Confirm Payment</button>');
        var rejectBtn = $('<button type="button" class="btn btn-danger btn-sm" style="margin-right: 5px;">Reject Payment</button>');
        var emailBtn = $('<button type="button" class="btn btn-info btn-sm">Send Notification</button>');
        
        quickActions.append(confirmBtn).append(rejectBtn).append(emailBtn);
        
        // Insert after the form
        $('.form-row').first().before(quickActions);
    }

    function addEnrollmentQuickView() {
        // Add quick enrollment information
        var enrollmentInfo = $('<div class="yitp-enrollment-info" style="margin: 10px 0; padding: 10px; background: #e7f3ff; border-radius: 5px;"></div>');
        
        enrollmentInfo.append('<h4 style="margin: 0 0 10px 0; color: #341C67;">Enrollment Overview</h4>');
        enrollmentInfo.append('<p style="margin: 0;">Quick enrollment status and progress information will be displayed here.</p>');
        
        $('.form-row').first().before(enrollmentInfo);
    }

    // Utility functions
    function showAdminMessage(message, type) {
        type = type || 'info';
        var messageDiv = $('<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert"></div>');
        messageDiv.html(message + '<button type="button" class="close" data-dismiss="alert"><span>&times;</span></button>');
        
        $('.content').prepend(messageDiv);
        
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            messageDiv.fadeOut();
        }, 5000);
    }

})(django.jQuery || jQuery);

// Additional admin enhancements
document.addEventListener('DOMContentLoaded', function() {
    // Add YITP favicon if not present
    if (!document.querySelector('link[rel="icon"]')) {
        var favicon = document.createElement('link');
        favicon.rel = 'icon';
        favicon.href = '/static/img/favicon.png';
        document.head.appendChild(favicon);
    }
    
    // Add custom CSS for better admin experience
    var customCSS = document.createElement('style');
    customCSS.textContent = `
        .yitp-admin-enhancement {
            border-left: 4px solid #ff5d15;
            padding-left: 10px;
        }
        
        .payment-status-confirmed {
            background-color: #d4edda !important;
            color: #155724 !important;
        }
        
        .payment-status-pending {
            background-color: #fff3cd !important;
            color: #856404 !important;
        }
        
        .payment-status-failed {
            background-color: #f8d7da !important;
            color: #721c24 !important;
        }
    `;
    document.head.appendChild(customCSS);
});
