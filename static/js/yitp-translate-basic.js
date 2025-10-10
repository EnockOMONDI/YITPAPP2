/**
 * YITP Google Translate - Ultra Simple Implementation
 * Just the basic Google Translate widget with minimal customization
 */

// Google Translate initialization with banner hiding
function googleTranslateElementInit() {
    console.log('🚀 Initializing Google Translate...');

    // Create widget in the main container
    new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,fr,sw,ar,pt,ha,am',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
    }, 'google_translate_element');

    // Also create in navbar if container exists
    const navbarContainer = document.getElementById('google_translate_element_navbar');
    if (navbarContainer) {
        new google.translate.TranslateElement({
            pageLanguage: 'en',
            includedLanguages: 'en,fr,sw,ar,pt,ha,am',
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element_navbar');

        navbarContainer.style.display = 'block';
    }

    // Hide Google Translate banner immediately and continuously
    hideGoogleTranslateBanner();

    // Set up mutation observer to hide banner if it appears
    setupBannerHiding();

    console.log('✅ Google Translate initialized with banner hiding');
}

// Function to hide Google Translate banner (more targeted)
function hideGoogleTranslateBanner() {
    // Only hide actual banner elements, not dropdown containers
    const bannerSelectors = [
        '.goog-te-banner-frame',
        '.goog-te-banner-frame.skiptranslate'
    ];

    bannerSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            // Only hide if it's actually a banner (has banner-like characteristics)
            if (element.innerHTML && (
                element.innerHTML.includes('Google Translate') ||
                element.innerHTML.includes('Translated by') ||
                element.style.position === 'fixed' && element.style.top === '0px'
            )) {
                element.style.display = 'none';
                element.style.visibility = 'hidden';
                element.style.opacity = '0';
                element.style.height = '0';
                element.style.overflow = 'hidden';
            }
        });
    });

    // Reset body top margin/padding that Google might add
    document.body.style.top = '0';
    document.body.style.marginTop = '0';
    document.body.style.paddingTop = '0';
}

// Set up mutation observer to continuously hide banner
function setupBannerHiding() {
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Check for new banner elements
                hideGoogleTranslateBanner();
            }
        });
    });

    // Observe the entire document for changes
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Also hide banner every 500ms as a fallback
    setInterval(hideGoogleTranslateBanner, 500);
}

// Create translate button that shows the widget
function createTranslateButton() {
    const container = document.querySelector('.header__language');
    if (!container) return;
    
    // Only create if not already exists
    if (container.querySelector('.yitp-translate-btn')) return;
    
    const button = document.createElement('button');
    button.className = 'btn yitp-translate-btn';
    button.innerHTML = `
        <i class="fas fa-globe" style="color: #ff5d15; margin-right: 8px;"></i>
        <span>Translate</span>
    `;
    button.style.cssText = `
        background: none; 
        border: none; 
        color: #1a2e53; 
        padding: 8px 12px; 
        border-radius: 6px; 
        transition: all 0.3s ease;
        font-weight: 500;
    `;
    
    button.onclick = function() {
        console.log('🌐 YITP Translate button clicked');

        const widget = document.getElementById('google_translate_element');
        const navbarWidget = document.getElementById('google_translate_element_navbar');

        console.log('Widget found:', !!widget);
        console.log('Widget content:', widget ? widget.innerHTML : 'No widget');

        if (widget) {
            if (widget.style.display === 'none' || !widget.style.display) {
                console.log('📖 Showing Google Translate widget');

                // Show widget with minimal positioning to avoid conflicts
                widget.style.display = 'block';
                widget.style.position = 'fixed';
                widget.style.top = '80px';
                widget.style.right = '20px';
                widget.style.zIndex = '10000';
                widget.style.maxWidth = '300px';

                // Let CSS handle the styling instead of JavaScript
                widget.classList.add('yitp-translate-widget-visible');

                // Check what Google Translate elements are present
                setTimeout(() => {
                    const combo = widget.querySelector('.goog-te-combo');
                    const gadget = widget.querySelector('.goog-te-gadget');
                    console.log('Combo found:', !!combo);
                    console.log('Gadget found:', !!gadget);
                    console.log('Widget HTML:', widget.innerHTML);
                }, 500);
            } else {
                console.log('🔒 Hiding Google Translate widget');
                widget.style.display = 'none';
                widget.classList.remove('yitp-translate-widget-visible');
            }
        } else {
            console.log('❌ Google Translate widget not found');
        }
        
        // Toggle navbar widget visibility
        if (navbarWidget) {
            navbarWidget.style.display = navbarWidget.style.display === 'none' ? 'block' : 'none';
        }
    };
    
    // Add hover effects
    button.onmouseover = function() {
        this.style.backgroundColor = 'rgba(255, 93, 21, 0.1)';
        this.style.color = '#ff5d15';
    };
    button.onmouseout = function() {
        this.style.backgroundColor = 'transparent';
        this.style.color = '#1a2e53';
    };
    
    container.appendChild(button);
}

// Initialize everything
function initTranslation() {
    console.log('🌐 Initializing YITP Translation...');
    
    // Create main Google Translate container
    let container = document.getElementById('google_translate_element');
    if (!container) {
        container = document.createElement('div');
        container.id = 'google_translate_element';
        container.style.display = 'none';
        document.body.appendChild(container);
    }
    
    // Create translate button
    createTranslateButton();
    
    // Load Google Translate script
    if (!document.querySelector('script[src*="translate.google.com"]')) {
        const script = document.createElement('script');
        script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        script.async = true;
        document.head.appendChild(script);
    }
    
    console.log('✅ Translation initialization complete');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initTranslation);

// Make functions globally available for testing
window.toggleGoogleTranslate = function() {
    const widget = document.getElementById('google_translate_element');
    if (widget) {
        if (widget.style.display === 'none' || !widget.style.display) {
            widget.style.display = 'block';
            widget.style.position = 'fixed';
            widget.style.top = '100px';
            widget.style.right = '20px';
            widget.style.zIndex = '9999';
            widget.style.background = 'white';
            widget.style.padding = '15px';
            widget.style.borderRadius = '8px';
            widget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            widget.style.border = '1px solid #ddd';
        } else {
            widget.style.display = 'none';
        }
    }
};

// Debug function
window.debugYITPTranslation = function() {
    console.log('🐛 YITP Translation Debug:');
    console.log('Translate Button:', document.querySelector('.yitp-translate-btn'));
    console.log('Main Widget:', document.querySelector('#google_translate_element'));
    console.log('Navbar Widget:', document.querySelector('#google_translate_element_navbar'));
    console.log('Google Translate Combo:', document.querySelector('.goog-te-combo'));
    console.log('Widget Visible:', document.getElementById('google_translate_element')?.style.display !== 'none');
};
