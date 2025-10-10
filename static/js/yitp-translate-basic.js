/**
 * YITP Google Translate - Native Dropdown Implementation
 * Shows Google's native language dropdown directly in navbar
 */

// Google Translate initialization with native dropdown
function googleTranslateElementInit() {
    console.log('🚀 Initializing YITP Native Google Translate...');

    // Create native widget directly in navbar container
    const navbarContainer = document.querySelector('.header__language');
    if (navbarContainer) {
        // Clear any existing content
        navbarContainer.innerHTML = '';

        // Create container for Google Translate widget
        const translateContainer = document.createElement('div');
        translateContainer.id = 'google_translate_element';
        translateContainer.style.cssText = `
            display: block !important;
            visibility: visible !important;
        `;
        navbarContainer.appendChild(translateContainer);

        // Initialize Google Translate with native dropdown
        new google.translate.TranslateElement({
            pageLanguage: 'en',
            includedLanguages: 'en,fr,sw,ar,pt,ha,am',
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false,
            multilanguagePage: true
        }, 'google_translate_element');

        console.log('✅ Native Google Translate dropdown initialized in navbar');

        // Apply YITP styling after widget loads
        setTimeout(function() {
            applyYITPStyling();
        }, 1500);
    } else {
        console.log('❌ Navbar language container not found');
    }
}

// Apply YITP styling to Google Translate elements
function applyYITPStyling() {
    console.log('🎨 Applying YITP styling to native Google Translate...');

    // Style the main widget container
    const widget = document.getElementById('google_translate_element');
    if (widget) {
        widget.style.cssText = `
            display: block !important;
            visibility: visible !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        `;
    }

    // Style the dropdown selector with YITP branding
    const combo = document.querySelector('.goog-te-combo');
    if (combo) {
        combo.style.cssText = `
            background: linear-gradient(135deg, #ff5d15 0%, #e04a0f 100%) !important;
            color: white !important;
            border: 2px solid #ff5d15 !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            cursor: pointer !important;
            min-width: 150px !important;
            box-shadow: 0 2px 8px rgba(255, 93, 21, 0.2) !important;
        `;

        console.log('✅ YITP styling applied to dropdown');
    } else {
        console.log('⏳ Dropdown not ready yet, will retry...');
        // Retry after a short delay
        setTimeout(applyYITPStyling, 500);
    }

    // Style the gadget container
    const gadget = document.querySelector('.goog-te-gadget');
    if (gadget) {
        gadget.style.cssText = `
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            font-size: 14px !important;
        `;
    }
}

// Hide Google Translate banner (targeted approach)
function hideGoogleTranslateBanner() {
    console.log('🚫 Hiding Google Translate banner...');

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

// Initialize everything
function initTranslation() {
    console.log('🌐 Initializing YITP Native Translation System...');

    // Check if navbar language container exists
    const navbarContainer = document.querySelector('.header__language');
    if (!navbarContainer) {
        console.log('❌ Navbar language container not found');
        return;
    }

    // Load Google Translate script
    if (!document.querySelector('script[src*="translate.google.com"]')) {
        const script = document.createElement('script');
        script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        script.async = true;
        document.head.appendChild(script);

        console.log('📡 Loading Google Translate API for native dropdown...');
    }

    // Set up banner hiding
    setTimeout(hideGoogleTranslateBanner, 2000);

    console.log('✅ YITP Native Translation initialization complete');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initTranslation);

// Debug function for testing
window.debugYITPTranslation = function() {
    console.log('🔍 YITP Translation Debug Info:');
    console.log('Widget exists:', !!document.getElementById('google_translate_element'));
    console.log('Button exists:', !!document.querySelector('.yitp-translate-btn'));
    console.log('Google script loaded:', !!document.querySelector('script[src*="translate.google.com"]'));
    console.log('Combo dropdown exists:', !!document.querySelector('.goog-te-combo'));

    const widget = document.getElementById('google_translate_element');
    if (widget) {
        console.log('Widget HTML:', widget.innerHTML);
        console.log('Widget display:', widget.style.display);
    }
};
