import re, json,logging,os,pystache,textualibooks,sys

logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-heads')
stache = pystache.Renderer(search_dirs='.',file_encoding='utf-8',string_encoding='utf-8',file_extension=False)

headp = re.compile("^.*<\s*div.*class=\"pagelive\"\s*>",re.DOTALL)
tailp = re.compile("<\s*\/\s*body\s*>.*$",re.DOTALL)
yespat = re.compile("^y(es)?$",re.IGNORECASE)
  
def make_heads(textualibook,bookhtmls):
    for filename in os.listdir(bookhtmls):
        htmfile = bookhtmls+"/"+filename
        if os.path.isfile(htmfile):
            with open(htmfile,'r+') as t:
                top = re.sub(headp,stache.render(stache.load_template('htmhead.html'),textualibook.htm_template_data(filename)).encode('utf-8').rstrip(),t.read())
                w = ""
                if re.match(tailp,top) :
                    w = re.sub(tailp,'</body>\n</html>',top)
                else:
                    w = top+'</body>\n</html>' 
                t.seek(0)
                t.write(w)
                t.truncate()
                t.close()
    
            logger.info(filename+" done")

def fix_book_htms(authid,bookid,conf):
    htmpath = os.path.join(conf['front']['srcs_dir'],authid+"/"+bookid+"/html")
    if not os.path.exists(htmpath):
        logger.info("can't find htmls in "+authid+" "+bookid)
        return
    book = textualibooks.TextualiBook(bookid,authid,conf)
    make_heads(book,htmpath)     

if __name__=='__main__':
    args = sys.argv[1:]
    conf = json.load(file('config.json'))
    if len(args) < 1  or len(args) > 2:
        print("usage: python make-auth.py <author> [<book>]")
        quit()
    
    authid = args[0]
    
    if authid not in conf['authors']:
        logger.error("sorry "+authid+" is not listed in config.json")
        quit()

    if len(args) == 1:
        conti = raw_input("run the wrap script on all "+authid+" files Y/N? ")
        if re.match(yespat,conti):
            for bookid in conf['authors'][authid]['books'].iterkeys():
                fix_book_htms(authid,bookid,conf)    
    else:
        bookid = args[1]
        conti = raw_input("run the wrap script only on "+authid+" "+bookid+"? ")
        if re.match(yespat,conti):
           fix_book_htms(authid,bookid,conf)
