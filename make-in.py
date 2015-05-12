
import csv,json,urllib2,re,logging,sys,os,glob

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-in')

import pystache
stache = pystache.Renderer(
    search_dirs='.',file_encoding='utf-8',string_encoding='utf-8',file_extension='html'
)

from HTMLParser import HTMLParser
from PIL import Image
htmlparser = HTMLParser()
def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

if __name__=='__main__':
    conf = json.load(file('config.json'))
    execfile("../webconfig.py")
    logger.info(u"rendering front page")
    file('index.html','w').write(stache.render(stache.load_template('front-template'),conf).encode('utf-8'))
    logger.info(u"rendering book indices")
    #book_type_pattern = re.compile('"^([a-zA-Z])(\d)$"')
    for authorblock in conf['authors']:
        authdir = authorblock['dir']
        authbooks = authorblock['books']		
        authnicename = authorblock['nicename'];
        for book in authbooks:
            book['textsdir'] = conf['front']['textsdir']
            indexpath = book['textsdir']+"/"+authdir+"/"+book['bookdir']+"/"
            book['topdir'] = conf['front']['domain']
            book['coddir'] = book['topdir'] + conf['front']['coddir']
            book['authnice'] = authnicename
            jpgslist = sorted(glob.glob(indexpath+"jpg/*.jpg"))
            foundpages = len(jpgslist)
            book['type'] = conf['book_types'].get(book['bookdir'][:1],"book")
            if(foundpages > 0):
                logger.info(book['book_shortname'])
                if(os.path.isfile(book['textsdir']+"/"+authdir+"/authorstyle.css")):
                    book['has_author_css'] = 1
                if(os.path.isfile(indexpath+"bookstyle.css")):
                    book['has_book_css'] = 1
                if (folders.has_key(authdir+'-'+book['bookdir'])):
                    book['has_search'] = 1
                #book['pages'] = foundpages - 2 if book['hard_cover'] else  foundpages
                book['pages'] = foundpages
                book['page_list']= map((lambda uri : unescape(os.path.splitext(os.path.basename(uri))[0])),jpgslist)
                book['authdir'] = authdir
                book['frontjpg'] = os.path.basename(jpgslist[0])
                frontjpg = Image.open(jpgslist[0])
                fsize = frontjpg.size
                book['openbook_ratio'] = float(2*fsize[0])/fsize[1]
                f = open(indexpath+"index.html",'w')
                f.write(stache.render(stache.load_template('index-template'),book).encode('utf-8'))
                logger.info(book['book_shortname']+ " complete")
            else:
                logger.info(book['book_shortname'] + " couldn't find pages")
        
        logger.info(authdir + " book indices complete")


