book indexes
============
* run: python make-in.py 
errors should explain themselves, usually they're due to faulty config.json
* uses the language module
* flip  styling: 
to overrride default styles use (create if needed) the following files:
    ** for all <author> flips:
    .../(dev)-texts/<author>/authorstyle.css
    ** for particular <book>:
    .../(dev)-texts/uri_avnery/\<book\>/bookstyle.css
* to update the dev config json from the live one, use the update option:
    ** python make-in.py -u or python make-in.py --update-config

generic site
================
* an author's site diectory is (dev)-texts/<auhthor>/site -- this is SITEROOT
* the site is rendered with python and mustache as by a sitecofing.json.
* most data is stored in json files in the site directory but some depend on the language module and on the authors flip data: home/sidelang/webapps/phptextuali/textuali(-dev)/config.json
* siteconfig usage :
    ** menu -- see comments in the json itself 
    ** social -- see comments in the json itself 
    ** pages -- see general comments in the json, but also: 
        *** templates:
            **** isotope -- requires an isotope-blocks.json in SITEROOT/<lang>/. see the json for instructions about block options
            **** static -- requires a SITEROOT/<lang>/<page>-static.html -- good for arbitrary html
            **** timeline -- requires a SITEROOT/timeline.json see instructions there
            **** videos -- requires a SITEROOT/videos.json see instructions there
            **** external -- requires a url object where iframes urls are given per-language
       
* any SITEROOT/<lang>/<page>-adittional.html will be appended at the bottom of the <main> element common to all templates.
* run: python2.7 make-auth.py <author_directory>

language module
===============
* for language meta-data (the language name, it's directionality)
* for string translations common to many textuali pages ("by", "book", "page" etc.)
* directory:  home/sidelang/webapps/phptextuali/langs
* fill in what you like textuali-langs.json. it is self explanatory.
