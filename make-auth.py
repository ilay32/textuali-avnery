
import csv,json,jsoncomment,urllib2,re,logging,sys,os,glob,jsonmerge,lesscpy,six, optparse,textualangs,pystache,string,random,cgi,urlparse,textualibooks,subprocess
from PIL import Image
from HTMLParser import HTMLParser


op = optparse.OptionParser()
op.add_option("-s", action="store_true", dest="render_styles", help="render style files")
op.add_option("--hidelang", action="store", type="string", dest="hidelang", help="hides the specified language wihtout rendering the site")
op.add_option("--showlang", action="store", type="string", dest="showlang", help="hides the specified language without rendering the site")
op.add_option("-p", "--pagelinks", action="store_true", dest="pagelinks", help="generate dummy webpages with link to book htmls")
op.add_option("--init",action="store",type="string", dest="init_auth",help="initialize author site. AUTHOR should be an existing directory in texts")
op.add_option("--subdir",action="store",type="string", dest="subdir",help="render the site in a the given directory. assuming it exists under texts/author with a siteconfig.json and all")

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-auth')
jc = jsoncomment.JsonComment(json)
stache = pystache.Renderer(
    search_dirs='auth_templates',file_encoding='utf-8',string_encoding='utf-8',file_extension=False
)
htmlparser = HTMLParser()

