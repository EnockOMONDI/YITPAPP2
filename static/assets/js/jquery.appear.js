/*
 * jQuery appear plugin
 * Simple stub to prevent 404 errors
 */
(function($) {
    $.fn.appear = function(fn, options) {
        var settings = $.extend({
            data: undefined,
            one: true,
            accX: 0,
            accY: 0
        }, options);

        return this.each(function() {
            var t = $(this);
            
            // Simple fallback - just trigger immediately
            if ($.isFunction(fn)) {
                fn.call(this, settings.data);
            }
        });
    };
})(jQuery);
