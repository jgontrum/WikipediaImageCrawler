### Written by Johannes Gontrum (gontrum@vogelschwarm.com)
### See my website at vogelschwarm.com to read the tutorials I wrote to describe this script.
### And here is my GitHub page: https://github.com/jgontrum/
### Twitter: @motivationsara
###
### This small scripts returns the URLs of all images that are linked in pages on
### Wikipedia wich belong recursvly to a defined category.

import wikitools
import urllib2
import urllib
import math

from wikitools import wiki
from wikitools import api

verbose = True
debug = True

page_blacklist = ['disease', 'extinct', 'described', 'list', 'pets', 'location', 'anatomy', 'fictional']
image_blacklist = ['commons', 'wiki', 'svg', 'ogv,', 'png', 'ogg']

def checkBlacklist(item, blacklist):
    for blackword in blacklist:
        if blackword in item:
            return False
    return True

# create a Wiki object
site = wiki.Wiki("http://en.wikipedia.org/w/api.php") 


def cleanURLs(images):
    ret = []

    for url in images:
        good = True
        if checkBlacklist(url, image_blacklist):
            ret.append(url)

    return ret

def crawlCategory(category, ctype, pageIDs):
    continue_value = ""
    # First, crawl the pages that belong directly to this category
    while continue_value != None:
        params = {  
                'format':'json',    
                'action':'query',
                'list':'categorymembers',
                ctype:category,
                'cmtype':'page',
                'cmlimit':100,
                'continue' :  "",
                'cmcontinue' : continue_value
                }

        page_result = api.APIRequest(site, params).query()

        if 'query' in page_result and 'categorymembers' in page_result['query']:
            for page in page_result['query']['categorymembers']:
                if checkBlacklist(page['title'].encode('ascii', 'ignore').lower(), page_blacklist):
                    if verbose:
                        print "Found page: ", page['pageid'], ' = ', page['title'].encode('ascii', 'ignore')
                    pageIDs.append(str(page['pageid']))

        # Set new continue_value
        if ( 'continue' in page_result and
             'cmcontinue' in page_result['continue'] ):

            continue_value = page_result['continue']['cmcontinue']
        else:
            continue_value = None # leave the loop, no more data coming
    # !while (pages)


    continue_value = ""
    # Now, continue the recursion with all subcategories
    while continue_value != None:
        params = {  
                'format':'json',    
                'action':'query',
                'list':'categorymembers',
                ctype:category,
                'cmtype':'subcat',
                'cmlimit':100,
                'continue' :  "",
                'cmcontinue' : continue_value
                }

        subcat_result = api.APIRequest(site, params).query()

        if 'query' in page_result and 'categorymembers' in page_result['query']:
            for subcat in subcat_result['query']['categorymembers']:
                if checkBlacklist(subcat['title'].encode('ascii', 'ignore').lower(), page_blacklist):
                    if verbose:
                        print "Found category: ", subcat['title'].encode('ascii', 'ignore')
                    crawlCategory(subcat['pageid'], 'cmpageid', pageIDs)

        # Set new continue_value
        if ( 'continue' in page_result and
             'cmcontinue' in page_result['continue'] ):

            continue_value = page_result['continue']['cmcontinue']
        else:
            continue_value = None # leave the loop, no more data coming




def fetchImages(pages, images):
    step = 100
    for i in range(0, len(pages), step):
        if (i / len(pages)) % 10 == 0:
            print str(int(math.ceil((i / float(len(pages))) * 100))), "%"

        pids = "|".join(pages[i:i+step])
        continue_value = ""

        # Get all images for the current page
        while continue_value != None:
            params = {  
                    'format':'json',    
                    'action':'query',
                    'pageids':pids,
                    'prop':'images',
                    'imlimit':500,
                    'continue' : "",
                    }
            if not continue_value == "":
                params['imcontinue'] = continue_value

            image_result = api.APIRequest(site, params).query()

            if 'query' in image_result and 'pages' in image_result['query']:
                for page in image_result['query']['pages']:
                    if 'images' in image_result['query']['pages'][page]:
                        for image in image_result['query']['pages'][page]['images']:
                            images.append(image['title'])

            # Set new continue_value
            if 'continue' in image_result and 'imcontinue' in image_result['continue']:
                continue_value = image_result['continue']['imcontinue']
            else:
                continue_value = None # leave the loop, no more data coming



def getImageURL(images, urls):
    step = 50
    for i in range(0, len(images), step):
        url_query = "|".join(images[i:i+step])
    
        # Get all URLS
        params = {
                    "format":"json", 
                    "action":"query", 
                    "prop":"imageinfo",
                    "iiprop":"url",
                    "continue":"",
                    "titles":url_query
                 }

        image_result = api.APIRequest(site, params).query()

        try:
            for page in image_result['query']['pages']:
                if 'imageinfo' in image_result['query']['pages'][page]:
                    for image in image_result['query']['pages'][page]['imageinfo']:
                        urls.append(image['url'])
        except Exception, e:
            print "Error getting URL: ",e
            continue



##~~~~~~~~~~~~~~~~~~~~~~~~~~~~
pids = []         #< page IDs 
image_names = []  #< image names
urls = []         #< list of complete urls, ready to be downloaded

crawlCategory('Category:Rodents', 'cmtitle', pids)
#crawlCategory('Category:Callosciurus', 'cmtitle', pids)

if verbose: 
    print "Getting images for all pages..."

fetchImages(pids, image_names)

lookup_urls = cleanURLs(set(image_names))

getImageURL(lookup_urls, urls)


print "Done."
print "Found ", len(pids), " pages."
print "Found ",len(image_names), " images."
print "Found ",len(lookup_urls), " good images."
print "Found ",len(set(urls)), " URLS."

download_link_file = open('links.txt', 'w')
for p in urls:
    download_link_file.write(p + "\n")
