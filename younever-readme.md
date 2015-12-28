book indexes
============
* run: python make-in.py 
errors should explain themselves, usually they're due to faulty config.json
* uses the language module
* generates thumbnails available in this url: <textuali.com or authordomain>/texts/<author>/<book>/<front or back>-thumbnail.jpg
* flip  styling: 
to overrride default styles use (create if needed) the following files:
    ** for all <author> flips:
    .../(dev)-texts/<author>/authorstyle.css
    ** for particular <book>:
    .../(dev)-texts/uri_avnery/\<book\>/bookstyle.css
* to update the dev config json from the live one, use the update option:
    ** python make-in.py -u or python make-in.py --update-config

htm files  wrap script
======================
run: python make-heads.py <author> [<book>]
the script will guide you if there are any errors

generic site
================
* an author's site diectory is (dev)-texts/<auhthor>/site -- this is SITEROOT
* the site is rendered with python and mustache as by a sitecofing.json.
* most data is stored in json files in the site directory but some depend on the language module and on the authors flip data: home/sidelang/webapps/phptextuali/textuali(-dev)/config.json
* a 420px thumbnail is generated automatically for the first slide of every slideshow. It is used in the slideshow page.
* siteconfig usage :
    ** favicon -- enter file name and save it in SITEROOT/img. Defaults to textuali.com/media/favicon.ico
    ** logo -- enter file name and save it in SITEROOT/img. Defaults to /img/logo-<langcode> where <langcode> is the page language, or 'he' for rtl and 'en' for ltr.
    ** default image for facebook <og:image> tag -- save fbshare-default.whatever in site/img. If absent, the logo-<language> is used. If a page has
    an "fbshare" (full url) entry specified, it overrides both of the above.
    ** menu -- see comments in the json itself 
    ** social -- see comments in the json itself 
    ** pages -- see general comments in the json, but also: 
        *** templates:
            **** isotope -- requires a SITEROOT/<lang>/<pagename>-isotope-blocks.json. see the json for instructions about block options
            defaults to siteconfig.primary_language/<pagename>-isotope-blocks.json
            **** static -- requires a SITEROOT/<lang>/<page>-static.html -- good for arbitrary html
            
            **** videos -- requires a SITEROOT/videos.json see instructions there
            **** external (good for timelines too) -- requires a url dictionary where iframe urls are given per-language (defaults to the url.primary_language value)
            **** books -- optional lists of exclusions:
                ***** by type : "exclude_types" : ["type1", "type2"...]
                ***** by id (folder): "exclude_ids": ["bookfolder1", "boookfolder2"...]
       
* dittional html will be appended at the bottom of the <main> element common to all templates. the files for this are, in cascading override order:
    *** SITEROOT/additional.html
    *** SITEROOT/<lang>/additional.html
    *** SITEROOT/<lang>/<pagename>-additional.html
except if the page block in siteconfig includes "no_additional" with any value

* if found, SITEROOT/footer.html will be appended inside a  <footer> tag after </main>


* run: python2.7 make-auth.py <author_directory>

language module
===============
* for language meta-data (the language name, it's directionality)
* for string translations common to many textuali pages ("by", "book", "page" etc.)
* directory:  home/sidelang/webapps/phptextuali/langs
* fill in what you like textuali-langs.json. it is self explanatory.

directories report
==================
To see current status regarding author backups, tif files, book folders sizes,
cd to phptextuali/texts and run:
./report > report.csv
you can then access that file with ftp or http://textuali.com/texts/report.csv
