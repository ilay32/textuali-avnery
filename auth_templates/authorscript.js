var minuses = {
    'main' : 85,
    '#auth-mod': 30
}
var authbase = '{{authtexts}}';
var slideshows = '{{destination_domain}}/{{lang}}/slideshows';
//var search_template = "https://www.googleapis.com/customsearch/v1?GOOGLESEARCHQUERY&cx={{google_search}}&fields=items%searchInformation%2FtotalResults%2Curl&key={{gapikey}}";
var search_template = "https://www.googleapis.com/customsearch/v1?GOOGLESEARCHQUERY&cx={{google_search}}&fields=items%2Cqueries%2CsearchInformation%2FtotalResults%2Curl&key={{gapikey}}";

var pdf_embed_src = "https://docs.google.com/viewer?embedded=true&url=DOCURL";
var vid_template = "http://www.youtube.com/embed/VIDEOID?autoplay=1";

//var trickparse = document.createElement('a');
var pageresult = /\/texts\/[\w_\-]+\/\w\d{3}\/html\/(\w\d+p\d+\w?)\.html?$/
function padZeroes(i) {
    var bar = ""+i;
    while(bar.length < 3) {
        bar = "0"+bar;
   }
   return bar;
}  
   

function TextualiJpgsLoader(book,pages) {
    this.lastloaded = 0;
    this.hasmore = true;
    this.book = book;
    this.pages = parseInt(pages);
    
    this.destroy = function() {
        loader  = this;
        loader.hasmore = false;
        p = $('#phone-scroll-boook').detach();
        $('main#content').after(p);
    }
             
    this.loadmore = function() {
        var i = 0;
        var loader = this;
        while(i++ < 5 && loader.hasmore) {
           loader.loadNext() 
        }
    }; 
    
                
    this.loadNext = function() {
        var loader = this;
        var loading = new Image();
        loading.src = loader.next();
        loading.onload = function() {
            $('#phone-scroll-book').append(this);
            if(loader.hasmore && loader.lastloaded < loader.pages) {
                loader.loadNext();
            } 
        }
        loading.onerror = function() {
            loader.hasmore = false;
        } 
    }
        
    this.next = function() {
        this.lastloaded++;
        var ret = authbase;
        ret += '/'+this.book+'/jpg/'+this.book;
        ret += 'p'+padZeroes(this.lastloaded)+'.jpg';
        return ret;
    }; 

    this.bind_scroll = function() {
        var h = $('#phone-scroll-book  > img').eq(0).get(0).height;
        $(window).scroll(function() {
            console.log($(this).scrollTop());
            if ($(this).scrollTop() > (tjloader.lastloaded - 2) * h && tjloader.hasmore) {
                tjloader.loadmore();
            }
            else {
                console.log($(this).scrollTop(), tjloader, h);
            }
        });  
    }; 

} 

function frame_height(elem) {
    var height = $(window).height() - minuses[elem];
    $(elem).each(function() {
        $(this).find('iframe').height(Math.max(height,300));
    });
}


function iframe_in_modal(url) {
    $('#auth-mod').modal('show').find('.modal-body').html('<iframe></iframe>');
    frame_height('#auth-mod');
    setTimeout(function() {
        $('#auth-mod').find('iframe').attr('src',url);
    },100);
}

function video_in_modal(v) {
    var h = vid_template.replace('VIDEOID',v);
    iframe_in_modal(h);
    share('#auth-mod', window.location.href.replace(window.location.search, '')+'?vid='+v);
    bind_vid_adjustment();
}

function slideshow_in_modal(id) {
    var t = location.origin+location.pathname.replace(/(\/[a-z_\-0-9]+\.html)$/ , "/slideshows/"+id+".htm");
    $.ajax({
        url: t,
        dataType: 'HTML'
    }).done( function(slideshow) { 
        slideshow = $(slideshow);
        if (slideshow.length == 1) {
            slideshow.find('.loader').each(function() {
                var loader = $(this);
                var slide = new Image();
                slide.src = loader.data('src');
                slide.alt = loader.data('alt'); 
                slide.setAttribute("class", "slide");
                slide.onload = function() {
                    loader.hide().after(this);
                } 
            });
            //$(this).after(attr('src', $(this).data('src'));
            $('#auth-mod').modal('show').find('.modal-body').html(slideshow);
            slideshow.height($(window).height()*0.9).fadeIn(200);
            share('#auth-mod',window.location.href.replace(window.location.search, '')+'?slideshow='+id);

        
    }
    });
}


