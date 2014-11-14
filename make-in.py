
import csv,json,urllib2,re,logging,sys,os,glob


logging.basicConfig(level=logging.DEBUG) # maybe do syslog, mail, or something fancier later on
logger=logging.getLogger('make-in')

import pystache
stache = pystache.Renderer(
    search_dirs='.',file_encoding='utf-8',string_encoding='utf-8',file_extension='html'
)

#item_filter = json.load(file(ITEM_FILTER_FILE))

from HTMLParser import HTMLParser
htmlparser = HTMLParser()
def unescape(s):
    return htmlparser.unescape(s).encode('utf-8')

RE_POST_URL = re.compile('"http://no2bio.org/([^/".]*)/?"')
def _post_url_handler(m):
    slug = m.group(1)
    if slug in item_filter['no-url-conversion']:
        return '"{0}.html"'.format(slug)
    return '"post-{0}.html"'.format(slug)
def _tweak_post_urls(s):
    return RE_POST_URL.sub(_post_url_handler,s)

def _make_item(keys,row):
    item = {}
    for k,v in zip(keys,row):
        item[k]=v
    return item

def _item_by_id(menu,item_id):
    for item in menu['items']:
        if item['id'] == item_id:
            return item
        if item.get('items'):
            found = _item_by_id(item,item_id)
            if found:
                return found
    return None

def _load_category(slug):
    logger.info( u"getting category: {0}".format(slug))
    return json.load(urllib2.urlopen(u'{0}/get_category_posts?slug={1}&count=666'.format(API_URL,slug)))

def hilite_menu(menu,path):
    for m in menu.get('items',[]):
        _hilite_menu_aux(m,path)
def _hilite_menu_aux(menu,path):
    if path and menu.get('id')==path[0]:
        menu['active'] = True
        for m in menu.get('items',[]):
            _hilite_menu_aux(m,path[1:])
    else:
        menu['active'] = False
        for m in menu.get('items',[]):
            _hilite_menu_aux(m,[])

#def make_menu(csv_filename=CSV_FILENAME):
#    menu = {'type':'submenu','items':[],'path':[]}
#    categories = {}
#    table = csv.reader(file(CSV_FILENAME))
#    keys = table.next()
#    for r in table:
#        item = _make_item(keys,r)
#        parent = item['parent'] and _item_by_id(menu,item['parent']) or menu
#        item['path'] = parent['path']+[item['id']]
#        parent['items'].append(item)
#        if item['type']=='submenu':
#            item['ismenu'] = True # mustache needs this
#            item['items'] = []
#        if item['type']=='category':
#            item['ismenu'] = True # mustache needs this
#            cat = _load_category(item['id'])
#            posts = filter(lambda x:not x['slug'] in item_filter['ignore-slugs'],cat['posts'])
#            first = filter(lambda x: x['slug']==item['arg'],posts)
#            rest = filter(lambda x: x['slug']!=item['arg'],posts)
#            posts = first+sorted(rest,key=lambda x:x['title'])
#            item['items'] = [{
#              'id':p['slug'],
#              'path':item['path']+[p['slug']],
#              'name':unescape(p['title']),
#              'type':'post',
#              'parent':item['id'],
#              'url':u'post-{0}.html'.format(p['slug'])
#            } for p in posts]
#            categories[item['id']] = posts
#        elif item['type'] in ['homepage','iframe']:
#            item['url']=item['id']+'.html'
#    return menu,categories
#
#def render_posts(menu,categories):
#    for cat in categories:
#        for post in categories[cat]:
#            post['title']=unescape(post['title'])
#            post['content']=_tweak_post_urls(post['content'])
#            current = _item_by_id(menu,post['slug'])
#            hilite_menu(menu,current['path'])
#            menuhtml = stache.render(stache.load_template('menu'),menu).encode('utf-8')
#            filename = '/'.join((OUTPUT_DIR,current['url']))
#            logger.info(filename)
#            file(filename,'w').write(
#                stache.render(stache.load_template('post'),post,menu=menuhtml).encode('utf-8'))
#            
#def render_non_posts(root,current=None):
#    if not current: current = root
#    if current['type']=='submenu':
#        logger.debug('submenu: '+current.get('id','(root)'))
#        for item in current.get('items',[]):
#           render_non_posts(root,item)
#    elif current['type'] in ['iframe','homepage']:
#        hilite_menu(root,current['path'])
#        menuhtml = stache.render(stache.load_template('menu'),root).encode('utf-8')
#        filename = '/'.join((OUTPUT_DIR,current['url']))
#        logger.info(filename)
#        file(filename,'w').write(
#            stache.render(stache.load_template(current['type']),{
#                'menu':menuhtml, 'item':current
#            }).encode('utf-8'))
#

if __name__=='__main__':
	#menu,categories = make_menu()
	#print json.dumps(menu,indent=1)
	#print json.dumps(categories,indent=1)
	#render_posts(menu,categories)
	#render_non_posts(menu)
	conf = json.load(file('config.json'))
    #logger.info(u"rendering front page")
	file('index.html','w').write(stache.render(stache.load_template('front-template'),conf).encode('utf-8'))
	logger.info(u"rendering book indices")	
	for authorblock in conf['authors'] :	
		authdir = authorblock['dir']
		authbooks = authorblock['books']		
		for book in authbooks:
			indexpath = conf['front']['textsdir']+"/"+authdir+"/"+book['bookdir']+"/"							
			book['topdir'] = conf['front']['domain']		
			book['coddir'] = book['topdir'] + conf['front']['coddir'] 		
			jpgslist = sorted(glob.glob(indexpath+"jpg/*.jpg"))
			foundpages = len(jpgslist)
			if(foundpages > 0):
				book['pages'] = foundpages
				book['frontjpg'] = os.path.basename(jpgslist[0])			
				f = open(indexpath+"index.html",'w')
				f.write(stache.render(stache.load_template('index-template'),book).encode('utf-8'))
	logger.info(u"complete")


