

import csv,json,jsoncomment,urllib2,re,logging,sys,os,glob,jsonmerge,gettext

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-auth')
jc = jsoncomment.JsonComment(json)
import pystache
stache = pystache.Renderer(
    search_dirs='auth_templates',file_encoding='utf-8',string_encoding='utf-8',file_extension=False
)

from HTMLParser import HTMLParser
from PIL import Image

htmlparser = HTMLParser()
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
        self.langs = {
           "he" : "rtl",
           "en" : "ltr"
        } 
        self.langpat = re.compile("(.*)\-(\w{2})$")
        self.stylevars = {
            "textcolor" : "#333"
        } 
        self.body_blocks = {
            "books": self.books_template_data
        } 
    
    
    def books_template_data(self,lang):
        return {"author_books": self.authorblock}
    
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
                self.indexpath = self.conf['front']['textsdir']+"/"+authdir+"/site"
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
        menu_items = []
        for menu_item in self.siteconfig['menu'][lang]:
            try :
                it = self.siteconfig['pages'][menu_item]
                menu_items.append(                
                {
                    "file": 'index' if menu_item == 'home' else menu_item,
                    "label": it['label'][lang],
                    "title" : it['mouseover'][lang]
                }
             )
            except:
                logger.error(menu_item+" not configured in 'pages' block")
            
        socials =[]
        for social in self.siteconfig['socials'] :
            socials.append(jsonmerge.merge(social,{"label":social['label'][lang]}))
        templatedata['menu_items'] = menu_items
        templatedata['socials'] = socials
        templatedata['cssoverride']=os.path.exists(self.indexpath+"/css/local-override.css") 
        return stache.render(stache.load_template('header.html'),templatedata).encode('utf-8')
    
    def render_footer(self,lang):
        templatedata=self.get_globals(lang)
        return stache.render(stache.load_template('footer.html'),templatedata).encode('utf-8') 
     
    def render_body(self,page,lang):
        block = self.get_globals(lang)
        template = self.siteconfig['pages'][page]['template']
        contf= self.indexpath+"/"+lang+"/"+page+"-maintext.txt"
        statf = self.indexpath+"/"+lang+"/"+page+"-static.html"
        tempf = "auth_templates/"+template+".html"
        if template in self.body_blocks:
            block = jsonmerge.merge(block,self.body_blocks[template](lang))
        if template == "static":
            if(os.path.exists(statf)):
                logger.info(u'loading '+lang+'/'+page+' static html')
                stat = open(statf).read() 
                return stat  
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
        return  stache.render(stache.load_template(template+".html"),block).encode('utf-8')
    
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
        string_translations = {}
        for p,v in self.siteconfig['string_translations'].iteritems():
            try: 
                string_translations[p]=v[lang]
            except:
                logger.info(u'missing '+p+' in '+lang)
        g['string_translations']=string_translations 
        g['dir'] = self.langs[lang]
        g['lang'] = lang
        g['auth_name_he'] = self.siteconfig['string_translations']['author']['he']
        g['auth_name_en'] = self.siteconfig['string_translations']['author']['en']
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
        rtlvars = jsonmerge.merge(self.stylevars, {"dir": "rtl", "side": "right", "oposide": "right" })
        stylertl.write(stache.render(stache.load_template('authorsite.css'),rtlvars)) 
        stylertl.close()
        logger.info('rtl styles done')
        ltrvars = jsonmerge.merge(self.stylevars,{ "dir": "ltr", "side": "left", "oposide": "right" }) 
        styleltr.write(stache.render(stache.load_template('authorsite.css'),ltrvars))
        styleltr.close()
        logger.info('ltr styles done')
        
    
    #def merge_menus(self,dict):
    #    ret = []
    #    for pages in dict.itervalues():
    #        ret = ret + pages.append["home"]
    #    return ret

    def render_site(self):
        self.render_styles()
        for lang,men in self.siteconfig['menu'].iteritems():
            header = self.render_header(lang)
            footer = self.render_footer(lang)
            if not 'home' in men:
                self.render_page('home',lang,header,footer)
            for page in men:
                self.render_page(page,lang,header,footer)
        logger.info(authdir+" site done")




if __name__=='__main__':
    authdir = sys.argv[1]
    asg = AuthorSiteGenerator(authdir)
    if(asg.good_to_go()):
        logger.info(u"rendering "+authdir)
        asg.render_site()
    
