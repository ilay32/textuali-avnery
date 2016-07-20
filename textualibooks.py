import json,logging,os,textualangs,glob,Image,re,random,cgi,pycurl,io,urllib
from webconfig import folders
from PIL import Image
from HTMLParser import HTMLParser
htmlparser = HTMLParser()

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('textualibooks')

def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

class TextualiBook:
    def __init__(self,bookid,authid,env):
        self.files = None
        self.booktype = None
        self.authorblock = env['authors'][authid]
        self.bookdata = self.authorblock['books'][bookid]
        self.bookid = bookid
        self.authid = authid
        self.env = env
        self.indexpath = env['front']['indices_dir']+"/"+authid+"/"+bookid+"/"
        self.srcpath = env['front']['srcs_dir']+"/"+authid+"/"+bookid
        self.authcleanpath = os.path.basename(env['front']['srcs_dir'])+"/"+authid
        self.books = TextualiBooks(env)
        #self.on_site_display = True
        #if 'site' in env:
        #    self.on_site_display = self.get_type() and str(self.get_type()) not in env['site']['suppress_book_types']
        self.default_lang = "he" if textualangs.direc(self.bookdata['language']) == 'rtl' else "en"
        self.auth_htm_title_part = self.default('authpart_htm_title').format(self.default(self.authorblock['nicename']))
        self.thumbsize = 200,200
    
    def cascade(self,key):
        ret = self.authorblock.get(key)
        if key in self.bookdata:
            ret = self.bookdata[key]
        return ret

    def get_pages_map(self):
        domain = self.cascade('external_texts_domain')
        logging.info("getting pages map from "+domain) 
        url = domain+'?book_map='+self.bookid;
        buf = io.BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL,str(url))
        c.setopt(c.WRITEFUNCTION,buf.write)
        c.perform()
        return buf.getvalue().decode('UTF-8')
         
        
    def htm_template_data(self,htmfile):
        num = self.page_num_by_file(htmfile)
        pagedesc = self.bookdata['book_nicename']
        pageliveid = self.authid+"-"+self.bookid 
        if num:
            pagedesc += " - "+self.default('page_word')+" "+str(num)
            pageliveid += "-"+str(num)
        authpart = self.auth_htm_title_part 
        return {
           "title" : pagedesc+" | "+authpart,
           "pageliveid" : pageliveid
        }
       
    def default(self,obj):
        return textualangs.default(self.bookdata['language'],self.default_lang,obj)

    def index_dict(self):
        files = self.book_files()
        if not files:
            return None
        ret = self.bookdata
        ret['authdir'] = self.authid
        ret['bookdir'] = self.bookid
        ret['pdf_downloads'] = self.authorblock['pdf_downloads']
        ret['indices_dir'] = self.env['front']['indices_dir']
        ret['srcs'] = os.path.join(self.env['front']['domain'],self.authcleanpath+"/"+self.bookid)
        ret['front'] = self.env['front']
        #ret['type'] = self.books.get_book_type(self.bookid)
        ret['type'] = textualangs.translate(self.get_type(),self.bookdata['language'])
        if os.path.isfile(ret['indices_dir']+"/"+self.authid+"/authorstyle.css"):
            ret['has_author_css'] = 1
        if os.path.isfile(self.indexpath+"bookstyle.css"):
            book['has_book_css'] = 1
        #if folders.has_key(self.authid+'-'+self.bookid):
        #    ret['has_search'] = 1    
        ret['has_search'] = self.bookdata.get('has_search')
        ret['pages'] = files['count'] 
        ret['page_list'] =  map((lambda uri : unescape(os.path.splitext(os.path.basename(uri))[0])),files['jpgs']) 
        ret.update(self.calc_book_offsets(files['count'],ret['page_list']))
        ret.update(self.book_sides())
        ret['authnice'] = self.default(self.authorblock['nicename'])
        ret['string_translations'] = textualangs.translations(self.default_lang)
        ret['frontjpg'] = os.path.basename(files['jpgs'][0])
        ret['openbook_ratio'] = files['openratio']
        ret['ver'] = str(random.randint(999,9999)) 
        ret['rel'] = self.auth_text_relation()
        ret['write_index_to'] = os.path.join(self.indexpath,'index.php')
        ret['write_script_to'] = os.path.join(self.indexpath,'bookscript.js')
        pages = self.pages_list()
        if(pages):
            ret.update(pages)
        #if self.bookdata['editorial_info'] or self.bookdata['remark']:
        #    ret['info'] = True
        if self.bookdata.get('info_box'):
            ret['has_info'] = True
            ret['info_items'] = [{
                "name": textualangs.translate(key,'he'),
                "content" : val
            } for key,val in self.bookdata['info_box'].iteritems() ]
            if self.bookdata.get('language_translated_from') :
                ret['info_items']['tanslated_from'] = {
                    "content" : textualangs.langname(self.bookdata['language_translated_from'],self.bookdata['language']),
                    "content" : textualangs.translate("translation from",self.bookdata['language'],multi=True)
                } 
        if 'external_texts_domain' in self.authorblock or 'external_texts_domain' in self.bookdata:
            ret['external_texts_map'] = self.get_pages_map()
            ret['external_texts'] = True
        if 'blocked' in self.bookdata:
            ret['blocked'] = self.bookdata['blocked']
            message  = self.cascade('blocked_message')
            ret['blocked_message'] = self.default(message) if isinstance(message,dict) else message
        return ret 
         
    def auth_text_relation(self):
        t = self.bookdata['book_type']
        l = self.bookdata['language']
        k = 'by'
        if t == 'translation':
            k = 'translated_by'
        if t == 'about':
            k = 'about'
        if t == 'edited':
            k = 'edited_by'
        return textualangs.translate(k,l)
        
    def generic_block_dict(self):
       if 'site' not in self.env:
           logger.error("can't provide blocks without site configuration data")
           return {}
       ret = self.bookdata
       block = self.authorblock
       files = self.book_files()
       domain = self.env['site']['destination_domain'] if 'destination_domain' in self.env['site'] else self.env['front']['domain']
       authbase = os.path.join(domain,self.authcleanpath)
       bookbase = authbase+"/"+self.bookid
       if not files:
           logger.error("can't find book files for "+self.bookdata['book_nicename'])
           return ret
       ret['cover'] = bookbase+"/front-thumbnail.jpg"
       if self.get_type() != "magazine":
           ret['backcover'] = bookbase+"/back-thumbnail.jpg"
       ret['pages'] = files['count']
       ret['aspect'] = 'vertical' if files['closedratio'] > 1.0 else 'horizontal'
       ret['url'] = bookbase
       ret['language_name'] = textualangs.langname(self.bookdata['language'])
       ret['bookdir'] = self.bookid
       if 'orig_match_id' in self.bookdata:
           orig = self.bookdata['orig_match_id'] 
           ret['orig_name'] = self.authorblock['books'][orig]
           ret['orig_url'] = authbase+"/"+orig
           ret['other_langs'] = self.get_other_langs(orig)
       return ret
       
    
    def get_other_langs(self,orig):
        #if 'book_translations_base' not in self.env['site']:
        #    logger.error("please set 'book_translations_base', e.g en/publications.html, in siteconfig.json for books template to be complete")
        #    return ""
        #if not self.on_site_display:
        #    return ""
        olangs = {"langs" : []}
        for bookid,bookdata in self.authorblock['books'].iteritems():
            if bookid != self.bookid and 'orig_match_id' in bookdata :
                if bookdata['orig_match_id'] == self.bookid or bookdata['orig_match_id'] == orig or bookid == orig:
                    olangs['langs'].append({
                        "name" : textualangs.langname(bookdata['language']),
                        "link": "?book="+bookid
                    })
        if len(olangs['langs']) == 0:
            olangs = ""
        return olangs

    def pages_list(self):
        ret = None
        pages = []
        if self.bookdata['has_texts'] and 'generic_site_domain' in self.authorblock:
            pagebase = self.authorblock['generic_site_domain']
            ret = {"generic_srcs" : os.path.join(pagebase, self.authcleanpath+"/"+self.bookid)} 
            if 'pagelink_base' in self.authorblock:
                pagebase = os.path.join(pagebase,self.authorblock['pagelink_base'])
            pageslang = textualangs.translate("pages",self.bookdata['language'])
            ret['generic_base'] = pagebase
            htmls = self.book_files()['htmls']
            if len(htmls) >  0:
                for p in htmls:
                    pagenum = self.page_num_by_file(os.path.basename(p))
                    if pagenum:
                        pages.append({
                            "href" : self.books.pageurl.format(self.authorblock['generic_site_domain'],self.authid,self.bookid,os.path.basename(p)),
                            "title" : self.bookdata['book_nicename'] + " | "+pageslang+" "+str(pagenum),
                            "text": self.bookdata['book_nicename'] + ", "+pageslang+" "+str(pagenum)
                        })
                ret['pagelinks'] = pages    
        return ret 
    
    def page_num_by_file(self,s):
        ret = ""
        r = self.books.pagenum        
        m = r.search(s)
        if m and m.group(1):
            ret = m.group(1).lstrip("0")
        return ret

    def book_ratio(self,frontjpg):
        f = Image.open(frontjpg)
        fsize = f.size
        return {
            "open" : float(2*fsize[0])/fsize[1],
            "closed" :  float(fsize[1])/fsize[0]
        }
    
    def book_sides(self):
        d = textualangs.direc(self.bookdata['language'])
        ret = {
            "flipdirection" : d
        }
        if d  == 'rtl' : 
            ret['side'] = 'right'
            ret['oposide'] = 'left'
            ret['backward'] = 'forward'
            ret['forward'] = 'backward'
        else:
            ret['side'] = 'left'
            ret['forward'] = 'forward'
            ret['backward'] = 'backward'
            ret['oposide'] = 'right'
        return ret      


    def book_files(self):
        if self.files:
            return self.files
        jpgs = sorted(glob.glob(self.srcpath+"/jpg/*.jpg"))
        htmls = glob.glob(self.srcpath+"/html/*.htm*")
        if not len(jpgs):
            return None
        if not os.path.isfile(self.srcpath+"/front-thumbnail.jpg"):
            self.make_thumb('front',jpgs)
        if not os.path.isfile(self.srcpath+"/back-thumbnail.jpg"):
            self.make_thumb('back',jpgs)
        f = Image.open(jpgs[0])
        fsize = f.size
        ret =  {
            "count" : len(jpgs),
            "jpgs" : jpgs,
            "htmls" : htmls,
            "front" : os.path.basename(jpgs[0]),
            "back" : os.path.basename(jpgs[len(jpgs) - 1]),
            "count" : len(jpgs),
            "openratio" : float(2*fsize[0])/fsize[1],
            "closedratio" :  float(fsize[1])/fsize[0],
        }
        self.files = ret

        return ret
   
    def make_thumb(self,frontorback,jpgs):
        source = jpgs[0] if frontorback == 'front' else jpgs[len(jpgs) - 1] 
        try:
            im = Image.open(source)
            im.thumbnail(self.thumbsize, Image.ANTIALIAS)
            #d = self.env['front']['indices_dir']+"/"+self.authid+"/"+self.bookid+"/jpg/"
            #if not os.path.exists(d):
            #    os.makedirs(d)
            im.save(self.srcpath+"/"+frontorback+"-thumbnail.jpg", "JPEG")
        except IOError as e:
            logger.error("cannot create thumbnail for "+self.authid+" "+self.bookid+" "+frontorback+" cover. reason:\n"+str(e)) 
        
    
    def calc_book_offsets(self,count,pagelist):
        left = 0
        right = count - 1 
        stop = stop_start = stop_end = False
        while(right > left and not stop):
            if self.books.realpagename.search(pagelist[left]) == None:
                left = left + 1
            else:
                stop_start = True
            if self.books.realpagename.search(pagelist[right]) == None:
                right = right - 1
            else:
                stop_end = True
            stop = stop_end and stop_start 
        return {
            "start_offset" : left,
            "end_offset" : count - right,
            "phispage_count" : right - left + 1
        }

    def get_type(self):
        if self.booktype:
            return self.booktype
        elif 'book_type' in self.bookdata:
            ret =  self.bookdata['book_type']
        else: 
            t = self.bookid[:1]
            if t in self.env['book_types']:
                ret = self.env['book_types'][t]
            elif re.match("[a-z]",t):
                ret = "book"
            else:
                ret = None
        self.booktype = ret
        return ret

    
    def booklink_dict(self):
        return {
            "id" : self.bookid,
            "name" : self.bookdata['book_nicename'],
            "title" : cgi.escape(self.bookdata['book_nicename']).encode('utf-8', 'xmlcharrefreplace')
        }

    def page_redirect(self,pagenum,defaulturl):
        if 'generic_site_domain' in self.authorblock :
            if unicode(pagenum).isnumeric():
                files = self.book_files()
                l  =  map((lambda uri : unescape(os.path.splitext(os.path.basename(uri))[0])),files['jpgs']) 
                domain  = self.authorblock['generic_site_domain']
                start = self.calc_book_offsets(files['count'],l)['start_offset']
                realnum = int(pagenum)+start
                ret = domain+"?book="+self.bookid+"/#page/"+str(realnum)
            else:
                ret = self.authorblock['generic_site_domain']+'?book='+self.bookid
        else:
            ret = defaulturl
        return ret


