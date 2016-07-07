
import csv,json,urllib2,re,logging,sys,os,glob,pystache,textualangs,optparse,random,textualibooks
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

#def page_num_by_file(s):
#    ret = ""
#    r = re.compile("p+(\d{3,4})+\.htm+l?$")
#    m = r.search(s)
#    if m and m.group(1):
#        ret = m.group(1).strip("0")
#    return ret
        

if __name__=='__main__':
    conf = json.load(file('config.json'))
    (options, args) = op.parse_args()
    # update config file if requested and use the new for rendering
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
    
    # load the book utilities with already read config
    books = textualibooks.TextualiBooks(conf)
    file('index.html','w').write(stache.render(stache.load_template('front.html'),books.front_template_data()).encode('utf-8'))
   
    # write ltr/rtl css with mustache 
    logger.info("rendering flip ltr/rtl styles")
    fliprtl = open("css/flip-rtl.css","w")
    fliprtl.write(stache.render(stache.load_template("flip-style.css"),{ "dir" : "rtl", "side": "right", "oposide":"left", "even": "even", "odd": "odd"}).encode('utf-8')) 
    fliprtl.close()
    flipltr = open("css/flip-ltr.css","w")
    flipltr.write(stache.render(stache.load_template("flip-style.css"),{ "dir" : "ltr", "side": "left", "oposide":"right","even":"odd", "odd":"even"}).encode('utf-8')) 
    flipltr.close()
    logger.info(u"rendering book indices")
    
    # loop again to write book indexes
    for authdir in conf['authors'].iterkeys():
        authbooks = books.get_auth_books(authdir)
        for book in authbooks:
            bookdict = book.index_dict()
            if bookdict:
                if not os.path.exists(book.indexpath):
                    os.makedirs(book.indexpath)
                ind = open(book.indexpath+"index.php",'w')
                ind.write(stache.render(stache.load_template('index-template.html'),bookdict).encode('utf-8'))
                sc = open(book.indexpath+"bookscript.js", 'w')
                sc.write(stache.render(stache.load_template('bookscript.js'),bookdict).encode('utf-8'))
                logger.info(bookdict['book_shortname']+ " complete")
            else:
                logger.info(bookdict['book_shortname'] + " couldn't find pages")
        
        logger.info(authdir + " book indices complete")


