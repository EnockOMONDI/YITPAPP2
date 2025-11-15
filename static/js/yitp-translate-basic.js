/**
 * Fresh Google Translate integration for the YITP navbar language selector.
 * The dropdown remains the same, but the translation logic has been rebuilt
 * from scratch for clarity and reliability.
 */
(function () {
    'use strict';

    const LANGUAGES = {
        en: { name: 'English', flag: '🇬🇧' },
        sw: { name: 'Swahili (Kiswahili)', flag: '🇰🇪' },
        ar: { name: 'Arabic (العربية)', flag: '🇸🇦' },
        af: { name: 'Africana (Afrikaans)', flag: '🇿🇦' },
        fr: { name: 'French (Français)', flag: '🇫🇷' }
    };
    const STORAGE_KEY = 'yitp_language_preference';
    const SCRIPT_URL =
        'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    const CONTAINER_ID = 'yitp-google-translate';
    const WAIT_LIMIT = 80;
    const WAIT_DELAY = 200;

    let currentLanguage = 'en';
    let initialized = false;
    let translateElementReady = false;
    let scriptPromise = null;

    function onReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    }

    function init() {
        if (initialized) {
            return;
        }
        initialized = true;

        ensureHiddenContainer();
        const saved = getStoredLanguage();
        if (saved && LANGUAGES[saved]) {
            currentLanguage = saved;
        }

        updateLanguageSummary();
        bindLanguageEvents();
        loadGoogleScript()
            .then(() => console.info('YITP Translate: Google script loaded'))
            .catch((error) => {
                console.warn('YITP Translate preload warning:', error);
            });

        if (currentLanguage !== 'en') {
            translateTo(currentLanguage);
        }
    }

    function bindLanguageEvents() {
        document.querySelectorAll('.yitp-language-option').forEach((option) => {
            option.addEventListener('click', handleLanguageSelection);
        });
        document.querySelectorAll('.mobile__language-option').forEach((option) => {
            option.addEventListener('click', handleLanguageSelection);
        });
    }

    function handleLanguageSelection(event) {
        event.preventDefault();
        const option = event.currentTarget;
        const langCode = option.getAttribute('data-lang');
        if (!langCode || !LANGUAGES[langCode]) {
            return;
        }

        setLanguage(langCode);
        closeMobileMenuIfNeeded(option);
    }

    function closeMobileMenuIfNeeded(option) {
        if (!option.classList.contains('mobile__language-option')) {
            return;
        }
        const closeBtn = document.getElementById('sidebar__close-btn');
        if (closeBtn) {
            closeBtn.click();
        }
    }

    function setLanguage(langCode) {
        if (!LANGUAGES[langCode]) {
            return;
        }
        if (!initialized) {
            onReady(() => setLanguage(langCode));
            return;
        }

        currentLanguage = langCode;
        storeLanguage(langCode);
        updateLanguageSummary();

        if (langCode === 'en') {
            resetTranslation();
        } else {
            translateTo(langCode);
        }
    }

    function updateLanguageSummary() {
        document.documentElement.setAttribute('lang', currentLanguage);
        const language = LANGUAGES[currentLanguage];
        const flag = document.getElementById('currentLanguageFlag');
        const name = document.getElementById('currentLanguageName');

        if (flag) {
            flag.textContent = language.flag;
        }
        if (name) {
            name.textContent = language.name;
        }

        updateActiveStates('.yitp-language-option');
        updateActiveStates('.mobile__language-option');
    }

    function updateActiveStates(selector) {
        document.querySelectorAll(selector).forEach((option) => {
            const lang = option.getAttribute('data-lang');
            const isActive = lang === currentLanguage;
            option.classList.toggle('active', isActive);
            option.setAttribute('aria-checked', isActive ? 'true' : 'false');
        });
    }

    function translateTo(langCode) {
        ensureCombo(langCode)
            .then((combo) => applyLanguage(combo, langCode))
            .catch((error) => console.error('YITP Translate error:', error));
    }

    function resetTranslation() {
        if (!translateElementReady && !document.querySelector('.goog-te-combo')) {
            return;
        }

        ensureCombo()
            .then((combo) => applyLanguage(combo, ''))
            .catch((error) => console.warn('YITP reset warning:', error));
    }

    function ensureCombo(targetLanguage) {
        const existingCombo = document.querySelector('.goog-te-combo');
        if (existingCombo && (!targetLanguage || hasOption(existingCombo, targetLanguage))) {
            return Promise.resolve(existingCombo);
        }

        return loadGoogleScript()
            .then(() => waitForCombo(targetLanguage))
            .catch((error) => {
                scriptPromise = null;
                throw error;
            });
    }

    function loadGoogleScript() {
        if (window.google && window.google.translate) {
            console.info('YITP Translate: Google library already present');
            createTranslateElement();
            return Promise.resolve();
        }

        if (scriptPromise) {
            return scriptPromise;
        }

        scriptPromise = new Promise((resolve, reject) => {
            window.googleTranslateElementInit = () => {
                console.info('YITP Translate: googleTranslateElementInit fired');
                try {
                    createTranslateElement();
                    resolve();
                } catch (error) {
                    reject(error);
                }
            };

            const script = document.createElement('script');
            script.src = SCRIPT_URL;
            script.async = true;
            script.onerror = () => {
                console.error('YITP Translate: failed to load Google script');
                scriptPromise = null;
                reject(new Error('Failed to load Google Translate'));
            };
            document.head.appendChild(script);
            console.info('YITP Translate: loading Google script');
        });

        return scriptPromise;
    }

    function createTranslateElement() {
        if (translateElementReady || !window.google || !window.google.translate) {
            return;
        }
        const target = document.getElementById(CONTAINER_ID);
        if (!target) {
            return;
        }

        console.info('YITP Translate: creating TranslateElement');
        new window.google.translate.TranslateElement(
            {
                pageLanguage: 'en',
                includedLanguages: Object.keys(LANGUAGES).join(','),
                layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE,
                autoDisplay: false
            },
            CONTAINER_ID
        );
        translateElementReady = true;
        console.info('YITP Translate: TranslateElement ready');
    }

    function waitForCombo(targetLanguage, attempt = 0) {
        const combo = document.querySelector('.goog-te-combo');
        if (combo && (!targetLanguage || hasOption(combo, targetLanguage))) {
            console.info('YITP Translate: combo ready', combo.options.length);
            return Promise.resolve(combo);
        }

        if (attempt >= WAIT_LIMIT) {
            return Promise.reject(new Error('Google Translate dropdown unavailable'));
        }

        return delay(WAIT_DELAY).then(() => waitForCombo(targetLanguage, attempt + 1));
    }

    function hasOption(combo, langCode) {
        const hasOptionValue = Array.from(combo.options).some((option) => option.value === langCode);
        if (!hasOptionValue) {
            console.warn(`YITP Translate: option ${langCode} not yet available`);
        }
        return hasOptionValue;
    }

    function applyLanguage(combo, langCode) {
        if (langCode && !hasOption(combo, langCode)) {
            return waitForCombo(langCode).then((readyCombo) => applyLanguage(readyCombo, langCode));
        }

        combo.value = langCode;
        combo.dispatchEvent(new Event('change', { bubbles: true }));
        return Promise.resolve(combo);
    }

    function ensureHiddenContainer() {
        if (document.getElementById(CONTAINER_ID)) {
            return;
        }

        const placeholder = document.createElement('div');
        placeholder.id = CONTAINER_ID;
        placeholder.setAttribute('aria-hidden', 'true');
        document.body.appendChild(placeholder);
    }

    function storeLanguage(langCode) {
        try {
            window.localStorage.setItem(STORAGE_KEY, langCode);
        } catch (error) {
            console.warn('Unable to store language preference:', error);
        }
    }

    function getStoredLanguage() {
        try {
            return window.localStorage.getItem(STORAGE_KEY);
        } catch (error) {
            return null;
        }
    }

    function delay(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    onReady(init);

    window.YITPTranslate = {
        init,
        languages: LANGUAGES,
        getCurrentLanguage: () => currentLanguage,
        setLanguage: (code) => setLanguage(code),
        reset: () => setLanguage('en')
    };

    window.debugYITPTranslate = () => ({
        initialized,
        currentLanguage,
        translateElementReady,
        scriptPromiseActive: Boolean(scriptPromise),
        comboPresent: Boolean(document.querySelector('.goog-te-combo')),
        storedPreference: getStoredLanguage()
    });
})();
