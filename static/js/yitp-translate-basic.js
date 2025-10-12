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

// Comprehensive Google Translate banner hiding system
function hideGoogleTranslateBanner() {
    console.log('🚫 Aggressively hiding Google Translate banners...');

    // Comprehensive list of banner selectors
    const bannerSelectors = [
        '.goog-te-banner-frame',
        '.goog-te-banner-frame.skiptranslate',
        'body > .skiptranslate:not([id*="google_translate_element"])',
        '.skiptranslate iframe',
        'iframe.skiptranslate',
        'iframe[src*="translate.google"]',
        'iframe[src*="translate_a"]',
        '[id*="goog-te-banner"]',
        '[class*="goog-te-banner"]',
        '[id*="google_translate_banner"]',
        '[class*="google_translate_banner"]'
    ];

    let hiddenCount = 0;

    bannerSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            // Hide all banner elements aggressively
            element.style.display = 'none';
            element.style.visibility = 'hidden';
            element.style.opacity = '0';
            element.style.height = '0';
            element.style.width = '0';
            element.style.position = 'absolute';
            element.style.left = '-10000px';
            element.style.top = '-10000px';
            element.style.zIndex = '-1';
            element.style.overflow = 'hidden';

            // Remove from DOM if possible
            if (element.parentNode) {
                element.parentNode.removeChild(element);
                hiddenCount++;
            }
        });
    });

    // Force reset body styles that Google modifies
    document.body.style.top = '0';
    document.body.style.marginTop = '0';
    document.body.style.paddingTop = '0';
    document.body.style.position = '';

    // Remove any style attributes Google adds to body
    const bodyStyle = document.body.getAttribute('style');
    if (bodyStyle && (bodyStyle.includes('top:') || bodyStyle.includes('margin-top:') || bodyStyle.includes('padding-top:'))) {
        document.body.removeAttribute('style');
    }

    if (hiddenCount > 0) {
        console.log(`✅ Hidden ${hiddenCount} Google Translate banner elements`);
    }
}

// Set up continuous banner monitoring
function setupBannerMonitoring() {
    console.log('👁️ Setting up continuous Google Translate banner monitoring...');

    // Initial banner hiding
    hideGoogleTranslateBanner();

    // Set up MutationObserver to watch for new banner elements
    const observer = new MutationObserver(function(mutations) {
        let shouldHideBanners = false;

        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        // Check if the added node is a banner or contains banner elements
                        if (node.className && (
                            node.className.includes('goog-te-banner') ||
                            node.className.includes('skiptranslate')
                        )) {
                            shouldHideBanners = true;
                        }

                        // Check for banner elements within the added node
                        if (node.querySelector && (
                            node.querySelector('.goog-te-banner-frame') ||
                            node.querySelector('.skiptranslate iframe') ||
                            node.querySelector('iframe[src*="translate"]')
                        )) {
                            shouldHideBanners = true;
                        }
                    }
                });
            }

            // Check for style changes to body element
            if (mutation.type === 'attributes' &&
                mutation.target === document.body &&
                mutation.attributeName === 'style') {
                const bodyStyle = document.body.getAttribute('style');
                if (bodyStyle && (bodyStyle.includes('top:') || bodyStyle.includes('margin'))) {
                    shouldHideBanners = true;
                }
            }
        });

        if (shouldHideBanners) {
            console.log('🔍 Detected Google Translate banner changes, hiding...');
            hideGoogleTranslateBanner();
        }
    });

    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });

    // Also run banner hiding periodically as backup
    setInterval(hideGoogleTranslateBanner, 1000);

    console.log('✅ Banner monitoring system active');
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

    // Set up comprehensive banner monitoring system
    setTimeout(setupBannerMonitoring, 1000);

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
