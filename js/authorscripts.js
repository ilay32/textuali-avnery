var minuses = {
    'main' : 50,
    '#auth-mod': 150
}
function frame_height(elem) {
    var height = $(window).height() - minuses[elem];
    $(elem).each(function() {
        $(this).find('iframe').height(Math.max(height,500));
    });
}

function iframe_in_modal(url) {
    $('#auth-mod').modal('show').find('.modal-body').html('<iframe></iframe>');
    frame_height('#auth-mod');
    setTimeout(function() {
        $('#auth-mod').find('iframe').attr('src',url);
    },100);
}



$(document).ready(function() {
    $(window).load(function() {
        frame_height('main');
    });     
    $(window).resize(function() {
        $('iframe').attr('src',this.src);
        frame_height('main');
    });
    $('.flip-modal-trigger').click(function(c) {
        c.preventDefault();
        h = this.href; 
        iframe_in_modal(h);        
    });

});
