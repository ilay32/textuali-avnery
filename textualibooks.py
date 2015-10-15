import json,logging,os,textualangs,glob,Image,re,random,cgi
from PIL import Image
from webconfig import folders
from HTMLParser import HTMLParser
htmlparser = HTMLParser()

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('textualibooks')

def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

class TextualiBook:
    def __init__(self,bookid,authid,env):
        self.authtexts = None
        self.files = None
        self.booktype = None
        self.authorblock = env['authors'][authid]
        self.bookdata = self.authorblock['books'][bookid]
        self.bookid = bookid
        self.authid = authid
        self.env = env
        self.indexpath = env['front']['indices_dir']+"/"+authid+"/"+bookid+"/"
        self.srcdomain = env['front']['domain']
        self.srcpath = env['front']['srcs_dir']+"/"+authid+"/"+bookid
        self.srcscleanpath = os.path.basename(env['front']['srcs_dir'])+"/"+authid+"/"+bookid
        self.books = TextualiBooks(env)
        self.on_site_display = True
        if 'site' in env:
            self.on_site_display = self.get_type() and str(self.get_type()) not in env['site']['suppress_book_types']
            
    def index_dict(self):
        files = self.book_files()
        if not files:
            return None
        ret = self.bookdata
        ret['authdir'] = self.authid
        ret['pdf_downlads'] = self.authorblock['pdf_downloads']
        ret['indices_dir'] = self.env['front']['indices_dir']
        ret['srcs'] = os.path.join(self.srcdomain,self.srcscleanpath) 
        ret['front'] = self.env['front']
        ret['type'] = self.books.get_book_type(self.bookid)
        if os.path.isfile(ret['indices_dir']+"/"+self.authid+"/authorstyle.css"):
            ret['has_author_css'] = 1
        if os.path.isfile(self.indexpath+"bookstyle.css"):
            book['has_book_css'] = 1
        if folders.has_key(self.authid+'-'+self.bookid):
            ret['has_search'] = 1    
        ret['pages'] = files['count'] 
        ret['page_list'] =  map((lambda uri : unescape(os.path.splitext(os.path.basename(uri))[0])),files['jpgs']) 
        ret.update(self.calc_book_offsets(files['count'],ret['page_list']))
        ret.update(self.book_sides())
        dlang = "he" if ret['side'] == 'right' else "en"
        ret['authnice'] = textualangs.default(self.bookdata['language'],dlang,self.authorblock['nicename'])
        ret['string_translations'] = textualangs.translations(dlang)
        ret['frontjpg'] = os.path.basename(files['jpgs'][0])
        ret['openbook_ratio'] = files['openratio']
        ret['ver'] = str(random.randint(999,9999)) 
        pages = self.pages_list()
        if(pages):
            ret.update(pages)
        return ret 
    
    def generic_block_dict(self):
       if 'site' not in self.env:
           logger.error("can't privde blocks without site configuration data")
           return {}
       ret = self.bookdata
       block = self.authorblock
       files = self.book_files()
       if not files:
           logger.error("can't find book files for "+self.bookdata['book_nicename'])
           return ret
       ret['cover'] = files['front']
       ret['backcover'] = files['back']
       ret['pages'] = files['count']
       ret['aspect'] = 'vertical' if files['closedratio'] > 1.0 else 'horizontal'
       ret['url'] = files['url']+"/"+self.bookid
       ret['language_name'] = textualangs.langname(self.bookdata['language'])
       ret['bookdir'] = self.bookid
       if 'orig_match_id' in self.bookdata:
           orig = self.bookdata['orig_match_id'] 
           ret['orig_name'] = self.authorblock['books'][orig]
           ret['orig_url'] = files['url']+"/"+orig
           ret['other_langs'] = self.get_other_langs(orig)
       return ret
       
    
    def get_other_langs(self,orig):
        if 'book_translations_base' not in self.env['site']:
            logger.error("please set 'book_translations_base', e.g en/publications.html, in siteconfig.json for books template to be complete")
            return ""
        if not self.on_site_display:
            return ""
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
            ret = {"generic_srcs" : os.path.join(pagebase,self.srcscleanpath)}
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
                            "href" : self.books.pageurl.format(pagebase,self.bookid,pagenum),
                            "title" : self.bookdata['book_nicename'] + " | "+pageslang+" "+str(pagenum),
                            "text": self.bookdata['book_nicename'] + ", "+pageslang+" "+str(pagenum)
                        })
                ret = {"pagelinks" : pages}     
        return ret 
    
    def page_num_by_file(self,s):
        ret = ""
        r = self.books.pagenum        
        m = r.search(s)
        if m and m.group(1):
            ret = m.group(1).strip("0")
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
        authtexts = self.env['front']['srcs_dir'].replace("../","")+"/"+self.authid
        domain = self.authorblock['generic_site_domain'] if 'generic_site_domain' in self.authorblock else self.srcdomain
        authtexts = os.path.join(domain,authtexts)
        urlbase = authtexts+"/"+self.bookid+"/jpg/"
        jpgs = sorted(glob.glob(self.srcpath+"/jpg/*.jpg"))
        htmls = glob.glob(self.srcpath+"/html/*.htm*")
        if not len(jpgs):
            return None
        f = Image.open(jpgs[0])
        fsize = f.size
        ret =  {
            "count" : len(jpgs),
            "jpgs" : jpgs,
            "htmls" : htmls,
            "front" : urlbase+os.path.basename(jpgs[0]),
            "back" : urlbase+os.path.basename(jpgs[len(jpgs) - 1]),
            "count" : len(jpgs),
            "openratio" : float(2*fsize[0])/fsize[1],
            "closedratio" :  float(fsize[1])/fsize[0],
            "url" : authtexts
        }
        self.files = ret
        return ret
    
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



class TextualiBooks:
    def __init__(self,data=None):
        if not data:
            #self.conf = json.load(file('config.json'))
            self.conf = json.load(file('/home/sidelang/webapps/phptextuali/textuali/config.json'))
        else:
            self.conf = data 
         
        self.realpagename = re.compile("p\d{3,4}$")
        self.pageurl = '{0}?book={1}/#page/{2}'
        self.pagenum = re.compile("p+(\d{3,4})+\.htm+l?$")

    def get_book_name(self,bookid,author):
        a = self.conf['authors'][author]['books']
        if bookid in a:
            return a[bookid]['book_nicename']
        return ""

    def get_book_type(self,bookid):
        btype  = self.conf['book_types'].get(bookid[:1],"book")
        return textualangs.translate(btype,'he')
            

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
            ret.append({
                "bookdir" : book.bookid,
                "book_nicename" : book.bookdata['book_nicename'],
                "type" : self.get_book_type(book.bookid)
            })        
        return ret        