function bind_vid_adjustment() {
    $('#auth-mod').on('shown.bs.modal',function() {
        var d = $(this).find('.modal-dialog.modal-lg');
        d.width(d.height() * 1.5);
    });
}

function share(modalid,url) {
    var s = $(modalid).find('input.share');
    $(modalid).find('.share-modal').bind('click', function() {
        s.val(url).closest('.share-input-wrap').toggleClass('in');
    });
}

function filename2pagenum(name) {
    m = name.match(/^([a-z]\d{3}p)(\d{3})$/);
    return m[2];
}

function process_fts_search_results(results) {
    //var htm = '<h5>{{string_translations.search_results}} "'+results.q+'"</h5>';
    var htm = '<div id="search-results"><h3>{{string_translations.search_results}} "'+results.q+'"</h3>';
    if(results.status == 'success') {
        if(results.matches.length > 0) {
            htm += '<ul class="search-results">';
            var m = results.matches;
            for(var res in m) {
                var urls = fileurls(m[res].id);
                htm += '<li class="search-result">';
                htm += '<a href="'+urls.fliplink+'">'+m[res].book_name+' '+urls.page+'</a>';
                htm += '<p>'+m[res].match+'</p></li>';
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

function fileurls(file) {
    var m = file.match(/^([a-z]\d+)p(\d+[a-z]?)$/);
    if(!m) {
        return false;
    }
    var fliplink = '?book='+m[1], p="";
    if(/^\d+$/.test(m[2]) ) {
        p = parseInt(m[2]);
        fliplink += "/#page/"+(p + 1);
    }
    return {
        "fliplink" : fliplink,
        "page" : p 
    };
}


function identify_book_page(url) {
    var ret = false;
    var m = url.match(pageresult);
    if (m!=null && m.length == 2) {
        ret = fileurls(m[1]);
    }
    return ret;
}

function process_google_search_results(results) {
    var r = results.queries.request[0];
    var htm = '<div id="search-results"><h3>{{string_translations.search_results}} "'+r.searchTerms+'"</h3>';
    if(r.totalResults > 0) {
        htm += '<ul class="search-results">';
        $(results.items).each(function(index,res) {
            htm += '<li class="search-result">';
            var u = identify_book_page(res.link);
            var l = typeof(u) == 'object' ? u.fliplink : res.link;
            //l += '&q='+r.searchTerms.replace(/\s+/,"+");
            htm += '<a href="'+l+'">'+res.title+'</a>';
            htm += '<p>'+res.htmlSnippet+'</p></li>';
        });
        htm += '</ul></div>';
    }
    else {
        htm += 'sorry, no matches found</div>';
    } 
    return htm;
}

function highlight_menu(ul) {
    ul.find('li').each(function() {
        if($('body').hasClass(this.id)) {
            $(this).children('a').eq(0).addClass('active');
            $(this).closest('.dropdown').find('.dropdown-toggle').addClass('active');
        }
        if($(this).hasClass('dropdown')) {
            highlight_menu($(this).find('.dropdown-menu'));
        }
   });
}

$(document).ready(function() {
    $('li[data-file]').click(function() {
        var d = $(this).data('file'),
            k = $(this).closest('.panel').data('knesset'),
            u = authbase+'/site/img/protocols/'+k+'/'+d+'.pdf';
        iframe_in_modal(u);
    });
    var display_params  = location.search.match(/^\?(vid|book|slideshow)=(.*)$/);
    //$('.carousel.slide').hide();
    highlight_menu($('#primary-navigation > .nav'));
    $('.external iframe').load(function() {
        $(this).prev('.loader').hide();
        $('#iframe-wrap').css('height','auto');
    });
    //$('image[usemap]').rwdImageMaps(); 
    $(window).load(function() {
        $('#isotope').isotope({
            isOriginLeft: !('{{dir}}' == 'rtl'),
            itemSelector: window.isoIt,
            layoutMode: 'masonry'
        });
        $('#isotope').addClass('in');
    });
    $('.langswitch').click(function() {
        var l = $(this).data('langcode'),
            loc = window.location;
        if (loc.pathname == "/") {
            h = l;
        }
        else if (/^\/[a-z\/]*\.html$/.test(loc.href)) {
            h = l+loc.pathname;
        }
        else {
            var cur = loc.href.replace(loc.search,"");
            if (display_params != null && display_params[1] == 'book') {
                cur = cur.replace(loc.hash,"");
            }
            h = cur.replace(/\/[a-z]{2}(?=((\/.*\.[a-z]{2,4})|\/)(#.*)?$)/,'/'+l);
        }
        window.location.assign(h);
    });
    $('.doc-wrap').click(function() {
        var c = $(this).find('.document-image').clone().show();
        $('#auth-mod').find('.share-modal').hide().end().find('.modal-body').html(c).end().modal('show');
        $('#auth-mod .modal-dialog').addClass('multidoc');
    });
    $('.modal-content').click(function(c) {
        if (!$(c.target).is('.share-modal')) {
            $(this).find('input.share').removeClass('in');
        }
    });
    $('#auth-mod').on('hide.bs.modal',function() {
        $(this).find('.modal-body').empty();
        $(this).find('.modal-dialog').width('').removeClass('multidoc');
        $(this).find('.share-modal').show().unbind('click').next('.share-input-wrap').removeClass('in');
       
    });

    $('.share-input-wrap button').click(function() {
        $(this).parent().removeClass('in');
    });
    /*$('iframe').load(function() {
        console.log(parent.document.getElementById('content'));
    });*/
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
            case 'social' :
                window.open(h,"", "width=600, height=400");  
            break;
            default:
            case undefined:
                window.location.assign(h);
        }
    });
    if(display_params != null) {
        if(display_params[1] == 'book') {
            var u = display_params[2];
            var d = decodeURIComponent(window.location.hash);
            if (/#page\/\d+(&q=.+)?$/.test(d)){
                u += d.replace('&','?');
            }
            iframe_in_modal(authbase+'/'+u);        
        }
        else if(display_params[1] == 'vid') {
            video_in_modal(display_params[2]);
        }
        else if(display_params[1] == 'slideshow') {
            slideshow_in_modal(display_params[2])
        }
    }
    $(window).load(function() {
        frame_height('main');
    });     
    
    $(window).resize(function() {
        $('iframe').attr('src',this.src);
        frame_height('main');
    });
    
    $('#close-phone-scroll').click(function() {
        tjloader.destroy();
        $('#phone-scroll-book').fadeOut(200);
        $('main#content,footer').fadeIn(200);
    }); 
      
   $(window).scroll(function(){
        if ($(this).scrollTop() > 100) {
            $('#scrollup').fadeIn();
        } else {
            $('#scrollup').fadeOut();
        }
    });
    $('#scrollup').click(function(){
        $("html, body").animate({ scrollTop: 0 }, 600);
        return false;
    });
    
    $('.vid').click(function(c) {
        if(!$(c.target).is('a')) {
            video_in_modal($(this).data('vid'));
        }
    });

    $('.flip-modal-trigger').click(function(c) {
        c.preventDefault();
        h = $(this).attr('href'); 
        if($(window).width() <= 768 ) {
            if(typeof(tjloader) == 'object') {
                tjloader.destroy(); 
            }
            tjloader = new TextualiJpgsLoader($(this).data('book'), $(this).data('pages'));
            $('main#content,footer').fadeOut(200);
            $('#phone-scroll-book').fadeIn(200).find('> img').detach();
            tjloader.loadmore();
       }
        else {
            iframe_in_modal(h);
            share('#auth-mod', window.location.href.replace(window.location.search, '')+'?book='+$(this).data('book'));
        }
    });
    
    $('.slideshow-modal').click(function(c) {
        if(!$(c.target).is('a')) {
            s = $(this).data('slideshow');
            slideshow_in_modal(s);
        }
    });
    
        
    $('#fsearch').submit(function() {
        var query = $(this).serialize();
        $.ajax({
            url: location.origin+'/search/websearch.py/?pretty=1&f={{auth}}&'+query,
            DataType: 'json'
        }).done(function(results) {
            $('#auth-mod').modal('show').find('.modal-body').html(process_fts_search_results(results));
        }).fail(function(err) {
            alert(err);
        });
       return false; 
    }); 
    
    $('#gsearch').submit(function() {
        var query = $(this).serialize();
        $.ajax({
            url : search_template.replace('GOOGLESEARCHQUERY',query),            
            DataType: 'json'
        }).done(function(res) {
            $('#auth-mod').modal('show').find('.modal-body').html(process_google_search_results(res)).end().find('.share-modal').hide();
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