class AuthorSiteGenerator:
    puncpat = re.compile('[%s]' % re.escape(string.punctuation))
    frame0 = 'http://img.youtube.com/vi/{0}/0.jpg' 
    #booktranslink = '{0}/{1}?book={2}'    
    def __init__(self,auth,subdir):
        self.site_dir = 'site' if subdir is None else subdir 
        self.global_template_vars = None
        self.lang = None
        self.indexpath = None
        self.siteconfig = None
        self.authorblock = None
        self.langpath = None
        self.conf = jc.load(file('config.json'))
        self.auth = auth
        self.authtexts = None
        self.found = self.search_auth()
        #self.langpat = re.compile("(.*)\-(\w{2})$")
        self.langpat = re.compile("^[a-z]{2}$")
        self.hidden = []
        self.body_blocks = {
            "books" : self.books_template_data,
            "publications": self.publications_template_data,
            "videos" : self.videos_template_data,
            "isotope": self.isotope_template_data,
            "pictures" : self.pictures_template_data,
            "documents" : self.documents_template_data,
            "protocols" : self.protocols_template_data,
            "file_heap": self.file_heap_template_data
        } 
        if os.path.isfile(".makeauthignore") :
            self.hidden =  eval(open('.makeauthignore').read())
    
    def default(self,obj):
        return textualangs.default(self.lang, self.siteconfig['primary_language'],obj)
    
    def fhsearch_data(self,pagedict):
        return {
            'nicename' : self.default(pagedict['description']),
            'folder' : pagedict['heap_location']
        } 
    
    def parse_file_name(self,filename,heap,thumb_options):
        filename = filename.encode('utf-8')
        pat = re.compile("^[A-Z]\-I(\d+)\-D(\d+)")
        m = pat.match(filename)
        if not m or len(m.groups()) != 2:
            logger.warning("invalid file name (ignored): "+filename)   
            return False
        date = m.group(2)
        day = date[:2]
        month = date[2:4]
        year = '19'+date[4:6]
        return {
            "ord" : m.group(1),
            "year" : year,
            "day" : day,
            "month" : month,
            "date" : "/".join([day,month,year]),
            #"length" : m.group(2),
            #"begin" : m.group(3),
            "file" : filename,
            "thumb" : self.get_pdf_thumb(filename,heap,thumb_options)
        }
    
    
    def get_pdf_thumb(self,pdfname,pdfsdir,thumb_options):
        thumb = os.path.join(pdfsdir+"-thumbs",pdfname.replace('.pdf','.jpg'))
        thumburl = re.sub(r".*"+self.auth,self.authtexts,thumb).encode('utf-8')
        pdf = os.path.join(pdfsdir,pdfname)
        if not os.path.isfile(thumb): 
            if not thumb_options:
                logger.warning("please specify thumb_options for this page")
            return ""
            logger.info("creating thumb for "+pdf)
            try:
                params = 'convert '+thumb_options+' '+pdf+'[0]'+' '+thumb

                subprocess.check_call(params,shell=True)
                logger.info("done "+thumb)
            except Exception as e:
                logger.error(e)
        return thumburl
    
    def file_heap_template_data(self,pagedict):
        if 'heap_location' not in pagedict:
            logger.error("please specify heap location")
            return {}
        heaplocation = os.path.join(self.conf['front']['srcs_dir'],self.auth,pagedict['heap_location'])
        if not os.path.isdir(heaplocation+"-thumbs"):
            os.makedirs(heaplocation+"-thumbs")
        files = [self.parse_file_name(f,heaplocation,pagedict.get('thumb_options')) for f in os.listdir(heaplocation)]
        files.sort(key=lambda x: int(x['ord']))
        very_last_year = int(files[len(files) -1]['year'])
        minissue = int(files[0]['ord'])
        maxissue = int(files[len(files) - 1]['ord'])
        yearfiles = dict()
        years = list()
        for f in files:
            fy = f['year']            
            if fy in yearfiles:
                yearfiles[fy].append(f)
            else:
                years.append(fy)
                yearfiles[fy] = [f]
        return {
                "yearfiles" : yearfiles,
                "heap_base" : pagedict['heap_location'],
                "organic_form" : pagedict.get('organic_form'),
                "fhsearch" : self.fhsearch_data(pagedict),
                "years" : years,
                "download_button" : pagedict.get('download_button',False),
                "minissue" : minissue,
                "maxissue" : maxissue
            } 

    
    
    def _file_heap_template_data(self,pagedict):
        if 'heap_location' not in pagedict:
            logger.error("please specify heap location")
            return {}
        rows  = []
        files = [self.parse_file_name(f) for f in os.listdir(os.path.join(self.conf['front']['srcs_dir'],self.auth,pagedict['heap_location']))]
        files.sort(key=lambda x: int(x['ord']))
        very_last_year = int(files[len(files) -1]['year'])
        years_in_row = int(pagedict['years_in_row']) if 'years_in_row' in pagedict else 10
        loc = 0
        global_years_count = 0
        while loc < len(files):
            row_count = 0
            first_year = files[loc]['year']
            last_year = str(min(int(first_year) + years_in_row, very_last_year)) 
            row =  {
                "first_year" : "19"+first_year,                
                "last_year" : "19"+last_year,              
                "years" : list(),
            }
            end = False
            year = first_year
            while row_count <= years_in_row and not end:
                global_years_count += 1
                year_files = [f for f in files if f['year'] == year]
                if len(year_files) > 0:
                    row['years'].append({
                        "year" : "19"+year,
                        "year_files" :  year_files,
                        "index" : global_years_count
                    })
                row['years'].sort(key=lambda x: x['index'])
                year = str(int(year) + 1)
                loc = loc + len(year_files)
                if loc == len(files) - 1:
                    end = True
                row_count += 1
            rows.append(row)
        return {"rows" : rows, "heap_base": pagedict['heap_location']}

         
    def protocols_template_data(self,pagedict):
        knessets = []
        for f,name in pagedict['file_lists'].iteritems():
            protlist = os.path.join(self.indexpath,f+".csv")
            if not os.path.isfile(protlist):
                logger.error("can't find "+protlist+". check siteconfig")
            else:
                knesset = {
                    "name" : self.default(name['label']),
                    "years" : {},
                    "knesset" : f 
                }
                protlist = open(protlist,'r')
                reader  = csv.reader(protlist, delimiter=',', quotechar='"')
                for row in reader:
                    year = row[1][-4:]
                    if year not in knesset['years']:
                        knesset['years'][year] = {
                            "year" : year,                             
                            "protocols" : [{
                                "file" : row[1].replace('/','_'),
                                "vol" : row[0],
                                "date" : row[1]
                            }] 
                        }
                    else:
                        knesset['years'][year]['protocols'].append( {"vol" : row[0], "date" : row[1], "file": row[1].replace('/','_')})
            knesset['years'] = [v for k,v in knesset['years'].items()]
            knesset['years'].sort(key=lambda x : x['year'])
            knessets.append(knesset)
            knessets.sort(key=lambda x : x['knesset'])
        return {"knessets" : knessets, "protocols_base": pagedict['parent_folder']}
    
         
    def documents_template_data(self, pagedict) :
        ret = {}
        docsfile = self.indexpath+"/"+pagedict['pagename']+".json"
        if not os.path.isfile(docsfile) :
            logger.error("can't use documents template without "+docsfile)
            return ret
        docs = jc.load(file(docsfile))
        documents = []
        for docid,doc in docs.items():
            d = {}
            if isinstance(doc['image'],list) :
                first = doc['image'][0]
                d['others'] = doc['image'][1:]
                d['count'] = len(doc['image'])
                d['image'] = first
            else :
                d['image'] = doc['image']
            d['title'] = self.default(doc['title'])
            d['docid'] = docid
            d['year'] = doc['year']
            documents.append(d)
        documents.sort(key=lambda x : x['year'])
        if len(documents) > 0 :
            ret = {"has_docs" : True, "docs" : documents}
        return ret
            
    def pictures_template_data(self,pagedict):
        picfile = self.indexpath+"/pictures.json"
        if not os.path.isfile(picfile):
            logger.error("can't use pictures template without "+picfile)
            return {}
        slideshows = jc.load(file(picfile))
        for slideshow in slideshows:
            slideshow['slideshowtitle'] = slideshow['description'][self.lang]
            slideshow['titleattr']  = cgi.escape(slideshow['slideshowtitle']).encode('utf-8', 'xmlcharrefreplace').strip()
            for index, slide in enumerate(slideshow['slides']):
                if index == 0:
                    slide['active'] = "active"
                    slideshow['thumb'] = self.thumb_slide(slide['slide'])
                slide['caption'] = slide['title'][self.lang]
                slide['alt'] =  cgi.escape(self.default(slide['title'])).encode('utf-8', 'xmlcharrefreplace').strip()
                slide['ord'] = index
        if not os.path.isdir(self.langpath+"/slideshows"):
            os.makedirs(self.langpath+"/slideshows")
        logger.info("rendering slideshows in "+self.lang+"/slideshows")
        for slideshow in slideshows:
            if len(slideshow['slides']):
                slideshowfrag = open(self.langpath+"/slideshows/"+slideshow['id']+".htm","w")
                slideshowfrag.write(stache.render(stache.load_template("slideshow.html"),jsonmerge.merge(slideshow,self.get_globals())).encode('utf-8'))

        return {"slideshows": slideshows}
    
    def bare_slideshow(self,path):
        slides = os.listdir(os.path.join(self.indexpath,"img",path))
        slideshow = {
            "id" : path, 
            "slides" : [], 
        }
        for  index,slide in enumerate(slides):  
            slide = {
                "active" : "active" if index == 0 else None,
                "caption" : None,
                "alt" : os.path.splitext(slide)[0],
                "ord" : index,
                "slide" : os.path.join("img",path,slide)
            }
            slideshow['slides'].append(slide)
            slideshow.update(self.get_globals())

        slideshowfrag = open(self.langpath+"/slideshows/"+path+".htm","w")
        slideshowfrag.write(stache.render(stache.load_template("slideshow.html"),slideshow).encode('utf-8'))
            


    def thumb_slide(self,image):
        source = self.indexpath+"/"+image 
        thumb = re.sub("\.[a-z]{2,4}$","-thumbnail.jpg",source)
        if not os.path.isfile(thumb):
            try:
                size = 420,420
                im = Image.open(source)
                im.thumbnail(size,Image.ANTIALIAS)
                im.save(thumb, "JPEG")
            except IOError as e:
                logger.error("cannot create thumbnail for "+source+". reason:\n"+str(e)) 
        return thumb.replace(self.indexpath,"") 

    def isotope_template_data(self,pagedict): 
        bfilename = pagedict['pagename']+"-isotope-blocks.json"
        blocksf = self.langpath+"/"+bfilename;
        if not os.path.isfile(blocksf):
            blocksf = self.indexpath+"/"+self.siteconfig['primary_language']+"/"+bfilename
        if os.path.isfile(blocksf):
            blocks = jc.load(file(blocksf))
            for block in blocks:
                if 'text' in block:
                    block['text'] = block['text'][self.lang]
                if not bool(urlparse.urlparse(block['img']).scheme):
                    block['relative'] = "../img/"
                if 'link' in block and 'vid' in urlparse.parse_qs(urlparse.urlparse(block['link']).query):
                    block['playbutton'] = True
                if 'collapse' in block:
                    c = block['collapse']
                    col  = {
                        "coid" : block['id']+'-collapse',
                        "short" : self.default(c['short']),
                        "long" : self.default(c['long']) 
                    }
                    if 'trigger' in c and c['trigger'] == "arrow":
                        col['arrow'] = 1
                    else:
                        col['more'] = 1
                    block['collapse'] = col
        else:
            logger.error("could not find "+blocksf)
            blocks = []
        return {"iblocks" : blocks}
    
    def publications_template_data(self,pagedict):
        prim = self.siteconfig['primary_language']
        if self.lang ==  prim:
            cats = self.books_by_cat(pagedict)
        else:
            cats = self.books_by_lang(prim,pagedict)
        return {"cats":cats}
   
    def books_template_data(self,pagedict):
        return {"books" : [book.generic_block_dict() for book in self.filter_page_books(pagedict,False)]}
         
    def books_by_lang(self,skiplang,pagedict):
        ret = []
        tempdict = {}
        for book in self.filter_page_books(pagedict,True):
            lang = book.bookdata['language']
            if lang != skiplang:
                if lang not in tempdict:
                    tempdict[lang] = {
                        "lang" : lang,
                        "title" : textualangs.langname(lang),
                        "books" : [book.generic_block_dict()]
                    }
                else:
                    tempdict[lang]['books'].append(book.generic_block_dict())
        for obj in tempdict.itervalues():
            ret.append(obj)
        ret.sort(cmp=lambda x,y : -1 if x['lang'] == self.lang else 1)
        return ret    
    
    def books_by_cat(self,pagedict):
        langbooks = self.filter_page_books(pagedict,False)        
        ret = []
        tempdict = {}
        for book in  langbooks:
            booktype = book.get_type()
            if booktype not in tempdict:
                tempdict[booktype] = {
                    "type" : booktype,
                    "title" : textualangs.translate(booktype,self.lang,plural=True),
                    "books": [book.generic_block_dict()]
                }
            else:
                tempdict[booktype]['books'].append(book.generic_block_dict())
        for obj in tempdict.itervalues():
            ret.append(obj)

        ret.sort(cmp=lambda x,y : -1 if x['type'] == 'book' else 1)
        return ret
    
    def filter_page_books(self,pagedict,allangs):
        if not allangs:
            books = [x for x in self.authbooks if x.bookdata['language'] == self.lang]
        else:
            books = self.authbooks
        if 'exclude_types' in pagedict:
            books = [x for x in books if x.get_type() not in pagedict['exclude_types']]
        if 'exclude_ids' in pagedict:
            books = [x for x in books if x.bookid not in pagedict['exclude_ids']]
        return books
    
    def videos_template_data(self,pagedict):
        ret = None
        vidlistsrc = self.indexpath+"/videos.json" 
        if not os.path.isfile(vidlistsrc):
            logger.error("videos.json missing from "+self.indexpath)
        vidict = jc.load(file(vidlistsrc))
        videos = []
        if self.lang == self.siteconfig['primary_language']:
            for vid in vidict[self.lang]:
                videos.append(self.video_item(vid))                
            videos.sort(key=lambda x : x['date'],reverse=True)
            ret = {"primary" : True,  "videos" : videos}
        else:
            for lang,vids in vidict.iteritems():
                if lang != self.siteconfig['primary_language']:
                    langvids = []
                    for vid in vids:
                        langvids.append(self.video_item(vid))
                    langvids.sort(key=lambda x : x['date'], reverse=True)
                    videos.append({
                        "lang": lang,
                        "groupname": textualangs.langname(lang,self.lang),
                        "videos" : langvids
                    })
            videos.sort(key=lambda x : x['lang'])
            videos.sort(cmp=lambda x,y : -1 if x['lang'] == self.lang else 0)
            ret = {"video_groups":videos} 
        return ret 
                
    def video_item(self,vid): 
        return jsonmerge.merge(vid, {"firstframe" : self.video_frame(vid), "title": vid['title'][self.lang]})
     
    def video_frame(self,vid):
        ret = self.frame0.format(vid['id'])
        ext = '.jpg'
        if 'local_video_frame_extension' in self.siteconfig:
            ext = self.siteconfig['local_video_frame_extension']
        if os.path.isfile(self.vidframepath.format(vid['id'],ext)):
            ret = self.vidframeurl.format(vid['id'],ext) 
        if 'startframe' in vid:
            if bool(urlparse.urlparse(vid['startframe']).scheme):
                ret = vid['startframe']
            elif os.path.isfile(self.vidframepath.format(vid['startframe'],'')):
                ret = self.vidframeurl.format(vid['startframe'],'')
        return ret

    #def timeline_template_data(self,pagedict):
    #    src = self.conf['front']['domain']+"/timeline"
    #    tvars = {}
    #    dlang = self.siteconfig['primary_language']
    #    defaults = {"src": src, "theme_color" : "#288EC3", "auth":self.auth}
    #    varsf = self.langpath+"/timeline.json"
    #    if os.path.exists(varsf) :
    #        tvars = jc.load(file(varsf))
    #    elif self.lang != dlang:
    #        try:
    #            tvars = jc.load(self.indexpath+"/"+dlang+"/"+page+".json")
    #            logger.info("timline - "+self.lang+" using defaults found in the hebrew directory")
    #        except:
    #            logger.info("no timeline configuration, using general defaults")

    #    return jsonmerge.merge(defaults,tvars)
          

    def search_auth(self):
        for authid,authorblock in self.conf['authors'].iteritems():
            #d = authorblock['dir']
            if(authid == authdir):
                front = self.conf['front']
                self.authorblock = authorblock
                self.indexpath = os.path.join(front['indices_dir'],authdir,self.site_dir)
                self.siteconfig = jc.load(file(self.indexpath+"/siteconfig.json"))
                self.vidframeurl = self.siteconfig['baseurl']+'/img/video/{0}{1}' 
                self.vidframepath = self.indexpath+'/img/video/{0}{1}' 
                self.devurl = front['domain']+self.indexpath.replace("/home/sidelang/webapps/phptextuali","").replace("../","/")
                self.authtexts = self.siteconfig['destination_domain']+"/"+front['srcs_dir'].replace("../","")+"/"+authdir
                self.authbooks = textualibooks.TextualiBooks(self.conf).get_auth_books(authid,self.siteconfig)

                return True
         
    def good_to_go(self):
        if(self.found):
            logger.info("good to go")
            return True
        else:
            logger.error("sorry, "+authdir+" doesn't seem to be a correct directory name")
            return False        
    
    def compile_title(self,pagedict,delim=" | ") :
        ret = self.default(self.authorblock['nicename'])
        if 'label' in pagedict and self.lang in pagedict['label']:
            l = pagedict['label'][self.lang]
            if l:
                ret += delim+l
        if 'mouseover' in pagedict and self.lang in pagedict['mouseover'] :
             ret += delim+pagedict['mouseover'][self.lang]
        return ret.strip() 
         
    def render_header(self,page):
        lang = self.lang
        pagedict = self.siteconfig['pages'][page]
        templatedata=self.get_globals()
        templatedata['bodyclass'] = pagedict['template']+" "+page
        templatedata['html_title'] = self.compile_title(pagedict)
        desc = {}
        if 'description' in pagedict :
            desc = pagedict['description']
        elif 'mouseover' in pagedict:
            desc = pagedict['mouseover']
        elif 'label' in pagedict:
            desc = pagedict['label']
        templatedata['description'] = self.default(desc)
        
        if 'page_title' in pagedict and lang in pagedict['page_title'] and 'innertitle' not in pagedict:
            templatedata['pagetitle'] = pagedict['page_title'][lang]
            if 'title_image' in pagedict:
                templatedata['title_image'] =  pagedict['title_image']
            templatedata['has_pagetitle'] = True
        else:
            templatedata['has_pagetitle'] = None 
                 
        
        menu_items = []
        utils = [] 
        favicon = self.conf['front']['domain']+"/media/favicon.ico"
        if isinstance(self.siteconfig.get('favicon'),six.string_types):
            favicon = self.siteconfig['baseurl']+"/img/"+self.siteconfig['favicon']
        templatedata['favicon'] = favicon
        
        # find the facebbook share image (for <meta og:image>) 
        fbshare = None
        try: 
            fbshare = os.path.basename(glob.glob(self.indexpath+"/img/fbshare-default*")[0])
        except:
            if 'logo' in templatedata:
                fbshare  = templatedata['logo'] 
        if 'fbshare' in pagedict:
            fbshare  = pagedict['fbshare']
        
        if fbshare is not None:
            templatedata['fbshare'] = fbshare
                
        # collect menu items for lang
        for menu_item in self.siteconfig['menu'][lang]:
            menu_items.append(self.menu_items(menu_item,page))
        
        # simliarly, colect the util buttons (search, info, share)
        if 'utils'  in self.siteconfig:
            for utilname,utildefs in self.siteconfig['utils'].iteritems():
                if 'icon' in utildefs :
                    ic = utildefs['icon']
                    if not urlparse.urlparse(ic).netloc :
                        icon = self.conf['front']['domain']+"/media/"+ic 
                    else:
                        icon = ic 
                else:
                    icon = ""
                #if os.path.isfile(self.indexpath+"/img/"+util['icon']):
                #    icon = self.siteconfig['baseurl']+"/img/"+util['icon']
                utils.append({
                    "name" : utilname,
                    "icon" : icon,
                    "title" : self.default(utildefs['mouseover'])
                }) 
            templatedata['utils'] = utils
        templatedata['menu_items'] = menu_items
        templatedata['cssoverride']=os.path.isfile(self.indexpath+"/css/local-override.css") 
        templatedata['localscript'] = os.path.isfile(self.indexpath+"/js/sitescript.js")
        return stache.render(stache.load_template('header.html'),templatedata).encode('utf-8')
    
    # recursively generate the menu items list
    def menu_items(self,pagename,curpage):
        if pagename not in self.siteconfig['pages']:
            logger.error("the menu item "+pagename+" is not defined in the pages list")
            return None
        it = self.siteconfig['pages'][pagename]
        dropdown = {"items":[]}
        if 'dropdown' in it and isinstance(it['dropdown'],list):
            for menu_item in it['dropdown']:
                dropdown['items'].append(self.menu_items(menu_item,curpage))
        else:
            dropdown = ""
        return {
            "id" : pagename,
            "href": ('index' if pagename == 'home' else pagename)+".html",
            "label": it['label'][self.lang],
            "title" : it['label'][self.lang] if 'mouseover' not in it else it['mouseover'][self.lang],
            "dropdown" : dropdown,
        }
    
    def render_footer(self,page):
        pagedict = self.siteconfig['pages'][page]
        templatedata = self.get_globals()
        authbooks = []
        for book in self.authbooks:
            authbooks.append(book.booklink_dict())
        #    authbooks.append({
        #       "id" :  book['bookdir'],
        #       "name" : book['book_nicename'],
        #       "title" : cgi.escape(book['book_nicename']).encode('utf-8', 'xmlcharrefreplace')

        #    })
        templatedata['books'] = authbooks
        footf = self.indexpath+"/footer.html"
        if os.path.isfile(self.langpath+"/footer.html") :
            footf = self.langpath+"/footer.html"
        foot = ""
        if os.path.isfile(footf):
            foot = '<footer id="site-footer"><div class="container"><div class="row">'

            foot += open(footf).read()      
            foot += '</div></div></footer>'
        else:
            logger.info("no footer.html found in "+self.indexpath+" or "+self.langpath) 
        if self.site_dir == 'site':
            templatedata['search_form_popups'] = True
            if pagedict['template'] == "protocols":
                templatedata['protocolsearch'] = self.protocols_template_data(pagedict)
            else:
                templatedata['protocolsearch'] = None 
            if pagedict['template'] == 'file_heap': 
                templatedata['fhsearch'] = self.fhsearch_data(pagedict)
            else:
                templatedata['fhsearch'] = None
        else:
            templatedata['search_form_popups'] = False


        templatedata['page'] = page
        #aboutf = self.langpath+"/about.txt"
        #if os.path.isfile(aboutf):
        #    about = open(aboutf).read()
        #    templatedata['about'] = about
        #else: 
        #    logger.info("missing "+aboutf)
        if 'socials' in self.siteconfig:
            socials =[]
            for social,details in self.siteconfig['socials'].iteritems() :
                socials.append({
                    "label" : self.default(details['label']),
                    "icon" : os.path.join(self.siteconfig['baseurl'],"img", details['icon']) if 'icon' in details else os.path.join(self.conf['front']['domain'], "media", social+".png"),
                    "url" : self.compile_social_url(social,page)
                })
            templatedata['socials'] = socials
            searchopts = self.siteconfig['utils']['search']['opts']
            if 'google' in searchopts:
                templatedata['googlesearch'] = 1
            if 'fts' in searchopts and self.authorblock.get('has_full_search'):
                templatedata['booksearch'] = 1
        return foot+stache.render(stache.load_template('footer.html'),templatedata).encode('utf-8') 
    
    def compile_social_url(self,social,page) :
        pagedict = self.siteconfig['pages'][page]
        ret = ""
        if social == "facebook" :
            ret = "https://www.facebook.com/sharer/sharer.php?u="        
            if page != "home" :
                ret += self.siteconfig['destination_domain']+"/"+page+".html"
        if social == "twitter" :
            text = pagedict['twitt'] if 'twitt' in pagedict else self.compile_title(pagedict,",") 
            ret = "https://twitter.com/intent/tweet?text="+text            
        if social == "email":
        #    pagename = self.default(pagedict['label']) if 'label' in pagedict else ""
        #    mailto = self.siteconfig['socials'][social]['mailto'] 
        #    #ret = "mailto:"+mailto+"?Subject="+self.siteconfig['destination_domain']+" "+pagename
            ret = "email"
        return ret
    
    def get_additional(self,page):
        add = ""
        if 'no_additional' in self.siteconfig['pages'][page]:
            return add
        if os.path.isfile(self.indexpath+"/additional.html"):
            add = open(self.indexpath+"/additional.html").read()
        if os.path.isfile(self.langpath+"/additional.html"):
            add = open(self.langpath+"/additional.html").read()
        if os.path.isfile(self.langpath+"/"+page+"-additional.html"):
            add += open(self.langpath+"/"+page+"-additional.html").read()
        #if os.path.isfile(addf) :
        #    #logger.info(u'loading '+addf)
        #    add = open(addf).read()
        return add
         
    def render_body(self,page):
        pagedict = self.siteconfig['pages'][page]
        lang = self.lang
        block = self.get_globals()
        ret = "" 
        if 'innertitle' in pagedict and pagedict['innertitle']:
            block['pagetitle'] = self.default(pagedict['page_title'])
            if 'title_image' in pagedict:
                block['title_image'] = pagedict['title_image']
            block['has_pagetitle'] = True
        else:
            block['has_pagetitle'] = False
        
        template = pagedict['template']
        contf= self.langpath+"/"+page+"-maintext.html" 
        statf = self.langpath+"/"+page+"-static.html"
        tempf = "auth_templates/"+template+".html"
        add = self.get_additional(page)        
        if template in self.body_blocks:
            pagedict['pagename'] = page
            block = jsonmerge.merge(block,self.body_blocks[template](pagedict))
        if template == "external":
            url = self.default(pagedict['url'])
            if not url or not urlparse.urlparse(url).netloc :
                logger.error("cannot find iframe url for  "+lang+"/"+page)
            else:
                block['url'] = url
                block['pagename'] = page

        if template == "404" : 
            block['message'] = pagedict['message']
        
        if template == "static":
            if(os.path.isfile(statf)):
                logger.info(u'loading '+lang+'/'+page+' static html')
                stat = open(statf).read() 
                ret = '<div id="static-container">'+stat+'</div><!-- static-container--></main>'            
            else:
                logger.error(page+" ("+lang+") "+"has template 'static' but no " + page + "-static.html found in ..."+self.site_dir+"/"+lang)
                return
        
        elif os.path.isfile(contf):
            logger.info(u'loading '+ page+ ' maintext  into template')
            cont = open(contf).read()
            block['has_content'] = True
            block['content'] = cont
        
                
        if page  == 'timeline':
            self.render_timeline_src()
        
        if ret == "": 
            if not os.path.isfile(tempf):
                logger.error("can't find template '"+template+"'")
                return
            ret =  stache.render(stache.load_template(template+".html"),block).encode('utf-8')

        if pagedict.get('additional_on_top'):
            ret = add+ret
        else:
            ret = ret+add
        return ret
    
    def render_timeline_src(self):
        lang = self.lang
        tfilepath = "../timeline/"+self.auth+"_"+lang+".html"
        block = self.get_globals()
        tvars = {}
        defaults = {
            "theme_color" : "#288EC3",  
            "skin":"timeline.dark", 
            "src" : os.path.join(self.conf['front']['domain'],"timeline",self.auth+"_"+lang+".json")
        }
        varsf = self.langpath+"/timeline_src_params.json"
        if os.path.isfile(varsf) :
            tvars = jc.load(file(varsf))
        elif lang != "he":
            try:
                tvars = jc.load(self.indexpath+"/"+self.siteconfig['primary_language']+"/timeline_src_params.json")
                logger.info("timeline - "+lang+" using defaults found in the hebrew directory")
            except:
                logger.info("no timeline configuration, using general defaults")
        tvars = jsonmerge.merge(defaults,tvars)
        try:
            block = jsonmerge.merge(block,tvars)
            tfile = open(tfilepath,"w")
            tfile.write(stache.render(stache.load_template("timeline_src.html"),block))
            tfile.close()
            logger.info("source written at "+tfilepath)
        except Exception as e:
            logger.error(e)
         
    def render_page(self,page):
        body = self.render_body(page)
        header = self.render_header(page)
        footer = self.render_footer(page)
        #home as index
        if(page == 'home'):
            page = 'index'
        if not os.path.isdir(self.langpath):
            os.makedirs(self.langpath)
        if isinstance(body,six.string_types) :
            try:
                htmlfile = open(self.langpath+"/"+page+".html",'w')
                htmlfile.write(header+body+footer)
                htmlfile.close()
                logger.info(textualangs.langname(self.lang,"en")+" "+page+" done")
            except Exception as e:
                logger.error(e)
             
    def get_globals(self):
        if isinstance(self.global_template_vars,dict) and self.global_template_vars['lang'] == self.lang:
            return self.global_template_vars
        lang = self.lang
        g={"baseurl": self.siteconfig['baseurl']}
        #string_translations = {}
        #for p,v in self.siteconfig['string_translations'].iteritems():
        #    try: 
        #        string_translations[p]=v[lang]
        #    except:
        #        logger.info(u'missing '+p+' in '+lang)
        g['string_translations']=jsonmerge.merge(textualangs.translations(lang),textualangs.translations(lang,self.siteconfig['string_translations']))
        g['dir'] = textualangs.direc(lang)
        g['lang'] = lang
        g['primlang'] = self.siteconfig['primary_language']
        g['primlangname'] = textualangs.langname(g['primlang'])
        g['altlang'] = self.siteconfig.get('alternate_language')
        g['altlangname'] =  textualangs.langname(g['altlang'])
        if 'langswitch' in self.siteconfig['string_translations'] and g['primlang'] in self.siteconfig['string_translations']['langswitch']:
            g['altlangname'] =  self.siteconfig['string_translations']['langswitch'][g['primlang']]
        g['is_primary_language'] = lang == g['primlang']
        g['split_logo'] = self.siteconfig.get('split_logo')
        # prevents css caching
        g['ver'] = str(random.randint(999,9999)) 
        for p,v in self.siteconfig.iteritems():
            if isinstance(v,six.string_types):
                g[p]=v
        try:
            a = self.siteconfig['string_translations']['author']
            g['auth_name'] = self.default(a)
        except:
            logger.error("the author name is not specified for "+lang+" nor for "+self.siteconfig['primary_language'])
        g['front'] = self.conf['front']
        g['auth'] = self.auth
        g['authtexts'] = self.authtexts
        langs = []
        for l in self.siteconfig['menu'].iterkeys():
            if l != lang:
                name = textualangs.langname(l)
                if 'langswitch' in g['string_translations']:
                    name = g['string_translations']['langswitch']
                icon = '<img src="'+self.conf['front']['domain']+'/media/globe.png"/>'
                if not g['is_primary_language']:
                    icon = "["+g['primlangname']+"]"
                if 'language_button_content' in self.siteconfig and lang in self.siteconfig['language_button_content']:
                    icon = self.siteconfig['language_button_content'][lang]
                langs.append({
                    "name" : name,
                    "code" : l,
                    "icon" : icon
                })
        g['langs'] = langs
        if "info" in self.siteconfig:
            info = self.siteconfig['info']
            g['info'] = {
                "link" : self.default(info['link']),
                "title" : self.default(info['mouseover'])
            }
        #try to find the right logo for this language
        logo = None
        dlang = 'he' if textualangs.direc(lang) == 'right' else 'en'
        try:
            logo  = os.path.basename(glob.glob(self.indexpath+"/img/logo-"+lang+".*")[0])
        except:
            logos  = glob.glob(self.indexpath+"/img/logo-"+dlang+".*")
            if len(logos) > 0:
                logo = os.path.basename(logos[0])
                logger.warning("using "+logo+" as logo for "+textualangs.langname(lang))
        
        if isinstance(logo,six.string_types):
            g['logo'] = logo
        else:
            if 'logo' in self.siteconfig:
                try:
                    im = Image.open(source)
                    print im
                except:
                    g['logo'] = False
                    g['text_logo'] = self.siteconfig['logo']
                    print g['text_logo']
            else:
                logger.error("can't find logo for "+self.lang+ "or a general one")
        self.global_template_vars = g
        return g
         
    def render_styles(self):
        stylertl = open(self.indexpath+"/css/style-rtl.css", 'w')
        styleltr = open(self.indexpath+"/css/style-ltr.css", 'w')
        rtlvars = jsonmerge.merge(self.siteconfig['stylevars'], {"dir": "rtl", "side": "right", "oposide": "left" })
        srtl = lesscpy.compile(six.StringIO(stache.render(stache.load_template('authorsite.less'),rtlvars).encode('utf-8')),minify=True)
        if srtl:
            stylertl.write(srtl) 
        stylertl.close()
        logger.info('rtl styles done')
        ltrvars = jsonmerge.merge(self.siteconfig['stylevars'],{ "dir": "ltr", "side": "left", "oposide": "right" }) 
        sltr = lesscpy.compile(six.StringIO(stache.render(stache.load_template('authorsite.less'),ltrvars).encode('utf-8')),minify=True)
        if sltr:
            styleltr.write(sltr)
        if not sltr or not srtl:
            logger.error("could not compile authorsite.less")
        styleltr.close()
        logger.info('ltr styles done')
    
    def render_script(self):
        scriptf = self.indexpath+"/js/authorscript-"+self.lang+".js"
        s = open(scriptf,"w")
        script = stache.render(stache.load_template('authorscript.js'),self.get_globals()).encode('utf-8')
        if not script:
            logger.error("could not render author script")
        else:
            s.write(script) 
            logger.info(scriptf+" written")
        s.close()
        
    def render_pagelinks(self):
        logger.info('generating links to book pages')
        front = self.conf['front']
        pageurl = '{0}/{1}/html/{2}'
        linksdir = self.indexpath+"/pagelinks" 
        links = '{0}/{1}-pages.html'
        if not os.path.isdir(linksdir):
            os.makedirs(linksdir)
        for book in self.authorblock['books'] :
            bookdir = book['bookdir']
            #logger.info('generating links for '+book['bookdir'])
            booklinks = open(links.format(linksdir,bookdir),"w")
            pages = []
            htmls = glob.glob(self.conf['front']['srcs_dir']+"/"+self.auth+"/"+bookdir+"/html/*.htm")
            if len(htmls) == 0:
                return
            for p in htmls:
                pages.append(pageurl.format(self.authtexts,bookdir,os.path.basename(p)))
            booklinks.write(stache.render(stache.load_template('pagelinks.html'),{"pages" : pages}).encode('utf-8'))
            booklinks.close()
        logger.info('page links generated')

            
    def render_site(self):
        if options.render_styles:
            self.render_styles()
        access = open(self.indexpath+"/access", "w")
        access.write(stache.render(stache.load_template("access"),{"lang":self.siteconfig['primary_language'], "domain" : self.siteconfig['destination_domain'] }))
        
        if options.pagelinks:
            self.render_pagelinks()
         
        for lang,men in self.siteconfig['menu'].iteritems():
            if lang in self.hidden:
                logger.info("skipping "+textualangs.langname(lang)+" -- it is hidden. to render it use '--showlang "+lang+"' and render the site again")
            else:
                self.lang = lang
                self.langpath = self.indexpath+"/"+lang
                self.render_script()
                if isinstance(self.siteconfig.get('bare_slideshows'),list):
                    logger.info("rendering bare slideshows in "+self.lang+"/slideshows")
                    if not os.path.isdir(self.langpath+"/slideshows"):
                        os.makedirs(self.langpath+"/slideshows")
                    for slideshow in self.siteconfig['bare_slideshows']:
                        self.bare_slideshow(slideshow)
                for page,defs in self.siteconfig['pages'].iteritems():
                    if 'template' in defs and not not defs['template']:
                        self.render_page(page)
                logger.info(textualangs.langname(lang,"en")+" rendered")
                print "======"
        logger.info(authdir+" site done")
    
                   
    def book_files(self,book):
        urlbase = self.authtexts+"/"+book+"/jpg/"
        jpgs = sorted(glob.glob(self.conf['front']['srcs_dir']+"/"+self.auth+"/"+book+"/jpg/*.jpg"))
        if len(jpgs) == 0:
            logger.error("no jpgs for "+book)
            return None
        frontjpg = Image.open(jpgs[0])
        fsize = frontjpg.size
        ratio = float(fsize[1])/fsize[0]
        return {
            "front" : urlbase+os.path.basename(jpgs[0]),
            "back" : urlbase+os.path.basename(jpgs[len(jpgs) - 1]),
            "count" : len(jpgs),
            "proportions" : ratio
        }
    
    
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
    if isinstance(options.init_auth,six.string_types):
        logger.info("intializing default site for "+options.init_auth)
        quit()
    if not args:
        logger.error("usage:python2.7 make-auth.py [options] [lang to show/hide]  <author>")
        quit()
    else:
        authdir = args[0]
        asg = AuthorSiteGenerator(authdir,options.subdir)
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
                destht = "/home/sidelang/webapps/"+asg.siteconfig['destination_folder']+"/.htaccess"
                if not os.path.isfile(destht):
                    logger.warning("flip addresses are under "+asg.siteconfig["destination_domain"]+".\nsave "+asg.indexpath+"/access as "+destht+" to make them work")

                if os.path.isdir("/home/sidelang/webapps/"+asg.siteconfig['destination_folder']):
                    print "if you like what you see in %s, type 'copy-generic %s %s':" %(asg.devurl, asg.auth,asg.siteconfig['destination_folder'])
                else:
                    logger.error("specified live destination "+asg.siteconfig['destination_folder']+" doesn't exist.")
                
