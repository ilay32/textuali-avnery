##book indexes

**run:** python make-in.py 

errors should explain themselves, usually they are due to faulty config.json
  * uses the language module
  * generates thumbnails available in this url: <textuali.com or authordomain>/texts/<author>/<book>/<front or back>-thumbnail.jpg
  * flip  styling:
    
    to overrride default styles use (create if needed) the following files:
     * for all <author> flips: /(dev)-texts/<author>/authorstyle.css

      * for particular <book>: /(dev)-texts/uri_avnery/\<book\>/bookstyle.css

  * to update the dev config json from the live one, use the update option:
    ** python make-in.py -u or python make-in.py --update-config

  * blocked pages json instructions:
    * blocked_message: general for author -- object with language code keys:
     
          "blocked_message" : {
            "he" : "עברית",
            "en" : "אנגלית"
          }

     * blocked -- array of two-valued array: 
     
           "blocked" : [ [1,10], [34,45] ] 
           
       meaning the blocked pages are 1 through 10 and 34 through 45.

##htm files  wrap script

**run:** python make-heads.py <author> [<book>]

the script will guide you if there are any errors

##generic site

**run:** python2.7 make-auth.py <author_directory>

* adittional html will be appended at the bottom of the <main> element common to all templates. the files for this are, in cascading override order:
  
  * SITEROOT/additional.html
  
  * SITEROOT/<lang>/additional.html
  
  * SITEROOT/<lang>/<pagename>-additional.html
 
except if the page block in siteconfig includes "no_additional" with any value

* if found, SITEROOT/footer.html will be appended inside a  <footer> tag after </main>


* an authors site diectory is (dev)-texts/<auhthor>/site -- this is SITEROOT

* the site is rendered with python and mustache as by a sitecofing.json.

* most data is stored in json files in the site directory but some depend on the language module and on the authors flip data: home/sidelang/webapps/phptextuali/textuali(-dev)/config.json

* a 420px thumbnail is generated automatically for the first slide of every slideshow. It is used in the slideshow page.

* siteconfig usage :
    
  * favicon -- enter file name and save it in SITEROOT/img. Defaults to textuali.com/media/favicon.ico
  
  * logo -- enter file name and save it in SITEROOT/img. Defaults to /img/logo-<langcode> where <langcode> is the page language, or 'he' for rtl and 'en' for ltr.
  
  * default image for facebook <og:image> tag -- save fbshare-default.whatever in site/img. If absent, the logo-<language> is used. If a page has
 "fbshare" (full url) entry specified, it overrides both of the above.

  * menu -- see comments in the json itself
  
  * social -- see comments in the json itself
  
  * bare slideshows -- a list of directories relative to SITEROOT/img. For each directory a slideshow will be rendered in all languages. To activate it use <a href="whatever" class="bare-slideshow" title="will go over the carousel" data-slideshow="id of slideshow from the bare_slideshows list mentioned above"></a>
    * pages -- see general comments in the json, but also:
      
      * general for all templates:
        
        * page_title -- see instructions in json
        
        * title_image -- relative to site img foler, if exists will float before the title text
        
        * description -- goes in meta description
        
        * label -- page name in menus
        
        * content -- save <pagename>-maintext.txt in the relevant language folder. will appear below the title.
           
      * templates:
        
        * isotope -- requires a SITEROOT/<lang>/<pagename>-isotope-blocks.json. see the json for instructions about block options
            defaults to siteconfig.primary_language/<pagename>-isotope-blocks.json
        
        * static -- requires a SITEROOT/<lang>/<page>-static.html -- good for arbitrary html
        
        * videos -- requires a SITEROOT/videos.json see instructions there
        
        * external (good for timelines too) -- requires a url dictionary where iframe urls are given per-language (defaults to the url.primary_language value)
        * books -- optional lists of exclusions:
          
          * by type : "exclude_types" : ["type1", "type2"...]
          
          * by id (folder): "exclude_ids": ["bookfolder1", "boookfolder2"...]
       
      * protocols --- requires a file_lists object in which
         
         * keys are names of csv files kept in texts/<author>/protocols
         
         * items are the lables for them
          
      * file_heap
      
        * requires:
          
          * heap_location -- name of directory containing the files relative to texts/<author>/
        
        * optional:
          
          * batch_size -- how many files per dropdown
          
          * batches_in_row -- how many batches should be bunched together in the same html element
       


##language module

* for language meta-data (the language name, it's directionality)

* for string translations common to many textuali pages ("by", "book", "page" etc.)

* directory:  home/sidelang/webapps/phptextuali/langs

* fill in what you like textuali-langs.json. it is self explanatory.

##directories report
To see current status regarding author backups, tif files, book folders sizes,
cd to phptextuali/texts and run:
./report > report.csv
you can then access that file with ftp or http://textuali.com/texts/report.csv
