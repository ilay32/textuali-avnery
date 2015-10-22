var first_flipto = location.href.match(/(\/#page\/)(\d*)$/);
var srcs = "{{srcs}}";
{{#generic_srcs}}
if(location.host != "textuali.com") {
    srcs = "{{generic_srcs}}"; 
    if (self == self.top) {
        location.assign("{{generic_base}}?book={{bookdir}}");
    }
}
{{/generic_srcs}}


function page_files(page) {
    if(page > {{pages}}  || page < 1) {
        return false    
    }
    var filename = {{page_list}}[page-1], 
        hard = /[a-z]/.test(filename.slice(-1)) && (page >= {{page_list}}.length - 1 || page <= 2);
    return {
        jpg : srcs+'/jpg/'+ filename + '.jpg', 
        html : srcs+'/html/' + filename + '.htm', 
        hard : hard
    };
}

function unenlarge_flip() {
    $('#enlarge').removeClass('btn-danger').addClass('btn-default');
    $('.flipbook').turn('zoom', 1).css('{{side}}','').animate({'{{oposide}}': '-20px', top: '0'},500).turn('disable',false).draggable("destroy");
    $('.textuali-container').width($('.flipbook').width() + 20);
}

function enlarge_flip() {
    $('#enlarge').addClass('btn-danger').removeClass('btn-default');
    var dist_from_center = $('.flipbook').offset().left - $('.flipbook').width()/2;
    var dist_from_middle = $('.flipbook').offset().top - $('.flipbook').height()/2;
    
    $('.flipbook').turn('zoom', 2);            
    $('.flipbook').turn('disable',true).draggable();
}

function flip2phis(num) {
    var ret = -1;
    if(num > 0 && num <= {{phispage_count}}) {
        ret = parseInt(num) + parseInt({{start_offset}});
    }
    /*var ret = -1;
    var zeros = '00';
    if(num > 9 && num < 99) {
        zeros = '0';
    }
    if(num > 99) {
        zeros = '';
    }
    var filebase = {{page_list}}[0].match(/^\w\d{3}p/);
    var inlist = $.inArray(filebase+zeros+num,{{phispages}});
    if(inlist > 0) {
        ret =  inlist + 1;
    }*/
    return ret;
}

function loadPage(page, pageElement) {
    var pf = page_files(page);
    if (!pf) {
        return;
    }
    pageElement.css('background-image','url('+pf.jpg+')');
    foundHtml = false;
    if('{{has_texts}}' == 'True' ) {			
        $.ajax({url: pf.html}).done(function(pageHtml) {
            if('{{whole_docs}}'=='True') {
                pageHtml = $(pageHtml).get(7);
            }
            if(!$.isEmptyObject(pageHtml)) {				
                $(pageHtml).find('img').each(function() {
                    var sr = this.src;
                    sr = sr.replace('{{bookdir}}', '{{bookdir}}/html');
                    $(this).attr('src',sr);
                });
                hidden = $('.flipbook').data('displayMode') == 'scan' ? ' hidden' : '';
                pageElement.find('.spine-gradient').append($('<div class="page-html'+hidden+'"/>').html(pageHtml));
            }
            /* else {
                pageElement.find('.page-html').remove();
            } */  
       }).fail(function() {
           pageElement.find('.page-html').remove();    
       });
    }
}

function addPage(page, book) {
    var id, pages = $('.flipbook').turn('pages'), 
        pageElement = $('<div/>').html('<div class="spine-gradient"/>');
    if(page > 0 && page_files(page).hard) {
        pageElement.addClass('hard');
    }
    if (book.turn('addPage', pageElement, page))  {
        loadPage(page, pageElement);
    }
}

function highlight_search(page,query) {
    var target = $('.p'+page).find('.page-html');
    if(target.length > 0) {
        var rawhtml = target.html();
        var newhtml = rawhtml.replace(query,'<strong class="in-page-highlight whole">'+query+'</strong>');
        var sq = query.split(" ");
        for(w in sq) {
            newhtml = newhtml.replace(sq[w], '<strong class="in-page-highlight">'+sq[w]+'</strong>');
        }
        target.html(newhtml);
    }
    return 1;
} 

function filename2pagenum(filename) {
    var ans="";
    var n = filename.match(/\d+p0*([1-9]\d*)$/);
    if(n != null && n.length > 1) {
        ans= n[1];
    }
    return ans;
} 

function get_toc(pagenum) {
    $.ajax({url: page_files(pagenum).html}).done(function(pageHtml) {
        var toc_list = $('<ul class="toc-list dropdown-menu"/>');
        $(pageHtml).find('.toc-list li').each(function() {
            toc_list.append(this);
        });
        $('#totoc').after(toc_list);
    });
}

function process_search_results(results) {
    var htm = '<h3>{{string_translations.search_results}} "'+results.q+'"</h3>';
    if(results.status == 'success') {
        if(results.matches.length > 0) {
            htm += '<ul class="toc-list">';
            var m = results.matches;
            for(var res in m) {
                htm += '<li><span class="search-results-pagenum">עמ\' ' + filename2pagenum(m[res].id)+'</span>';
                htm += '<a class="toc-link search-result" href="#page/'+($.inArray(m[res].id,{{page_list}}) + 1);
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

function toggle_html(btn) {
    $(btn).parent().parent().find('iframe').each(function() {
        $(this).css('height',($(this).parent().parent().height()-80)+'px');
        $(this).parent().toggleClass('hidden');
    });
}

function show_html(pages) {
    var tar; 
    for (i in pages) {
        tar = find_html_div(pages[i]).add('.page-html').filter(function() {
            return $(this).html() != "";
        });
        tar.each(function() {
            $(this).closest('.page').css({'overflow-y': 'auto', 'background-size': '0 0'});
            $(this).removeClass('hidden');
            var l = $(this).find('.pagelive').height() + 20,
                t = $(this).height(),
                p = $(this).closest('.page').height(),
                h = Math.max(t,p,l);
            //$(this).removeClass('hidden').find('iframe').css('height',($(this).closest('.page-wrapper').height()-80)+'px');
            $(this).height(h); 
            if(l < h) {
                $(this).find('.pagelive').height(h);
            }
        });
    }
    $('#totoc').attr('data-toggle', '').removeClass('jpg-toc');
}

function hide_html(pages) {
    for (i in pages) {
        find_html_div(pages[i]).add('.page-html').addClass('hidden').closest('.page').css({
            'overflow-y' : 'hidden',
            'background-size' : '100% 100%'
        });
    }
    $('#totoc').attr('data-toggle', 'dropdown').addClass('jpg-toc');
}

function find_html_div(n) {
    return $('.page.p'+n).find('.page-html');
}

function toggleHtml(pages) {
    var displayMode = $('.flipbook').data('displayMode');
    if(displayMode == 'scan') {
        hide_html(pages);
    }
    else if(displayMode == 'html') {
        show_html(pages);
    }
}

function loadApp() {
    //$('.largenav').addClass('disabled');
    var  book_height = $(window).height() - $('#buttons-row').outerHeight() - 20,
        screen_ratio = $(window).width()/$(window).height(),
        book_width,
        openbook_ratio = parseFloat({{openbook_ratio}});
    if(typeof(openbook_ratio) != "number" || openbook_ratio == 0) {
        im = $('<img src="jpg/{{frontjpg}}"/>').get(0);
        openbook_ratio = (2*im.naturalWidth)/im.naturalHeight;
    }
    
    if(Math.abs(1 - openbook_ratio/screen_ratio) > Math.abs(1 - screen_ratio/openbook_ratio)) {
        openbook_ratio = 1/openbook_ratio;
        book_width = Math.floor($(window).width() * 0.8);
        book_height = Math.floor(book_width*openbook_ratio);
    }   
    else {
        book_width=Math.floor(book_height*openbook_ratio);
    }
    var clearbuttons = $('#side-buttons').offset().top+$('#side-buttons').height() - 20;
    //var screen_marge = Math.floor(($(window).width() - book_width)/2);
    //var largenav_offset = (screen_marge - 85)+'px';
    $('.textuali-container').width(book_width + 20);
    //$('.flb-next.largenav').css('{{oposide}}', largenav_offset);
    //$('.flb-prev.largenav').css('{{side}}',largenav_offset);
    $('.largenav').css('top',Math.max(book_height/2,clearbuttons)+'px');
    //$('.largenav').removeClass('hidden');
    $('.flipbook').turn({
        width:book_width,
        height:book_height,
        elevation: 50,
        duration:2000,
        pages: {{pages}},
        direction: '{{flipdirection}}',
        // Enable gradients
        gradients: true,
        // Auto center this flipbook
        autoCenter: true,
        when: {
            'turned': function(event, page, pages) {
                if(Hash.fragment() != "" || page > 2 ) {
                    var searchq = Hash.fragment().match(/\?q=(.*)$/);
                    if(searchq != null && searchq.length == 2) {
                        show_html(pages);
                        for(var p in pages) {
                            highlight_search(pages[p],decodeURIComponent(searchq[1])),$('.p'+page);
                        }
                    }
                    Hash.go('page/'+page);
                } 
                //$('.flb-next, .flb-prev').show();
                $('.largenav').removeClass('disabled');
                if(page == $(this).turn('pages')) {
                    $('.largenav.next').addClass('disabled');
                }
                if(page == 1) {
                    $('.largenav.prev').addClass('disabled');
                }
            },
            'start' : function(event,pageObject,corner) {
                toggleHtml(pageObject.turn.turn('view'));
            }, 
            'missing': function (e, pages) { 
                for (var i = 0; i < pages.length; i++) {
                    addPage(pages[i], $(this));
                }					
            },
            'turning' : function(event, page, view) {
                $('.popover').modalPopover('hide');
                //$('#search-results').removeClass('in');
                if($('#next-prev-toc').hasClass('open')) {
                    $('.toc-list').dropdown('toggle');
                }

            }
        }                 
    });
    
    //loadPage(1,$('.flipbook').find('div').eq(0));
    
    // URIs
    Hash.on('^page\/([0-9]*)\/\?(.*)$', {
        yep: function(path, parts) {
            var page = parts[1];
            if (page!==undefined) {
                if ($('.flipbook').turn('is'))
                    $('.flipbook').turn('page', page);
            }
        },
        nop: function(path) {
           if ($('.flipbook').turn('is'))
               $('.flipbook').turn('page', 2);
        }
    });

    // Arrows
    $(document).keydown(function(e){
        var previous = 37, next = 39;
        switch (e.keyCode) {
            case previous:
                $('.flipbook').turn('previous');
            break;
            case next:
                $('.flipbook').turn('next');
            break;
        }
    });
    
    if(first_flipto != null && first_flipto[2] !== "") {
        Hash.go('page/'+flip2phis(first_flipto[2]));
    }

    
} //loadApp

$(window).resize(function() {
    var rememberme = {
        page:  $('.flipbook').turn('page'), 
        displaymode : $('.flipbook').data('displayMode')
    };
    $('.flipbook').turn('destroy');
    loadApp();
    var book = $('.flipbook');
    book.data('displayMode',rememberme.displaymode);
    Hash.go('page/'+rememberme.page);
    book.turn('page',rememberme.page);
    /*for(p in book.turn('view')) {
        addPage(p,book);
    }*/
    toggleHtml(); 
});

$(document).ready(function() {
    $('.flipbook').data('displayMode', 'scan');
    $('body').mousedown(function(c) {
        if($(this).hasClass('modal-open')) {
            var exclude1 = $('#gotopage-trigger').add($('#gotopage-popover').find('*').andSelf());
            var exclude2 = $('#search-trigger').add($('#search-popover').find('*').andSelf());
            if(!exclude1.is(c.target)) {
                $('#gotopage-popover').modalPopover('hide');
            }
            if(!exclude2.is(c.target)) {
                $('#search-popover').modalPopover('hide');
                //$('#search-results').removeClass('in');

           }
        }
    }); 
    if(parseInt({{toc}}) > 0) {
        get_toc({{toc}});
    }
    $('.page_end').click(function(c) {
        c.preventDefault();
    }); 
   
    $('#download-pdf').click(function() {
        var pdf = $(this).attr('href'),
            h = location.href;
        if(h.indexOf('#') > 0) {
            h = h.substr(0,h.indexOf('#'));
        }
        if(undefined != pdf) {
            window.open(h+"{{authdir}}-{{bookdir}}-"+pdf, "{{book_nicename}} PDF", "width=600, height=400" );
        }
    });

    $('[data-popper]').click(function() {
        $($(this).data('popper')).modalPopover('toggle');
    });

    $('.popover').each(function() {
        $(this).modalPopover({
            target: $(this).data('trigger'),
            placement: 'bottom'
        });
    });

    $('#gotopage-form').submit(function() {
        var v = $(this).find('input').val();
        phis = flip2phis(v);
        if(phis > 0) {
            $('.flipbook').turn('page', phis);
        }
        else {
            $(this).siblings('.error-message').fadeIn(300).delay(4000).fadeOut(300);
        }
        return false;
    });


    $('#search-form').submit(function() {
        $('#search-results').removeClass('in');
        var query = $(this).serialize();
        $.ajax({
            url: 'http://textuali.com/search/websearch.py/?pretty=1&f={{authdir}}-{{bookdir}}&'+query,
            DataType: 'json'
        }).done(function(results) {
            $('#search-results').html(process_search_results(results)).addClass('in');
        }).fail(function(err) {
           $(this).siblings('.error-message').fadeIn(300).delay(4000).fadeOut(300);
       });
       return false; 
    });

    $('#enlarge').click(function(){
        if($(this).hasClass('btn-danger')) {
            unenlarge_flip();
        }
        else {
            enlarge_flip();
       }
    });
    $('[class*=flb]').click(function() {
        if($('#enlarge').hasClass('btn-danger')) {
            unenlarge_flip();
        }
     });        

    $('.flb-next').click(function() {
        $('.flipbook').turn('next');
    });

    $('.flb-prev').click(function() {
        $('.flipbook').turn('previous');
    });
    
    $('.flb-seek').click(function() {
        seek = $(this).data('seek');
        if(/^\d+$/.test(seek)) {
            $('.flipbook').turn('page',seek);
        }
    });
    $('.mode-toggle').click(function() {
        $('.mode-toggle').not(this).removeClass('on');
        var d=$('.flipbook').data();
        if(this.id == 'showhtmls' && d.displayMode == 'scan')  {
            d.displayMode = 'html';
            $('#showhtmls').addClass('on');
            if($('#totoc').hasClass('open')) {
                $('.toc-list').dropdown('toggle');
                $('#totoc').removeClass('open');
            } 
       }
       else if(this.id == 'showscans' && d.displayMode == 'html') {
            d.displayMode = 'scan';
            $('#showscans').addClass('on');
       }
       toggleHtml($('.flipbook').turn('view'));
    });

    {{#toc}}
    $('#totoc').click(function() {
        if(!$(this).hasClass('jpg-toc')) {  
            //show_html([{{toc}},{{toc}} -1, {{toc}} + 1]);
            $('.flipbook').turn('page',{{toc}});
        }
        else {
            $(this).toggleClass('open');
        }
    });
    
    $('#totoc').on('shown.bs.dropdown',function() {
        $(this).next('.toc-list').css('max-height',$('body').height()*0.85+'px');
    });
    {{/toc}}

});

// Load the HTML4 version if there's not CSS transform
$(function() {
    yepnope({
        test : Modernizr.csstransforms,
        yep: ['{{front.domain}}vendor/turnjs4/lib/turn.js'],
        nope: ['{{front.domain}}vendor/turnjs4/lib/turn.html4.min.js'],
        complete: loadApp
    });
});     

