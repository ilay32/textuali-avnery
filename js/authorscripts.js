var minuses = {
    'main' : 50,
    '#auth-mod': 30
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

function bind_vid_adjustment() {
    $('#auth-mod').on('shown.bs.modal',function() {
        var d = $(this).find('.modal-dialog.modal-lg');
        d.width(d.height() * 1.5);
    });
}

function share(url) {
    $('#share-modal').click(function() {
        $('#share-input').fadeIn(300).val(url).mouseleave(function() {
            $(this).delay(3000).fadeOut(400);
        });
    });
}

function filename2pagenum(name) {
    m = name.match(/^([a-z]\d{3}p)(\d{3})$/);
    return m[2];
}

function process_search_results(results) {
    var htm = '<h5>'+window.TextualiStrings.search_results+' "'+results.q+'"</h5>';
    if(results.status == 'success') {
        if(results.matches.length > 0) {
            htm += '<ul class="toc-list">';
            var m = results.matches;
            for(var res in m) {
                htm += '<li><span class="search-results-pagenum">\' ' + filename2pagenum(m[res].id)+'</span>';
                htm += '<a class="toc-link search-result" href="#page"';
                htm += '?q='+results.q+'">'+m[res].match+'</a></li>';
            }
            htm += '</ul>';
        }
        else {
            htm = 'sorry, no matches found';
        } 
   }
   else if(results.status == 'fail') {
       htm = results.error;
   }
   else {
       htm = 'unknown error';
   }
   return htm;
} 

$(document).ready(function() {
    var youtube = "http://www.youtube.com/embed/ID?autoplay=1";
    var display_params  = location.search.match(/^\?(vid|book)=(.*)$/);
    $('#isotope').isotope({
        isOriginLeft: $('body').css('direction') == 'rtl' ? false : true,
        itemSelector: window.isoIt,
        layoutMode: 'masonry'
    });
    $('.langswitch').click(function() {
        var l = $(this).data('langcode'),
            loc = window.location;
        if (loc.pathname == "/") {
            h = l;
        }
        else if (/^\/[^\/]+html$/.test(loc.pathname)) {
            h = l+loc.pathname;
        }
        else {
            h = loc.href.replace(/\/[a-z]{2}(?=((\/.*\.[a-z]{2,4})|\/)$)/,'/'+l);
        }
        window.location.assign(h);
    });

    $('#auth-mod').on('hide.bs.modal',function() {
        $(this).find('.modal-body').empty();
        $(this).find('.modal-dialog').width('');
    });
    $('[data-href]').click(function() {
        var h = $(this).data('href'),
            o = $(this).data('open');
        switch(o) {
            case 'blank':
                window.open(h, '_blank');
            break;
            case 'modal':
                iframe_in_modal(h);
            break;
            default:
            case undefined:
                window.location.assign(h);
        }
    });
    if(display_params != null) {
        if(display_params[1] == 'book') {
            iframe_in_modal(window.TextualiAuthorBase+'/'+display_params[2]);        }
        else if(display_params[1] == 'vid') {
            iframe_in_modal(youtube.replace('ID',display_params[2]));
            bind_vid_adjustment()
        }
    }
    $(window).load(function() {
        frame_height('main');
    });     
    
    $(window).resize(function() {
        $('iframe').attr('src',this.src);
        frame_height('main');
    });
    
    $('.flip-modal-trigger').click(function(c) {
        c.preventDefault();
        h = $(this).attr('href'); 
        iframe_in_modal(h);        
        if('string' == typeof($(this).data('book')) ) {
            share(window.TextualiAuthorBase+'/?book='+$(this).data('book'));
        }
        if('string' == typeof($(this).data('vid'))) {
            share(window.TextualiAuthorBase+'/?vid='+$(this).data('vid'));
            bind_vid_adjustment()
        }
    });
    
    /*$('.vid').click(function() {
        var id = $(this).data('vidid');
        iframe_in_modal(youtube.replace('ID',id));
    });*/
    
    $('#searchform').submit(function() {
        var query = $(this).serialize();
        $.ajax({
            url: window.TextualiSearchBase+'&'+query,
            DataType: 'json'
        }).done(function(results) {
            $('#auth-mod').modal('show').find('.modal-body').html(process_search_results(results));
        }).fail(function(err) {
            alert(err);
        });
       return false; 
    });
    $('.util-button').click(function() {
        var tarid = '#'+this.id.replace('-trigger','-container'),
            tar = $(tarid);
        $('.utilbox').not(tarid).removeClass('in');
        tar.toggleClass('in');
    });
   
});
