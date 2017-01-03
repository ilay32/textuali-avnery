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
   
function YearDocs() {
    this.years =  Object.keys(window.YearFiles);
    this.numyears = this.years.length;
    this.middle  =  Math.ceil(this.numyears/2);
    this.container = '#year-files';
    this.selector = '#years-view';
    this.numpickers  = Math.min(this.numyears,Math.floor($(this.selector).width()/55) - 1);
    this.inview = [];
    this.current = null;
    this.step = 5;
    
    //initial population of years row
    this.init = function() {
        var left = Math.ceil(this.numpickers/2);
        var start = this.middle - left;
        var finish = this.middle + (this.numpickers - left - 1);
        this.populate([start,finish]);
        this.load_year_files(this.years[this.middle]);
    };
    
    //show a given year
    this.load_year_files = function(year) {
        $('.year-picker').removeClass('current');
        $(this.container).empty();
        for(var n in YearFiles[year]) {
            var fd = YearFiles[year][n], 
                el = $('#file-block-template').clone();
            el.attr('id','').removeClass('hide');
            el.find('.file-thumb').attr('src',fd.thumb);
            el.find('.file-date').text(fd.date);
            el.data('file',fd.file);
            el.click(function() {
                var d = $(this).data('file'),
                    b = $('#static-container').data('heaplocation'),
                    u = null;
                if(typeof(b) == 'string') {
                    u = authbase+'/'+b+'/'+d;
                    tag_in_modal(u,'object','data');
                    share('#auth-mod',location.origin+location.pathname+'?protocol='+b+'/'+d);
                }
            }).end();  
            $(this.container).append(el);
        }
        $('.year-picker[data-year='+year+']').addClass('current');
        this.current = this.years.indexOf(year);
        if(this.current == this.numyears - 1) {
            $('.years-control.next').addClass('disabled');
        }
        else {
            $('.years-control.next').removeClass('disabled');
        }
        if(this.current == 0) {
            $('.years-control.prev').addClass('disabled');
        }
        else {
           $('.years-control.prev').removeClass('disabled');
        }
    };

    //go to previous year
    this.prev = function() {
        var p = this.current - 1;
        if(p < 0) {
            return false;
        }
        if(p < this.inview[0]) {
            goleft = Math.min(this.step,this.inview[0]);
            if(goleft > 0) {
                newstart = this.inview[0] - goleft; 
                newfinish = this.inview[1] - goleft;
                this.populate([newstart,newfinish]);
            }
        }
        this.load_year_files(this.years[p]); 
    };

    //go to next year
    this.next = function() {
        var n = this.current + 1;
        if(n >= this.numyears) {
            return false;
        }
        if(n >= this.inview[1]) {
            console.log(this.inview);
            goright = Math.min(this.step,(this.numyears - this.inview[1] - 1));
            if(goright > 0) {
                newstart = this.inview[0] + goright;
                newfinish = this.inview[1] + goright;
                this.populate([newstart,newfinish]);
            }
        }
        this.load_year_files(this.years[n]);
    };

    this.gotoyear = function(year) {
        if(!year in window.YearFiles) {
            return;
        }
        var ind = this.years.indexOf(year.toString());
        if(ind == -1) {
            return
        }
        if(ind >= this.inview[0] && ind <= this.inview[1]) {
            this.load_year_files(year)
        }
        else {
            this.populate(this.slice_on(ind));
            this.load_year_files(year);
        }
    }
    
    this.slice_on = function(ind) {
        var left = 0,
            right = 0,
            added = 1;
        while(added < this.numpickers) {
            if(ind - left > 0){
                added++;
                left++;
            }
            if(ind + right < this.numpickers) {
                added++;
                right++;
            }
        }
        return [ind - left, ind + right]; 
    }
    //populate the years row with  a given slice of this.years
    this.populate = function(slice) {
        var yd = this;
        $(yd.selector).empty();
        for(var i = slice[0]; i <= slice[1]; i++) {
            var y = yd.years[i],
            picker =  $('<span class="year-picker" data-year="'+y+'">'+y+'</span>').click(function() {
               yd.load_year_files(String($(this).data('year')));
            });
            $(yd.selector).append(picker);
        }
        yd.inview = slice;
    }; 
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
        $(this).find('iframe,object').height(Math.max(height,300));
    });
}


