
import csv,json,urllib2,re,logging,sys,os,glob,pystache,textualangs,optparse,random
from HTMLParser import HTMLParser
from PIL import Image
from webconfig import folders
logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-in')


stache = pystache.Renderer(search_dirs='book_templates',file_encoding='utf-8',string_encoding='utf-8',file_extension=False)

htmlparser = HTMLParser()
op = optparse.OptionParser()
op.add_option("-u", "--update-config", action="store_true", dest="update_config", help="copy the config.json file from ../textuali")

def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

if __name__=='__main__':
    conf = json.load(file('config.json'))
    (options, args) = op.parse_args()
    if options.update_config:
        if 'textuali-dev' not in os.path.realpath(__file__):
            logger.error("you are using the --update-config option in the wrong place. quitting.")
            quit()
        logger.info("updating config.json")
        old = conf
        new = json.load(file('../textuali/config.json'))
        new['front'] = old['front']
        new['book_types'] = old['book_types']
        conf = new
        os.remove('_config.json')
        os.rename('config.json','_config.json')
        newconfig = open('config.json', 'w')
        newconfig.write(json.dumps(new,encoding='utf-8', sort_keys=False, indent=4))
        newconfig.close()
    logger.info(u"rendering front page")
    for author in conf['authors']:
        author['authnice'] = textualangs.default(None, "he", author['nicename'])
        for book in author['books']:
            btype  = conf['book_types'].get(book['bookdir'][:1],"book")
            book['type'] = textualangs.translate(btype,'he')
    conf['string_translations'] = textualangs.translations('he') 
    file('index.html','w').write(stache.render(stache.load_template('front.html'),conf).encode('utf-8'))
    logger.info("rendering flip ltr/rtl styles")
    fliprtl = open("css/flip-rtl.css","w")
    fliprtl.write(stache.render(stache.load_template("flip-style.css"),{ "dir" : "rtl", "side": "right", "oposide":"left", "even": "even", "odd": "odd"}).encode('utf-8')) 
    fliprtl.close()
    flipltr = open("css/flip-ltr.css","w")
    flipltr.write(stache.render(stache.load_template("flip-style.css"),{ "dir" : "ltr", "side": "left", "oposide":"right","even":"odd", "odd":"even"}).encode('utf-8')) 
    flipltr.close()
    logger.info(u"rendering book indices")
    #book_type_pattern = re.compile('"^([a-zA-Z])(\d)$"')
    for authorblock in conf['authors']:
        authdir = authorblock['dir']
        authbooks = authorblock['books']		
        pdfs = authorblock['pdf_downloads']
        for book in authbooks:
            bd = book['bookdir']
            book['pdf_downloads'] = pdfs
            book['indices_dir'] = conf['front']['indices_dir']
            indexpath = book['indices_dir']+"/"+authdir+"/"+bd+"/"
            srcpath  = conf['front']['srcs_dir']+"/"+authdir+"/"+bd+"/"
            srcurl = conf['front']['domain']+os.path.basename(conf['front']['srcs_dir'])+"/"+authdir+"/"+bd+"/"
            book['srcs'] = srcurl
            #book['topdir'] = conf['front']['domain']
            #book['coddir'] = book['topdir'] + conf['front']['coddir']
            book['front'] = conf['front']
            jpgslist = sorted(glob.glob(srcpath+"jpg/*.jpg"))
            foundpages = len(jpgslist)
            book['type'] = conf['book_types'].get(bd[:1],"book")
            if(foundpages > 0):
                #logger.info("rendering "+book['book_shortname'])
                if(os.path.isfile(book['indices_dir']+"/"+authdir+"/authorstyle.css")):
                    book['has_author_css'] = 1
                if(os.path.isfile(indexpath+"bookstyle.css")):
                    book['has_book_css'] = 1
                if (folders.has_key(authdir+'-'+bd)):
                    book['has_search'] = 1
                book['pages'] = foundpages
                realpagename = re.compile("p\d{3,4}$")
                book['page_list']= map((lambda uri : unescape(os.path.splitext(os.path.basename(uri))[0])),jpgslist)
                left  = 0
                right = foundpages - 1
                stop = stop_start = stop_end = False
                while(right > left and not stop):
                    if realpagename.search(book['page_list'][left]) == None:
                        left = left + 1
                    else:
                        stop_start = True
                    if realpagename.search(book['page_list'][right]) == None:
                        right = right - 1
                    else:
                        stop_end = True
                    stop = stop_end and stop_start 
                book['start_offset'] = left
                book['end_offset'] = foundpages - right 
                book['phispage_count'] = right - left + 1
                book['authdir'] = authdir
                book['frontjpg'] = os.path.basename(jpgslist[0])
                book['ver'] = str(random.randint(999,9999))
                frontjpg = Image.open(jpgslist[0])
                fsize = frontjpg.size
                book['openbook_ratio'] = float(2*fsize[0])/fsize[1]
                book['flipdirection'] = textualangs.direc(book['language'])
                dlang = "he"
                if book['flipdirection'] == 'rtl' : 
                    book['side'] = 'right'
                    book['oposide'] = 'left'
                    book['backward'] = 'forward'
                    book['forward'] = 'backward'
                else:
                    book['side'] = 'left'
                    book['forward'] = 'forward'
                    book['backward'] = 'backward'
                    book['oposide'] = 'right'
                    dlang = "en"
                book['authnice'] = textualangs.default(book['language'], dlang, authorblock['nicename'])
                book['string_translations'] =  textualangs.translations(dlang) 
                if not os.path.exists(indexpath):
                    os.makedirs(indexpath)

                ind = open(indexpath+"index.html",'w')
                ind.write(stache.render(stache.load_template('index-template.html'),book).encode('utf-8'))
                sc = open(indexpath+"bookscript.js", 'w')
                sc.write(stache.render(stache.load_template('bookscript.js'),book).encode('utf-8'))
                pages = []
                pageurl = '{0}html/{1}'
                if book['has_texts'] :
                    htmls = glob.glob(srcpath+"/html/*.htm*")
                    if len(htmls) >  0:
                        for p in htmls:
                            pages.append(pageurl.format(srcurl,os.path.basename(p)))
                        pagelinks = open(indexpath+"pagelinks.html","w")
                        pagelinks.write(stache.render(stache.load_template('pagelinks.html'),{"pages" : pages}).encode('utf-8'))
                        pagelinks.close()

                logger.info(book['book_shortname']+ " complete")
            else:
                logger.info(book['book_shortname'] + " couldn't find pages")
        
        logger.info(authdir + " book indices complete")


