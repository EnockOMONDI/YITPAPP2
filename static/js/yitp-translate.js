(function() {
    var SUPPORTED = ['en','sw','ar','af','fr'];
    var scriptLoaded = false;
    var pendingLang = null;

    function injectGoogle() {
        if (scriptLoaded) return;
        scriptLoaded = true;
        var s = document.createElement('script');
        s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        document.body.appendChild(s);
    }

    function applyLang(lang) {
        var combo = document.querySelector('.goog-te-combo');
        if (!combo) {
            setTimeout(function() { applyLang(lang); }, 300);
            return;
        }
        combo.value = lang;
        combo.dispatchEvent(new Event('change'));
    }

    window.googleTranslateElementInit = function() {
        new google.translate.TranslateElement({
            pageLanguage: 'en',
            includedLanguages: SUPPORTED.join(','),
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element');

        if (pendingLang) {
            applyLang(pendingLang);
            pendingLang = null;
        }
    };

    function setLanguage(lang) {
        if (SUPPORTED.indexOf(lang) === -1) lang = 'en';
        pendingLang = lang;
        injectGoogle();
        applyLang(lang);
    }

    function bindButtons() {
        var buttons = document.querySelectorAll('.yitp-language-option, .yitp-mobile-lang [data-lang]');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var lang = btn.getAttribute('data-lang');
                setLanguage(lang);
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function() {
        injectGoogle();
        bindButtons();
    });
})();
