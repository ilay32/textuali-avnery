
import csv,json,re,logging,sys,os,glob,pystache,textualangs,optparse,random,textualibooks,errno,shutil,zipfile
from HTMLParser import HTMLParser
from PIL import Image
from webconfig import folders
logging.basicConfig(level=logging.DEBUG) 
logger=logging.getLogger('make-in')


stache = pystache.Renderer(search_dirs='book_templates',file_encoding='utf-8',string_encoding='utf-8',file_extension=False)

htmlparser = HTMLParser()
op = optparse.OptionParser()
op.add_option("-u", "--update-config", action="store_true", dest="update_config", help="copy the config.json file from ../textuali")
op.add_option("-a", "--author", action="store", dest="author", help="render indexes only for specified author")
op.add_option("-p", "--pack", action="store_true", dest="pack", help="create export package")

def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for f in files:
            file_location = os.path.join(root, f)
            ziph.write(file_location, os.path.relpath(file_location, os.path.join(path, '..')))

def convert_to_export(data,pack_data,path):
    data['packing'] = True
    data['front']['domain'] = os.path.join(pack_data['domain'],pack_data['root'])
    #data['front']['coddir'] = pack_data['root']
    data['indices_dir'] = None
    data['srcs'] = os.path.join(pack_data['domain'],pack_data['root'],data['bookdir'])
    data['write_index_to'] = os.path.join(path,data['bookdir'],'index.html') 
    data['write_script_to'] = os.path.join(path,data['bookdir'],'bookscript.js')
    return data


if __name__=='__main__':
    conf = json.load(file('config.json'))
    (options, args) = op.parse_args()
    packing = False
    auth = options.author
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
    fliprtl = open("../css/flip-rtl.css","w")
    fliprtl.write(stache.render(stache.load_template("flip-style.css"),{
        "dir" : "rtl", 
        "side": "right", 
        "oposide":"left", 
        "even": "even", 
        "odd": "odd"
    }).encode('utf-8')) 
    fliprtl.close()
    flipltr = open("../css/flip-ltr.css","w")
    flipltr.write(stache.render(stache.load_template("flip-style.css"),{
        "dir" : "ltr", 
        "side": "left",
        "oposide":"right",
        "even":"odd",
        "odd":"even"
    }).encode('utf-8')) 
    flipltr.close()

    if options.pack:
        if auth == None:
            quit("can't pack all authors. please run again with -pa <author>")
        elif not os.path.isdir(os.path.join(conf['front']['indices_dir'],auth)):
            quit("can't find author: "+auth+" please try again")
        else:  
            packing = True
            auth = options.author
            pack_params = {
                "root" : "fliptexts",
            }
            pack_params.update(conf['authors'][auth]['pack'])
            packagehouse = os.path.join(conf['front']['indices_dir'],auth,pack_params['root'])
            if os.path.isdir(packagehouse):
                shutil.rmtree(packagehouse)
            os.makedirs(packagehouse)
    
    logger.info(u"rendering book indices")
    
    doing = conf['authors'].iterkeys() if auth == None else [auth]
    for authdir in doing:
        authbooks = books.get_auth_books(authdir)
        for book in authbooks:
            bookdict = book.index_dict()
            if bookdict:
                if not os.path.exists(book.indexpath):
                    os.makedirs(book.indexpath)
                if packing:
                    logger.info("packing "+auth)
                    bookdict = convert_to_export(bookdict,pack_params,packagehouse)    
                    shutil.copytree(os.path.join(conf['front']['srcs_dir'],auth,bookdict['bookdir']), \
                    os.path.join(packagehouse,bookdict['bookdir']), ignore=shutil.ignore_patterns('*.php','*.tif','_*'))
                ind = open(bookdict['write_index_to'],'w')
                ind.write(stache.render(stache.load_template('index-template.html'),bookdict).encode('utf-8'))
                ind.close()
                sc = open(bookdict['write_script_to'], 'w')
                sc.write(stache.render(stache.load_template('bookscript.js'),bookdict).encode('utf-8'))
                sc.close()
                logger.info(bookdict['book_shortname']+ " complete")
            else:
                logger.info(bookdict['book_shortname'] + " couldn't find pages")
        logger.info(authdir + " book indices complete")
        if packing :
            logger.info("zipping and cleaning up")
            shutil.copytree('../media',packagehouse+'/media')
            shutil.copytree('../vendor',packagehouse+'/vendor')
            shutil.copytree('../bootstrap',packagehouse+'/bootstrap')
            shutil.copytree('../css',packagehouse+'/css')
            zfname = auth+'.zip'
            
            if os.path.isfile(zfname):
                os.remove(zfname)
            zipf = zipfile.ZipFile(zfname, 'w', zipfile.ZIP_DEFLATED)
            zipdir(packagehouse,zipf)
            logger.info("zip contnenents:")
            zipf.printdir()
            zipf.close() 
            
            if zipfile.is_zipfile(zfname):
                if os.path.isfile('../'+zfname):
                    os.remove('../'+zfname)
                shutil.rmtree(packagehouse)
                shutil.move(zfname,'../')
                logger.info("zip ready for download at textuali.com/"+auth+'.zip')
            else:
                logger.warning("could not zip, please zip and then remove the package directory manually")