class TextualiBooks:
    def __init__(self,data=None):
        if not data:
            #self.conf = json.load(file('config.json'))
            self.conf = json.load(file('/home/sidelang/webapps/phptextuali/textuali/config.json'))
        else:
            self.conf = data 
         
        self.realpagename = re.compile("p\d{3,4}$")
        # this renders links to webpages that load the page in ajax
        # its for the bots
        #self.pageurl = '{0}?book={1}/#page/{2}'
        # for now, we do direct link
        self.pageurl = '{0}/texts/{1}/{2}/html/{3}' 
        self.pagenum = re.compile("p+(\d{3,4})+\.htm+l?$")
        
    
    
    def get_book_name(self,bookid,author):
        a = self.conf['authors'][author]['books']
        if bookid in a:
            return a[bookid]['book_nicename']
        return bookid

    #def get_book_type(self,bookid):
    #    btype = self.conf[ 
    #    #btype  = self.conf['book_types'].get(bookid[:1],"book")
    #    return textualangs.translate(btype,'he')
            

    def get_auth_books(self,authid,authsite=None):
        if not authid in self.conf['authors']:
            return None
        a = self.conf['authors'][authid]
        ret = []
        env = self.conf
        if authsite:
            env.update({"site":authsite})
        for bookid in a['books'].iterkeys():
            ret.append(TextualiBook(bookid,authid,env))
        ret.sort(cmp = lambda x,y : -1 if x.bookid < y.bookid else 1)
        ret.sort(cmp = lambda x,y : -1 if 'year' in x.bookdata and 'year' in y.bookdata and  x.bookdata['year'] < y.bookdata['year'] else 1)
        return ret 
   
    def front_template_data(self) :
        authors = []
        for authid,authdata in self.conf['authors'].iteritems():
            if len(authdata['books']):
                authors.append({
                    "authnice":textualangs.default(None, "he", authdata['nicename']),
                    "dir" : authid,
                    "books" : self.auth_books_for_front(authid)
               })
        trns = textualangs.translations('he')
        return {
            "front" : self.conf['front'],
            "authors" : authors, 
            "string_translations" : trns
        }

    
    def auth_books_for_front(self,authid): 
        ret = []
        books = self.get_auth_books(authid)
        for book in books:
            block = {
                "bookdir" : book.bookid,
                "book_nicename" : book.bookdata['book_nicename'],
                "type" : textualangs.translate(book.get_type(),"he")
            }
            if "language_translated_from" in book.bookdata and not not book.bookdata['language_translated_from'] :
                block['translation'] = textualangs.translate("translation from","he",multi=True)+textualangs.langname(book.bookdata['language_translated_from'],'he')
            ret.append(block)
        return ret        


