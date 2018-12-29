if (!window.__PERSIST) {
    // for pre-rendered abstract pages
    require(['jquery'], function ($) {
        window.__PERSIST = function () {
        var $head = $('head').clone(true);
        var $body = $('body').clone(true);
        var toRemove = [
            '#toggle-aff',
            '#toggle-more-authors',
            'div.navbar-collapse',
            '.popover'
        ];
        $('script', $head).remove();
        


        $head.append('<script>window.__PRERENDERED = true;</script>');
        $(toRemove.join(', '), $body).remove();
        $('#authors-and-aff', $body).prepend('<div style="height:20px;"></div>')
        $('.s-nav-container nav>[data-widget-id]>div', $body)
        .not('[data-widget-id~="ShowAbstract"]>div', $body)
        .addClass('s-nav-inactive')
        .attr('href', '#');
        $('form[name="main-query"] input', $body).addClass('disabled');
        $('form[name="main-query"] button[type="submit"]>i', $body).addClass('disabled fa-spin fa-spinner');
        var $dom = $('<html></html>').append($head).append($body);
        
        $('base', $head).remove();
        $head.prepend($('<base href="//">'));

        return $dom[0].outerHTML;
        }
    });
}
