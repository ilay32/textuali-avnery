

import csv,json,jsoncomment,urllib2,re,logging,sys,os,glob,jsonmerge,lesscpy,six, optparse,textualangs,pystache,string,random

#lets you compile the css with -s or skip it without
op = optparse.OptionParser()
op.add_option("-s", action="store_true", dest="render_styles", help="render style files")
op.add_option("--hidelang", action="store", type="string", dest="hidelang", help="hides the specified language wihtout rendering the site")
op.add_option("--showlang", action="store", type="string", dest="showlang", help="hides the specified language without rendering the site")

#op.add_option("-a", action="store_true", dest="do_htaccess", help="add a .htaccess file according to the 'primary_language' specified in siteconfig.json")

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-auth')
jc = jsoncomment.JsonComment(json)
stache = pystache.Renderer(
    search_dirs='auth_templates',file_encoding='utf-8',string_encoding='utf-8',file_extension=False
)

#htmlparser = HTMLParser()
#hetran = gettext.translation('avnery_heb',os.getcwd()+'/lang',['he_IL'])
#hetran.install('avnery_heb')

def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

class AuthorSiteGenerator:
    def __init__(self,auth):
        self.indexpath = ""
        self.siteconfig = None
        self.authorblock = None
        self.conf = jc.load(file('config.json'))
        self.auth = auth
        self.found = self.search_auth()
        #self.langpat = re.compile("(.*)\-(\w{2})$")
        self.langpat = re.compile("^[a-z]{2}$")
        self.body_blocks = {
            "books": self.books_template_data,
            "videos" : self.videos_template_data,
            "isotope": self.isotope_template_data
        } 
        self.puncpat = re.compile('[%s]' % re.escape(string.punctuation)) 
        self.hidden =  eval(open('.makeauthignore').read())
    
    def isotope_template_data(self,lang): 
        blocksf = self.indexpath+"/isotope-blocks.json";
        if os.path.isfile(blocksf):
            blocks = jc.load(file(blocksf))
            for block in blocks:
                if 'text' in block:
                    block['text'] = block['text'][lang]
        else:
            logger.error("could not find "+blocksf)
            blocks = []
        return {"iblocks" : blocks}
    
    def books_template_data(self,lang):
        block = self.authorblock
        front = self.conf['front']
        auth_base_url = front['domain']+"/"+front['indices_dir']+"/"+self.authorblock['dir']+"/"
        google = "https://www.google.com/search?q={0}"
        for book in block['books']:
            files = self.book_files(book['bookdir'])
            if files != None:
                book['cover'] = files['front']
                book['backcover'] = files['back']
                book['pages'] = files['count']
            book['url'] = auth_base_url+book['bookdir']
            book['language_name'] = textualangs.langname(book['language'])
            if 'orig_id' in book:
                book['orig_name'] = self.get_book_name(book['orig_id'])
                book['orig_url'] = auth_base_url+book['orig_id']
            if 'link' not in book or book['link']=="":
                q = '+'.join(self.puncpat.sub('',book['book_nicename']+" "+self.authorblock['nicename']).split(' '))
                book['google'] = google.format(q.encode('utf-8')) 
            
        return {"author_books":block}
    
    def videos_template_data(self,lang):
        vidlistsrc = self.indexpath+"/videos.json" 
        if not os.path.isfile(vidlistsrc):
            logger.error("videos.json missing from "+self.indexpath)
            return {}
        vidlist = jc.load(file(vidlistsrc))
        videos = []
        frame0 = 'http://img.youtube.com/vi/{0}/0.jpg' 
        for vid in vidlist:
            videos.append(                
                {
                    "id": vid['id'],
                    "title": vid['title'][lang],
                    "firstframe" : frame0.format(vid['id']),
                    "date" : vid['date']
                }
            )
            videos.sort(key=lambda x : x['date'],reverse=True)
        return {"videos" : videos}

    def timeline_template_data(self,lang):
        src = self.conf['front']['domain']+"/timeline"
        vars = {}
        defaults = {"src": src, "theme_color" : "#288EC3", "auth":self.auth}
        varsf = self.indexpath+"/"+lang+"/timeline.json"
        if os.path.exists(varsf) :
            vars = jc.load(file(varsf))
        elif lang != "he":
            try:
                vars = jc.load(self.indexpath+"/he/"+page+".json")
                logger.info("timline - "+lang+" using defaults found in the hebrew directory")
            except:
                logger.info("no timeline configuration, using general defaults")

        return jsonmerge.merge(defaults,vars)
          

    def search_auth(self):
        for authorblock in self.conf['authors']:
            d = authorblock['dir']
            if(d == authdir):
                self.authorblock = authorblock
                self.indexpath = self.conf['front']['indices_dir']+"/"+authdir+"/site"
                self.siteconfig = jc.load(file(self.indexpath+"/siteconfig.json"))
                return True
         
    def good_to_go(self):
        if(self.found):
            logger.info("good to go")
            return True
        else:
            logger.error("sorry, "+authdir+" doesn't seem to be a correct directory name")
            return False        
    
         
    def render_header(self,lang):
        templatedata=self.get_globals(lang)
        # prevents css caching
        templatedata['ver'] = str(random.randint(999,9999)) 
        menu_items = []
        utils = [] 
        favicon = self.conf['front']['domain']+"/media/favicon.ico"
        #try to find the right logo for this language
        logo = None
        dlang = 'he' if textualangs.dir(lang) == 'right' else 'en'
        try:
            logo  = os.path.basename(glob.glob(self.indexpath+"/img/logo-"+lang+".*")[0])
        except:
            logos  = glob.glob(self.indexpath+"/img/logo-"+dlang+".*")
            if len(logos) > 0:
                logo = os.path.basename(logos[0])
                logger.info("using "+logo+" for "+lang+" header")
        if isinstance(logo,six.string_types):
            templatedata['logo'] = logo
        else:
            logger.error("both /img/logo-"+lang+" and /img/logo-"+self.siteconfig['primary_language']+" not found")

        if isinstance(self.siteconfig['favicon'],six.string_types):
            favicon = self.siteconfig['baseurl']+"/img/"+self.siteconfig['favicon']
        templatedata['favicon'] = favicon
        # collect menu items for lang
        for menu_item in self.siteconfig['menu'][lang]:
            menu_items.append(self.menu_items(menu_item,lang))
            # keep this in case the videos page link has to move to the "utilities" element again
            '''if menu_item == "videos":
                templatedata['videos'] = item_block
            else: menu_items.append(item_block)'''
        
        # simliarly, colect the uti buttons (search, info, share)
        for util in self.siteconfig['utils']:
            icon = self.conf['front']['domain']+"media/"+util['icon']
            if os.path.isfile(self.indexpath+"/img/"+util['icon']):
                icon = self.siteconfig['baseurl']+"/img/"+util['icon']
            utils.append({
                "name" : util['name'],
                "icon" : icon,
                "title" : util['mouseover'][lang] if lang in util['mouseover'] else ""
            }) 
        templatedata['utils'] = utils
        templatedata['menu_items'] = menu_items
        templatedata['cssoverride']=os.path.exists(self.indexpath+"/css/local-override.css") 
        return stache.render(stache.load_template('header.html'),templatedata).encode('utf-8')
    
    # recursively generate the menu items list
    def menu_items(self,pagename,lang):
        if pagename not in self.siteconfig['pages']:
            logger.error("the menu item "+pagename+" is not defined in the pages list")
            return None
        it = self.siteconfig['pages'][pagename]
        dropdown = {"items":[]}
        if 'dropdown' in it and isinstance(it['dropdown'],list):
            for menu_item in it['dropdown']:
                dropdown['items'].append(self.menu_items(menu_item,lang))
        else:
            dropdown = ""
        return {
            "file": 'index' if pagename == 'home' else pagename,
            "label": it['label'][lang],
            "title" : it['label'][lang] if 'mouseover' not in it else it['mouseover'][lang],
            "dropdown" : dropdown
        }
    
    def render_footer(self,lang):
        templatedata=self.get_globals(lang)
        aboutf = self.indexpath+"/"+lang+"/about.txt"
        if os.path.isfile(aboutf):
            about = open(aboutf).read()
            templatedata['about'] = about
        else: 
            logger.info("missing "+aboutf)
        socials =[]
        for social in self.siteconfig['socials'] :
            socials.append(jsonmerge.merge(social,{"label":social['label'][lang]}))
    
        templatedata['socials'] = socials
        return stache.render(stache.load_template('footer.html'),templatedata).encode('utf-8') 
     
    def render_body(self,page,lang):
        block = self.get_globals(lang)
        template = self.siteconfig['pages'][page]['template']
        contf= self.indexpath+"/"+lang+"/"+page+"-maintext.txt"
        statf = self.indexpath+"/"+lang+"/"+page+"-static.html"
        tempf = "auth_templates/"+template+".html"
        addf = self.indexpath+"/"+lang+"/"+page+"-additional.html"
        if template in self.body_blocks:
            block = jsonmerge.merge(block,self.body_blocks[template](lang))
        if template == "external":
            pageblock = self.siteconfig['pages'][page]
            if lang in pageblock['url']:
                block['url'] = pageblock['url'][lang]
            else:
                try:
                    block['url'] = pageblock['url']['he']
                except:
                    logger.error("cannot find url for external site page "+lang+"/"+page)

        if template == "static":
            if(os.path.exists(statf)):
                logger.info(u'loading '+lang+'/'+page+' static html')
                stat = open(statf).read() 
                return '<div id="static-container">'+stat+'</div><!-- static-container-->'
            else:
                logger.error(page+" ("+lang+") "+"has template 'static' but no " + page + "-static.html found in ...site/"+lang)
                return
        elif os.path.exists(contf):
            logger.info(u'loading '+ page+ '.txt into template')
            cont = open(contf).read()
            block['content'] = cont
        if not os.path.exists(tempf):
            logger.error("can't find template '"+template+"'")
            return
        if template == 'timeline':
            self.render_timeline_src(lang)
        
        if os.path.isfile(addf) :
            logger.info(u'loading '+lang+'/'+page+' addtional html')
            add = open(addf).read()
        else:
            add = ""
        return  stache.render(stache.load_template(template+".html"),block).encode('utf-8')+add
    
    def render_timeline_src(self,lang):
        tfilepath = "../timeline/"+self.auth+"_"+lang+".html"
        block = self.get_globals(lang)
        vars = {}
        defaults = {"theme_color" : "#288EC3",  "skin":"timeline.dark", "tlconfig" : self.auth, "src" : self.conf['front']['domain']+"/timeline" }
        varsf = self.indexpath+"/"+lang+"/timeline_src_params.json"
        if os.path.exists(varsf) :
            vars = jc.load(file(varsf))
        elif lang != "he":
            try:
                vars = jc.load(self.indexpath+"/he/timeline_src_params.json")
                logger.info("timline - "+lang+" using defaults found in the hebrew directory")
            except:
                logger.info("no timeline configuration, using general defaults")
        #if not os.path.exists(dir):
        #    os.makedirs(dir)
        vars = jsonmerge.merge(defaults,vars)
        try:
            block = jsonmerge.merge(block,vars)
            tfile = open(tfilepath,"w")
            tfile.write(stache.render(stache.load_template("timeline_src.html"),block))
            tfile.close()
            logger.info("source written at "+tfilepath)
        except Exception as e:
            logger.error(e)
         
    def render_page(self,page,lang,header,footer):
        body = self.render_body(page,lang)
        dir = self.indexpath+"/"+lang
        #home as index
        if(page == 'home'):
            page = 'index'
        if not os.path.exists(dir):
            os.makedirs(dir)
        try:
            htmlfile = open(dir+"/"+page+".html",'w')
            htmlfile.write(header+body+footer)
            htmlfile.close()
            logger.info(lang+"/"+page+ u' done')
        except Exception as e:
            logger.error(e)
             
    def get_globals(self,lang):
        g={"baseurl": self.siteconfig['baseurl']}
        #string_translations = {}
        #for p,v in self.siteconfig['string_translations'].iteritems():
        #    try: 
        #        string_translations[p]=v[lang]
        #    except:
        #        logger.info(u'missing '+p+' in '+lang)
        g['string_translations']=jsonmerge.merge(textualangs.translations(lang),textualangs.translations(lang,self.siteconfig['string_translations']))
        g['dir'] = textualangs.dir(lang)
        g['lang'] = lang
        try:
            a = self.siteconfig['string_translations']['author']
            g['auth_name'] = a[lang] if lang in a else a[self.siteconfig['primary_language']]
        except:
            logger.error("the author name is not specified for "+lang+" nor for "+self.siteconfig['primary_language'])
        g['front'] = self.conf['front']
        g['auth'] = self.auth
        return g
         
    #def parse_lang(self,str):
    #    lang = 'he';
    #    m = self.langpat.match(str)
    #    if(m != None):
    #       lang = self.langpat.match(str).group(2) 
    #    return lang
    
    #def strip_lang(self,str):
    #    ans = str
    #    m = self.langpat.match(str)
    #    if(m != None):
    #        ans = self.langpat.match(str).group(1)
    #    return ans
          
    def render_styles(self):
        stylertl = open(self.indexpath+"/css/style-rtl.css", 'w')
        styleltr = open(self.indexpath+"/css/style-ltr.css", 'w')
        rtlvars = jsonmerge.merge(self.siteconfig['stylevars'], {"dir": "rtl", "side": "right", "oposide": "left" })
        stylertl.write(lesscpy.compile(six.StringIO(stache.render(stache.load_template('authorsite.less'),rtlvars).encode('utf-8')),minify=True)) 
        #stylertl.write(lesscpy.compile(six.StringIO(self.json2less(rtlvars)+open('auth_templates/authorsite.less').read()),minify=True)) 
        stylertl.close()
        logger.info('rtl styles done')
        ltrvars = jsonmerge.merge(self.siteconfig['stylevars'],{ "dir": "ltr", "side": "left", "oposide": "right" }) 
        styleltr.write(lesscpy.compile(six.StringIO(stache.render(stache.load_template('authorsite.less'),ltrvars).encode('utf-8')),minify=True))
        #styleltr.write(lesscpy.compile(six.StringIO(self.json2less(ltrvars)+open('auth_templates/authorsite.less').read()),minify=True)) 
        styleltr.close()
        logger.info('ltr styles done')
        
    #def json2less(self,dict) :
    #    ret = "/* Variables from */"
    #    lineform = '@{0}:{1};\n'
    #    for prop,val in dict.iteritems():
    #        ret += lineform.format(prop,val)
    #    return ret
    ##def merge_menus(self,dict):
    #    ret = []
    #    for pages in dict.itervalues():
    #        ret = ret + pages.append["home"]
    #    return ret

    def render_site(self):
        if options.render_styles:
            self.render_styles()
        for lang,men in self.siteconfig['menu'].iteritems():
            if lang in self.hidden:
                logger.info("skipping "+textualangs.langname(lang)+" -- it is hidden. to render it use '--showlang "+lang+"' and render the site again")
            else:
                header = self.render_header(lang)
                footer = self.render_footer(lang)
                #if not 'home' in men:
                #    self.render_page('home',lang,header,footer)
                for page in self.siteconfig['pages']:
                    self.render_page(page,lang,header,footer)
                logger.info(textualangs.langname(lang)+" rendered")
        logger.info(authdir+" site done")
    
        #if options.do_htaccess:
        #lang = self.siteconfig['primary_language'] if 'primary_language' in self.siteconfig else 'he'
        #hf = open(self.indexpath+"/.htaccess","w")
        #hf.write(stache.render(stache.load_template('htaccess.mustache'),{"lang": self.siteconfig['primary_language']}))
        #hf.close()
           
    def book_files(self,book):
        urlbase = self.conf['front']['domain']+os.path.basename(self.conf['front']['srcs_dir'])+"/"+self.auth+"/"+book+"/jpg/"
        jpgs = sorted(glob.glob(self.conf['front']['srcs_dir']+"/"+self.auth+"/"+book+"/jpg/*.jpg"))
        if len(jpgs) == 0:
            logger.error("no jpgs for "+book)
            return None
        return {
            "front" : urlbase+os.path.basename(jpgs[0]),
            "back" : urlbase+os.path.basename(jpgs[len(jpgs) - 1]),
            "count" : len(jpgs)
        }


    def get_book_name(self,bookdir):
       name = ''
       for book in self.authorblock['books']:
           if book['bookdir'] == bookdir:
               name = book['book_nicename']
               break;
       return name
    
    def hide_lang(self,lang):
        if lang in self.hidden:
            logger.info(lang+" already hidden")
        else:
            base  = self.indexpath+"/"+lang+"/"
            os.rename(base+"index.html",base+"_index.html")
            soon = open(base+"index.html","w")
            soon.write("soon")
            soon.close()
            h = open(base+".htaccess","w")
            h.write("RewriteEngine on\nRewriteRule ^.+$ /")
            h.write(self.indexpath.replace('../','')+"/"+lang+"/ [R=302,NC,L]\n")
            h.close()
            self.hidden.append(lang)
            logger.info(lang+" hidden") 
            ig = open(".makeauthignore","w")
            ig.write(jc.dumps(self.hidden))
            ig.close()
            

    def show_lang(self,lang):
        if lang not in self.hidden:
            logger.error(lang+" should be showing. use the --show option only after --hide")
        else:
            base  = self.indexpath+"/"+lang+"/"
            os.remove(base+"index.html")
            os.remove(base+".htaccess")
            os.rename(base+"_index.html",base+"index.html")
            ig = open(".makeauthignore","w")
            h = jc.dumps(self.hidden.remove(lang))
            if h == 'null':
                h = '[]'
            ig.write(h)
            ig.close()
            logger.info(lang+" reinstated")


if __name__=='__main__':
    (options, args) = op.parse_args()
    if not args:
        logger.error("usage:python2.7 make-auth.py [options] [lang (to show/hide]  <author>")
        quit()
    else:
        authdir = args[0]
        asg = AuthorSiteGenerator(authdir)
        if(asg.good_to_go()):
            if options.hidelang:
                if asg.langpat.match(options.hidelang):
                    logger.info("hiding "+options.hidelang)
                    asg.hide_lang(options.hidelang)
                else:
                    logger.error("bad lang to hide: "+options.hidelang+". aborting")
                quit()
            elif options.showlang:
                if asg.langpat.match(options.showlang):
                    logger.info("showing "+options.showlang)
                    asg.show_lang(options.showlang)
                else:
                    logger.error("bad lang to show: "+options.showlang+". aborting")
                quit() 
            else:
                logger.info(u"rendering "+authdir)
                asg.render_site()
            
