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
    if(display_params != null) {
        if(display_params[1] == 'book') {
            iframe_in_modal(window.TextualiAuthorBase+'/'+display_params[2]);        }
        else if(display_params[1] == 'vid') {
            iframe_in_modal(youtube.replace('ID',display_params[2]));
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
        h = this.href; 
        iframe_in_modal(h);        
    });
    
    $('.vid').click(function() {
        var id = $(this).data('vidid');
        iframe_in_modal(youtube.replace('ID',id));
    });
    
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
    $('#util-buttons > *').click(function() {
        var tarid = '#'+this.id.replace('-trigger','-container'),
            tar = $(tarid);
        $('.utilbox').not(tarid).removeClass('in');
        tar.toggleClass('in');
    });
   
});
