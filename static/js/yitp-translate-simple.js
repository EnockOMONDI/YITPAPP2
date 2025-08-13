/**
 * YITP Google Translate Integration - Standard Widget Approach
 * Simple and reliable using Google's standard implementation
 */

// Language configuration for display purposes
const YITP_LANGUAGES = {
    'en': { name: 'English', flag: '🇺🇸' },
    'fr': { name: 'Français', flag: '🇫🇷' },
    'sw': { name: 'Kiswahili', flag: '🇰🇪' },
    'ar': { name: 'العربية', flag: '🇸🇦' },
    'pt': { name: 'Português', flag: '🇵🇹' },
    'ha': { name: 'Hausa', flag: '🇳🇬' },
    'am': { name: 'አማርኛ', flag: '🇪🇹' }
};

let currentLanguage = 'en';

// Standard Google Translate initialization callback
function googleTranslateElementInit() {
    console.log('🚀 Initializing Google Translate...');

    new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,fr,sw,ar,pt,ha,am',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE
    }, 'google_translate_element');

    console.log('✅ Google Translate initialized');
}

// Create simple language selector that shows Google Translate widget
function createLanguageSelector() {
    console.log('🔧 Creating language selector...');

    // Find container
    const container = document.querySelector('.header__language');
    if (!container) {
        console.error('❌ Language container not found');
        return;
    }

    // Create simple button that shows Google Translate
    const selectorHTML = `
        <button class="btn yitp-translate-btn" onclick="toggleGoogleTranslate()"
                style="background: none; border: none; color: #1a2e53; padding: 8px 12px; border-radius: 6px; transition: all 0.3s ease;">
            <i class="fas fa-globe" style="color: #ff5d15; margin-right: 8px; font-size: 16px;"></i>
            <span style="font-weight: 500;">Translate</span>
        </button>
    `;

    container.innerHTML = selectorHTML;
    console.log('✅ Language selector created');
}

// Toggle Google Translate widget visibility
function toggleGoogleTranslate() {
    const widget = document.getElementById('google_translate_element');
    if (widget) {
        if (widget.style.display === 'none' || widget.style.display === '') {
            widget.style.display = 'block';
            widget.style.position = 'fixed';
            widget.style.top = '100px';
            widget.style.right = '20px';
            widget.style.zIndex = '9999';
            widget.style.background = 'white';
            widget.style.padding = '10px';
            widget.style.borderRadius = '8px';
            widget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
            console.log('✅ Google Translate widget shown');
        } else {
            widget.style.display = 'none';
            console.log('✅ Google Translate widget hidden');
        }
    } else {
        console.error('❌ Google Translate widget not found');
    }
}

// Simple initialization
function initializeTranslation() {
    console.log('🌐 Initializing YITP Translation System...');

    // Create Google Translate container
    let container = document.getElementById('google_translate_element');
    if (!container) {
        container = document.createElement('div');
        container.id = 'google_translate_element';
        container.style.display = 'none';
        document.body.appendChild(container);
        console.log('📦 Google Translate container created');
    }

    // Create language selector button
    createLanguageSelector();

    // Load Google Translate script
    const script = document.createElement('script');
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    script.async = true;
    document.head.appendChild(script);

    console.log('✅ Translation system initialized');
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initializeTranslation);

// Make toggle function globally available
window.toggleGoogleTranslate = toggleGoogleTranslate;

// Debug function
window.debugYITPTranslation = function() {
    console.log('🐛 YITP Translation Debug:');
    console.log('Language Button:', document.querySelector('.yitp-translate-btn'));
    console.log('Google Translate Element:', document.querySelector('#google_translate_element'));
    console.log('Google Translate Combo:', document.querySelector('.goog-te-combo'));
    console.log('Google Translate Widget Visible:',
        document.getElementById('google_translate_element')?.style.display !== 'none');
};
