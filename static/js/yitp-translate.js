/**
 * YITP Google Translate Integration
 * Provides seamless translation functionality for the entire YITP platform
 */

// YITP Translation Configuration
const YITPTranslate = {
    // Supported languages with African focus
    languages: {
        'en': { name: 'English', flag: '🇺🇸', code: 'en' },
        'fr': { name: 'Français', flag: '🇫🇷', code: 'fr' },
        'sw': { name: 'Kiswahili', flag: '🇰🇪', code: 'sw' },
        'ar': { name: 'العربية', flag: '🇸🇦', code: 'ar' },
        'pt': { name: 'Português', flag: '🇵🇹', code: 'pt' },
        'ha': { name: 'Hausa', flag: '🇳🇬', code: 'ha' },
        'am': { name: 'አማርኛ', flag: '🇪🇹', code: 'am' }
    },

    // Current language state
    currentLanguage: 'en',
    
    // Google Translate element
    googleTranslateElement: null,

    // Initialize translation system
    init: function() {
        console.log('🌐 Initializing YITP Translation System...');
        try {
            this.loadSavedLanguage();
            console.log('✅ Language preference loaded:', this.currentLanguage);

            this.createLanguageSelector();
            console.log('✅ Language selector created');

            this.initializeGoogleTranslate();
            console.log('✅ Google Translate initialized');

            this.bindEvents();
            console.log('✅ Events bound');

            console.log('🎉 YITP Translation System Initialized Successfully');
        } catch (error) {
            console.error('❌ Error initializing translation system:', error);
        }
    },

    // Load saved language preference
    loadSavedLanguage: function() {
        const saved = localStorage.getItem('yitp_language');
        if (saved && this.languages[saved]) {
            this.currentLanguage = saved;
        }
    },

    // Save language preference
    saveLanguage: function(langCode) {
        localStorage.setItem('yitp_language', langCode);
        this.currentLanguage = langCode;
    },

    // Create language selector UI
    createLanguageSelector: function() {
        this.createDesktopLanguageSelector();
        this.createMobileLanguageSelector();
    },

    // Create desktop language selector
    createDesktopLanguageSelector: function() {
        let headerLanguage = document.querySelector('.header__language');

        // If container doesn't exist, create it and insert it in the navbar
        if (!headerLanguage) {
            console.warn('⚠️ Header language container not found, creating fallback...');

            // Try to find the auth section to insert before it
            const authSection = document.querySelector('.header__auth');
            if (authSection && authSection.parentNode) {
                headerLanguage = document.createElement('div');
                headerLanguage.className = 'header__language d-none d-lg-block';
                headerLanguage.style.marginRight = '15px';
                authSection.parentNode.insertBefore(headerLanguage, authSection);
                console.log('✅ Created fallback language container');
            } else {
                console.error('❌ Could not create language container - auth section not found');
                return;
            }
        }

        console.log('📱 Creating desktop language selector...');

        const languageSelector = document.createElement('div');
        languageSelector.className = 'dropdown yitp-language-selector';
        languageSelector.innerHTML = `
            <a class="dropdown-toggle d-flex align-items-center" href="#" id="languageDropdown"
               role="button" data-bs-toggle="dropdown" aria-expanded="false"
               style="color: #1a2e53; text-decoration: none; padding: 8px 12px; border-radius: 6px; transition: all 0.3s ease;">
                <i class="fas fa-globe" style="color: #ff5d15; margin-right: 8px; font-size: 16px;"></i>
                <span id="currentLanguageFlag" style="font-size: 16px; margin-right: 5px;">${this.languages[this.currentLanguage].flag}</span>
                <span id="currentLanguageName" class="d-none d-lg-inline" style="font-weight: 500; margin-right: 5px;">${this.languages[this.currentLanguage].name}</span>
                <i class="fas fa-chevron-down" style="font-size: 12px; color: #ff5d15;"></i>
            </a>
            <ul class="dropdown-menu dropdown-menu-end yitp-language-menu" aria-labelledby="languageDropdown">
                ${this.generateLanguageOptions()}
            </ul>
        `;

        headerLanguage.appendChild(languageSelector);
        console.log('✅ Desktop language selector created');
    },

    // Create mobile language selector
    createMobileLanguageSelector: function() {
        const mobileContainer = document.getElementById('mobile-language-options');
        if (!mobileContainer) return;

        mobileContainer.innerHTML = this.generateMobileLanguageOptions();
    },

    // Generate language options HTML
    generateLanguageOptions: function() {
        return Object.entries(this.languages).map(([code, lang]) => `
            <li>
                <a class="dropdown-item yitp-language-option" href="#" data-lang="${code}">
                    <span class="language-flag">${lang.flag}</span>
                    <span class="language-name">${lang.name}</span>
                    ${code === this.currentLanguage ? '<i class="fas fa-check text-success ms-2"></i>' : ''}
                </a>
            </li>
        `).join('');
    },

    // Generate mobile language options HTML
    generateMobileLanguageOptions: function() {
        return Object.entries(this.languages).map(([code, lang]) => `
            <div class="mobile__language-option ${code === this.currentLanguage ? 'active' : ''}" data-lang="${code}">
                <div class="language__item d-flex align-items-center p-10" style="border-radius: 6px; cursor: pointer; transition: all 0.3s ease;">
                    <span class="language-flag" style="font-size: 18px; margin-right: 10px;">${lang.flag}</span>
                    <span class="language-name" style="font-weight: 500; color: #1a2e53;">${lang.name}</span>
                    ${code === this.currentLanguage ? '<i class="fas fa-check text-success ms-auto"></i>' : ''}
                </div>
            </div>
        `).join('');
    },

    // Initialize Google Translate
    initializeGoogleTranslate: function() {
        console.log('🔄 Initializing Google Translate...');

        // Create Google Translate element container (hidden)
        let container = document.getElementById('google_translate_element');
        if (!container) {
            container = document.createElement('div');
            container.id = 'google_translate_element';
            container.style.display = 'none';
            document.body.appendChild(container);
            console.log('📦 Google Translate container created');
        }

        // Set global callback first
        const self = this;
        window.googleTranslateElementInit = function() {
            console.log('🚀 Google Translate callback triggered');
            try {
                self.googleTranslateElement = new google.translate.TranslateElement({
                    pageLanguage: 'en',
                    includedLanguages: Object.keys(self.languages).join(','),
                    layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
                    autoDisplay: false,
                    multilanguagePage: true
                }, 'google_translate_element');

                console.log('✅ Google Translate element created');

                // Apply saved language after initialization
                setTimeout(() => {
                    if (self.currentLanguage !== 'en') {
                        console.log('🔄 Applying saved language:', self.currentLanguage);
                        self.translateTo(self.currentLanguage);
                    }
                }, 2000);
            } catch (error) {
                console.error('❌ Error creating Google Translate element:', error);
            }
        };

        // Load Google Translate script
        if (!window.google || !window.google.translate) {
            console.log('📥 Loading Google Translate script...');
            const script = document.createElement('script');
            script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
            script.async = true;
            script.onerror = function() {
                console.error('❌ Failed to load Google Translate script');
            };
            script.onload = function() {
                console.log('✅ Google Translate script loaded');
            };
            document.head.appendChild(script);
        } else {
            console.log('♻️ Google Translate already loaded, initializing...');
            window.googleTranslateElementInit();
        }
    },

    // Translate to specific language
    translateTo: function(langCode) {
        if (!this.languages[langCode]) return;

        // Update UI
        this.updateLanguageSelector(langCode);
        this.saveLanguage(langCode);

        // Trigger Google Translate
        if (langCode === 'en') {
            // Reset to original language
            this.resetTranslation();
        } else {
            // Translate to target language
            this.triggerGoogleTranslate(langCode);
        }

        // Update page metadata
        this.updatePageMetadata(langCode);
    },

    // Trigger Google Translate programmatically
    triggerGoogleTranslate: function(langCode, retryCount = 0) {
        console.log(`🔄 Attempting to translate to ${langCode} (attempt ${retryCount + 1})`);

        const selectElement = document.querySelector('.goog-te-combo');
        if (selectElement) {
            console.log('✅ Google Translate select element found');
            selectElement.value = langCode;
            selectElement.dispatchEvent(new Event('change'));
            console.log(`🌐 Translation triggered for ${langCode}`);

            // Show translation status
            this.showTranslationStatus(`Translating to ${this.languages[langCode].name}...`);
        } else {
            console.warn(`⚠️ Google Translate select element not found (attempt ${retryCount + 1})`);
            // Retry up to 10 times with increasing delays
            if (retryCount < 10) {
                const delay = Math.min(500 * (retryCount + 1), 5000);
                setTimeout(() => this.triggerGoogleTranslate(langCode, retryCount + 1), delay);
            } else {
                console.error('❌ Failed to find Google Translate element after 10 attempts');
                this.showTranslationStatus('Translation failed. Please refresh the page.', 'error');
            }
        }
    },

    // Reset translation to original language
    resetTranslation: function() {
        const selectElement = document.querySelector('.goog-te-combo');
        if (selectElement) {
            selectElement.value = '';
            selectElement.dispatchEvent(new Event('change'));
        }
    },

    // Update language selector UI
    updateLanguageSelector: function(langCode) {
        // Update desktop selector
        const flagElement = document.getElementById('currentLanguageFlag');
        const nameElement = document.getElementById('currentLanguageName');

        if (flagElement) flagElement.textContent = this.languages[langCode].flag;
        if (nameElement) nameElement.textContent = this.languages[langCode].name;

        // Update desktop dropdown options
        const dropdown = document.querySelector('.yitp-language-menu');
        if (dropdown) {
            dropdown.innerHTML = this.generateLanguageOptions();
        }

        // Update mobile selector
        const mobileContainer = document.getElementById('mobile-language-options');
        if (mobileContainer) {
            mobileContainer.innerHTML = this.generateMobileLanguageOptions();
        }

        // Re-bind events
        this.bindLanguageEvents();
    },

    // Update page metadata for SEO
    updatePageMetadata: function(langCode) {
        // Update HTML lang attribute
        document.documentElement.lang = langCode;

        // Update or create hreflang links
        this.updateHreflangTags(langCode);
    },

    // Update hreflang tags for SEO
    updateHreflangTags: function(currentLang) {
        // Remove existing hreflang tags
        document.querySelectorAll('link[hreflang]').forEach(link => link.remove());

        // Add hreflang tags for all supported languages
        const baseUrl = window.location.origin + window.location.pathname;
        
        Object.keys(this.languages).forEach(langCode => {
            const link = document.createElement('link');
            link.rel = 'alternate';
            link.hreflang = langCode;
            link.href = `${baseUrl}?lang=${langCode}`;
            document.head.appendChild(link);
        });

        // Add x-default for English
        const defaultLink = document.createElement('link');
        defaultLink.rel = 'alternate';
        defaultLink.hreflang = 'x-default';
        defaultLink.href = baseUrl;
        document.head.appendChild(defaultLink);
    },

    // Bind event handlers
    bindEvents: function() {
        // Handle language selection
        this.bindLanguageEvents();

        // Handle page navigation
        window.addEventListener('beforeunload', () => {
            this.saveLanguage(this.currentLanguage);
        });

        // Handle dynamic content updates
        this.observeContentChanges();
    },

    // Bind language selection events
    bindLanguageEvents: function() {
        // Desktop language options
        document.querySelectorAll('.yitp-language-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const langCode = e.currentTarget.dataset.lang;
                this.translateTo(langCode);

                // Close dropdown after selection
                const dropdown = document.querySelector('.yitp-language-selector .dropdown-toggle');
                if (dropdown) {
                    // Try Bootstrap 5 first, then Bootstrap 4, then jQuery
                    if (window.bootstrap && bootstrap.Dropdown) {
                        const bsDropdown = bootstrap.Dropdown.getInstance(dropdown);
                        if (bsDropdown) bsDropdown.hide();
                    } else if (window.$ && $.fn.dropdown) {
                        $(dropdown).dropdown('hide');
                    } else {
                        // Manual close
                        dropdown.setAttribute('aria-expanded', 'false');
                        const menu = dropdown.nextElementSibling;
                        if (menu) menu.classList.remove('show');
                    }
                }
            });
        });

        // Mobile language options
        document.querySelectorAll('.mobile__language-option').forEach(option => {
            option.addEventListener('click', (e) => {
                e.preventDefault();
                const langCode = e.currentTarget.dataset.lang;
                this.translateTo(langCode);

                // Close mobile menu after selection
                const sidebarToggle = document.getElementById('sidebar-toggle');
                if (sidebarToggle) {
                    sidebarToggle.click();
                }
            });
        });
    },

    // Observe content changes for dynamic translation
    observeContentChanges: function() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    // Re-apply translation to new content if needed
                    if (this.currentLanguage !== 'en') {
                        setTimeout(() => {
                            this.triggerGoogleTranslate(this.currentLanguage);
                        }, 100);
                    }
                }
            });
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    },

    // Get current language
    getCurrentLanguage: function() {
        return this.currentLanguage;
    },

    // Check if translation is active
    isTranslated: function() {
        return this.currentLanguage !== 'en';
    },

    // Show translation status to user
    showTranslationStatus: function(message, type = 'info') {
        let statusElement = document.getElementById('translation-status');
        if (!statusElement) {
            statusElement = document.createElement('div');
            statusElement.id = 'translation-status';
            statusElement.className = 'translation-status';
            document.body.appendChild(statusElement);
        }

        const statusText = document.getElementById('translation-status-text');
        if (statusText) {
            statusText.textContent = message;
        } else {
            statusElement.innerHTML = `<i class="fas fa-globe"></i> <span id="translation-status-text">${message}</span>`;
        }

        if (type === 'error') {
            statusElement.style.background = 'rgba(220, 53, 69, 0.9)';
        } else {
            statusElement.style.background = 'rgba(255, 93, 21, 0.9)';
        }

        statusElement.classList.add('show');
        statusElement.style.display = 'block';

        // Hide after 3 seconds
        setTimeout(() => {
            statusElement.classList.remove('show');
            setTimeout(() => {
                statusElement.style.display = 'none';
            }, 300);
        }, 3000);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('📄 DOM Content Loaded - Initializing YITP Translation...');

    // Add a small delay to ensure all scripts are loaded
    setTimeout(() => {
        YITPTranslate.init();
    }, 100);
});

// Also try to initialize on window load as fallback
window.addEventListener('load', function() {
    if (!document.querySelector('.yitp-language-selector')) {
        console.log('🔄 Fallback initialization on window load...');
        YITPTranslate.init();
    }
});

// Export for global access
window.YITPTranslate = YITPTranslate;

// Debug function for testing
window.debugTranslation = function() {
    console.log('🐛 Translation Debug Info:');
    console.log('Current Language:', YITPTranslate.currentLanguage);
    console.log('Language Selector:', document.querySelector('.yitp-language-selector'));
    console.log('Google Translate Element:', document.querySelector('#google_translate_element'));
    console.log('Google Translate Combo:', document.querySelector('.goog-te-combo'));
    console.log('Available Languages:', YITPTranslate.languages);
};