function tag_in_modal(url,tag,att) {
    $('#auth-mod').modal('show').find('.modal-body').html('<'+tag+'></'+tag+'>');
    frame_height('#auth-mod');
    setTimeout(function() {
        $('#auth-mod').find(tag).attr(att,url);
    },100);
    $('#auth-mod .share-modal').addClass('hide');
}

function iframe_in_modal(url) {
    tag_in_modal(url,'iframe','src');
}

function element_in_modal(el) {
    el = $(el);
    $('#auth-mod').modal('show').find('.modal-body').html($(el).html());
    frame_height('#auth-mod');
}

function video_in_modal(v) {
    var h = vid_template.replace('VIDEOID',v);
    iframe_in_modal(h);
    share('#auth-mod', window.location.href.replace(window.location.search, '')+'?vid='+v);
    bind_vid_adjustment();
}

function book_in_modal(bookurl,bookid) {
    iframe_in_modal(bookurl);
    //$('#auth-mod').data('curbook',bookid);
    //var s = window.location.href.replace(window.location.search, '');
    //if (bookid == undefined) {
    //    var m  = bookurl.match(/{{auth}}\/([a-z0-9]+)/);
    //    if (m.length == 2) {
    //        bookid = m[1];
    //   }
    //}
    //bookid = bookid.replace(/\/$/, '');
    //if (/^[a-z0-9]{3,5}$/.test(bookid)) {
    //    s += '?book='+bookid;
    //    share('#auth-mod', s);
    //}
}

function slideshow_in_modal(id,title) {
    var t = location.origin+location.pathname.replace(/(\/[a-z_\-0-9]+\.html)$/ , "/slideshows/"+id+".htm");
    $.ajax({
        url: t,
        dataType: 'HTML'
    }).done(function(slideshow) { 
        slideshow = $(slideshow);
        //console.log(slideshow);
        //if (slideshow.length == 1) {
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
            slideshow.find('.carousel').height($(window).height()*0.85).fadeIn(200);
            share('#auth-mod',window.location.href.replace(window.location.search, '')+'?slideshow='+id);
            if(title) {
                $('#'+id).find('.carousel').before('<h2 class="slideshow-title">'+title+'</h2>');
            }
        //}
    });
}


function bind_vid_adjustment() {
    $('#auth-mod').on('shown.bs.modal',function() {
        var d = $(this).find('.modal-dialog.modal-lg');
        d.width(d.height() * 1.5);
    });
}

function share(modalid,url) {
    var s = $(modalid).find('span.share');
    $(modalid).find('.share-modal').removeClass('hide').bind('click', function() {
        s.text(url).closest('.share-input-wrap').toggleClass('in');
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
    var m = file.match(/^([a-z0-9]\d+)p(\d+[a-z]?)$/);
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

function process_protocols_search_results(results) {
    var htm = '<div id="search-results"><h3>{{string_translations.search_results}} "'+results.q+'"</h3>';
    if(results.status == 'success') {
        if(/.pdf$/.test(results.results_file)) {
            htm += '<a target="_blank" class="btn btn-primary" href="{{front.domain}}/'+results.results_file+'">{{string_translations.download_search_results}}</a>';
        }
        htm += '<ul class="search-results">';
        var m = results.matches;
        for(var res in m) {
            var r = m[res];
            htm += '<li class="search-result" >';
            htm += '<a class="search-result" data-file="'+r.id+'" data-page="'+r.page+'" href="#NOGO" data-query="'+results.q.replace(/["']/g,'')+'">';
            htm += r.day+'/'+r.month+'/'+r.year;
            if(/^\d+$/.test(r.issue)){
                htm += ', {{string_translations.issue}} '+r.issue+', ';
            }
            htm += "{{string_translations.page}}".replace("'","\'")+' '+r.page
            htm += '</a>';
            htm += '<p>'+r.match+'</p></li>';
        }
        htm += '</ul>';
   }
   else {
       htm = '<div class="alert alert-danger" role="alert">';
       htm += '<strong>{{string_translations.search_error}}:</strong><br>';
       if(results.status == 'faile') {
             htm += results.error
       }
       else {
           htm += 'unknown error';
       }
       htm += '</div>';
    }
   return htm;
}


function bind_protocol_click() {
    $('.search-result').click(function(c) {
        c.preventDefault();
        var file = $(this).data('file'),
            page = $(this).data('page'),
            query = $(this).data('query'),
            u = authbase+'/'+window.DocsFolder+'/'+file+'.pdf',
            conc = '#';
        if(/^\d+$/.test(page)){
            u += '#page='+page;
            conc = '&'
        }
        u += conc+'search="'+query+'"';

        iframe_in_modal(u);
        share('#auth-mod',location.origin+location.pathname+"?protocol="+file);

    });
}

function search(options) {
    $.ajax({
        url: options.url+'&'+options.query,
        DataType: 'json'
    }).done(function(results) {
        $('#auth-mod').modal('show').find('.modal-body').html(options.results_handler(results));
        if('function' == typeof(options.post_process)) {
            options.post_process()
        }
    }).fail(function(err) {
        alert(err);
    });
    if(!options.share) {
        $('#auth-mod').find('.share-modal').hide();
    }
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
    $('[data-toggle="tooltip"]').tooltip();
    window.addEventListener("message", function(event) {
        //if(/textuali\.com\/avnery-timeline\/.*timeline.*html$/.test(event.source) || true) {
            switch(event.data.type) {
                case 'flip':
                    book_in_modal(event.data.url); 
                break;
                case 'video' :
                    video_in_modal(event.data.video);
                break;
                case 'slideshow':
                    slideshow_in_modal(event.data.slideshow,false);
                break;
                //case 'flipped_to':
                //    var s = $('#auth-mod').find('span.share');
                //    cur = s.text().replace(/\/#page.*$/,'');
                //    if(cur == "") {
                //        cur = location.host+location.pathname+'?book='+$('#auth-mod').data('curbook');
                //    }
                //    s.closest('.share-input-wrap').removeClass('in');
                //    s.replaceWith($('<span/>').addClass('share'));
                //    share('#auth-mod',cur+'/#page/'+event.data.page);
                //break;
                default:
                    $.noop();
            }
        //}
    });
    /*$('main .row.well').first().find('.collapse').eq(0).collapse('show');
    $('main .row.well').find('button').click(function() {
        exclude = $(this).next();
        $('.collapse').not(exclude).each(function() {
            if( $(this).hasClass('in') ) {
                $(this).collapse('hide');
            };
        });
    });*/
    if(undefined != window.YearFiles) {
        var yearsdoc = new YearDocs();
        yearsdoc.init();
        $('.years-control.prev').click(function() {
            yearsdoc.prev()
        });
        $('.years-control.next').click(function() {
            yearsdoc.next();
        });
        $('#goto-year li').click(function() {
            yearsdoc.gotoyear($(this).data('year'));
        });
    }
    $('.open-protocol').click(function() {
        var d = $(this).data('file'),
            k = $(this).closest('.well').data('knesset'),
            u = authbase+'/protocols/'+k+'/'+d+'.pdf';
            
        //iframe_in_modal(u);
        tag_in_modal(u,'object','data');
        share('#auth-mod',location.origin+location.pathname+'?protocol='+k+'/'+d);
    });
    $('.open-file').click(function() {
        var d = $(this).data('file'),
            b = $('#static-container').data('heaplocation'),
            u = null;
        if(typeof(b) == 'string') {
            u = authbase+'/'+b+'/'+d;
            tag_in_modal(u,'object','data');
            share('#auth-mod',location.origin+location.pathname+'?protocol='+b+'/'+d);
        }
    });  
    var display_params  = location.search.match(/^\?(vid|book|slideshow|doc|protocol)=(.*)$/);
    
    highlight_menu($('#primary-navigation > .nav'));
    
    $('.external iframe').load(function() {
        $(this).prev('.loader').hide();
        $('#iframe-wrap').css('height','auto');
    });
    
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
        var t = $(this).find('h2').clone().removeClass('col-xs-12').addClass('modal-doc-title');
        var c = $(this).find('.document-image').clone().show();
        $('#auth-mod').find('.modal-body').empty().append(t,c).end().modal('show');
        $('#auth-mod .modal-dialog').addClass('multidoc').scrollTop(0);
        share('#auth-mod', window.location.href.replace(window.location.search, '')+'?doc='+this.id);
    });

    $('.modal-content').click(function(c) {
        if (!$(c.target).is('.share-modal')) {
            $(this).find('span.share').removeClass('in');
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
    $('[data-href]').click(function(c) {
        if($(c.target).closest('.collapse, .collapser').length > 0) {
            return;
        } 
        var h = $(this).data('href'),
            o = $(this).data('open'),
            t = this.title;
        switch(o) {
            case 'blank':
                window.open(h, '_blank');
            break;
            case 'modal':
                iframe_in_modal(h);
            break;
            case 'social' :
                if(h == 'email') {
                    element_in_modal('#mailform-wrap');
                    $('#mailform').submit(function(e) {
                        e.preventDefault();
                        dat = {
                            mailfrom : $('#mailfrom').val(),
                            mailto : $('#mailto').val(),
                            subject : $('#subject').val(),
                            message: $('#message').val()+"\n{{front.domain}}"
                        } 
                        $.ajax({
                            url : "{{front.domain}}/mailer/sendmail.py/",
                            DataType: 'text/html',
                            data : dat,
                            method: 'POST'
                        }).done(function(results) {
                            $('#auth-mod').find('#mailform').fadeOut(300, function() {

                                $('#auth-mod').find('.modal-body').empty().append($(results).hide()); 
                                $('#auth-mod').find('.email-response').fadeIn(300);
                            });
                        }).fail(function(err) {
                            console.log(err);
                        });
                        return false;
                    });

                }
                else {
                    window.open(h,"", "width=600, height=400");  
                }
            break;
            default:
            case undefined:
                window.location.assign(h);
        }
    });
    if(display_params != null) {
        switch(display_params[1]) {
            case 'book' :
                var u = display_params[2];
                var d = decodeURIComponent(window.location.hash);
                if (/#page\/\d+(&q=.+)?$/.test(d)){
                    u += d.replace('&','?');
                }
                book_in_modal(authbase+'/'+u,display_params[2]);        
            break;
            case 'vid' : 
                video_in_modal(display_params[2]);
            break;
            case 'slideshow' :
                slideshow_in_modal(display_params[2],false)
            break;
            case 'doc':
                $('.doc-wrap#'+display_params[2]).trigger('click');
            break;
            case 'protocol':
                var u = /knesset/.test(display_params[2]) ? authbase+'/protocols/' : authbase+"/";
                if (!/\.pdf$/.test(display_params[2])) {
                    iframe_in_modal(u+display_params[2]+'.pdf');
                }
                else {
                    fileandpage = location.href.replace(/^.*\?protocol=/,'');
                    iframe_in_modal(u+fileandpage);
                }
                share('#auth-mod',location.href);
            break;
            default:
                $.noop();
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
        var h = $(this).attr('href'); 
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
            book_in_modal(h,$(this).data('book'))
        }
    });
    
    $('.slideshow-modal').click(function(c) {
        if(!$(c.target).is('a')) {
            s = $(this).data('slideshow');
            slideshow_in_modal(s,false);
        }
    });
    
    $('.bare-slideshow').click(function(c) {
        c.preventDefault();
        var s = $(this).data('slideshow');
        slideshow_in_modal(s,$(c.target).attr('title'));
    });
     
    $('#fsearch').submit(function() {
        search({
            query : $(this).serialize(),
            url : location.origin+'/search/websearch.py/?pretty=1&auth={{auth}}&book=allbooks',
            results_handler: process_fts_search_results
        });
       return false; 
    }); 
    
    $('#psearch').submit(function() {
        search({
            query : $(this).serialize(),
            url : location.origin+'/search/websearch.py/protocols/?pretty=1&auth={{auth}}',
            results_handler : process_protocols_search_results,
            post_process : bind_protocol_click,
            share: true
        });
        var knesset = $(this).find('select[name="book"]').val();
        window.DocsFolder = knesset        
        return false;
    });

    $('#fhsearch').submit(function() {
        var q = $(this).serialize();
        if(window.SearchResultsDownload == "True") {
            q += '&download_button=true';
        }
        search({
            query: q,
            url: location.origin+'/search/websearch.py/press/?pretty=1&auth={{auth}}',
            results_handler: process_protocols_search_results,
            post_process : bind_protocol_click
        });
        window.DocsFolder = $(this).find('input[name="book"]').val();
        return false;
    });
     
    $('#gsearch').submit(function() {
        var query = $(this).serialize();
        search({
            url : search_template.replace('GOOGLESEARCHQUERY',query),
            query : $(this).serialize(),
            results_handler : process_google_search_results
        });
        return false;
   });
        

    $('.util-button').click(function() {
        var tarid = '#'+this.id.replace('-trigger','-container'),
            tar = $(tarid);
        $('.utilbox').not(tarid).removeClass('in');
        tar.toggleClass('in');
    });
   
})

