#!/usr/bin/env python

import xml.dom.minidom
import webbrowser
import urlparse
import urllib2
import unicodedata
import cPickle
import md5
import sys
import os

import flickr_keys

API_KEY = flickr_keys.API_KEY
SHARED_SECRET = flickr_keys.SHARED_SECRET
CONFIG = {}
HTML = ''



#
# Utility functions for dealing with flickr authentication
#
def getText(nodelist):
    rc = ""
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc.encode("utf-8")

#
# Get the frob based on our API_KEY and shared secret
#
def getfrob():
    # Create our signing string
    string = SHARED_SECRET + "api_key" + API_KEY + "methodflickr.auth.getFrob"
    hash   = md5.new(string).digest().encode("hex")

    # Formulate the request
    url    = "http://api.flickr.com/services/rest/?method=flickr.auth.getFrob"
    url   += "&api_key=" + API_KEY + "&api_sig=" + hash

    try:
        # Make the request and extract the frob
        response = urllib2.urlopen(url)
    
        # Parse the XML
        dom = xml.dom.minidom.parse(response)

        # get the frob
        frob = getText(dom.getElementsByTagName("frob")[0].childNodes)

        # Free the DOM 
        dom.unlink()

        # Return the frob
        return frob

    except:
        raise "Could not retrieve frob"

#
# Login and get a token
#
def froblogin(frob, perms):
    string = SHARED_SECRET + "api_key" + API_KEY + "frob" + frob + "perms" + perms
    hash   = md5.new(string).digest().encode("hex")

    # Formulate the request
    url    = "http://api.flickr.com/services/auth/?"
    url   += "api_key=" + API_KEY + "&perms=" + perms
    url   += "&frob=" + frob + "&api_sig=" + hash

    # Tell the user what's happening
    print "To authenticate with Flickr, you'll be directed here:"
    print
    print url
    print 
    print "Waiting for you to press return"

    # We now have a login url, open it in a web-browser
    webbrowser.open_new(url)

    # Wait for input
    sys.stdin.readline()

    # Now, try and retrieve a token
    string = SHARED_SECRET + "api_key" + API_KEY + "frob" + frob + "methodflickr.auth.getToken"
    hash   = md5.new(string).digest().encode("hex")
    
    # Formulate the request
    url    = "http://api.flickr.com/services/rest/?method=flickr.auth.getToken"
    url   += "&api_key=" + API_KEY + "&frob=" + frob
    url   += "&api_sig=" + hash

    # See if we get a token
    try:
        # Make the request and extract the frob
        response = urllib2.urlopen(url)
    
        # Parse the XML
        dom = xml.dom.minidom.parse(response)

        # get the token and user-id
        token = getText(dom.getElementsByTagName("token")[0].childNodes)
        nsid  = dom.getElementsByTagName("user")[0].getAttribute("nsid")

        # Free the DOM
        dom.unlink()

        # Return the token and userid
        return (nsid, token)
    except:
        raise "Login failed. =["

# 
# Sign an arbitrary flickr request with a token
# 
def flickrsign(url):
    token = CONFIG['token']
    query  = urlparse.urlparse(url).query
    query += "&api_key=" + API_KEY + "&auth_token=" + token
    params = query.split('&') 

    # Create the string to hash
    string = SHARED_SECRET
    
    # Sort the arguments alphabettically
    params.sort()
    for param in params:
        string += param.replace('=', '')
    hash   = md5.new(string).digest().encode("hex")

    # Now, append the api_key, and the api_sig args
    url += "&api_key=" + API_KEY + "&auth_token=" + token + "&api_sig=" + hash
    
    # Return the signed url
    return url

#
# Grab the photo from the server
#
def getphoto(id, filename):
    try:
        # Contruct a request to find the sizes
        url  = "http://api.flickr.com/services/rest/?method=flickr.photos.getSizes"
        url += "&photo_id=" + id
    
        # Sign the request
        url = flickrsign(url)
    
        # Make the request
        response = urllib2.urlopen(url)
        
        # Parse the XML
        dom = xml.dom.minidom.parse(response)
        
        # Get the list of sizes
        sizes =  dom.getElementsByTagName("size")

        # Grab the original if it exists
        if (sizes[-1].getAttribute("label") == "Original"):
          imgurl = sizes[-1].getAttribute("source")
        else:
            imgurl = sizes[-1].getAttribute("source")
            print "Failed to get original for photo " + id

        # Free the DOM memory
        dom.unlink()

        # Grab the image file
        response = urllib2.urlopen(imgurl)
        data = response.read()
    
        # Save the file!
        fh = open(filename, "w")
        fh.write(data)
        fh.close()
        return "Saved photo " + filename
        return filename
    except:
        print "Failed to retrieve photo " + id

def flickr_frob_cache():
    global CONFIG # not going to go back and make a settings hash
    # First things first, see if we have a cached user and auth-token
    try:
        cache = open('flickr_frob_cache.txt', 'r')
        CONFIG = cPickle.load(cache)
        cache.close()
        result = 'Read cache from previously existing file.'
    # We don't - get a new one
    except:
        (user, token) = froblogin(getfrob(), 'read')
        CONFIG = { 'version':1 , 'user':user, 'token':token }
        # Save it for future use
        cache = open('flickr_frob_cache.txt', 'w')
        cPickle.dump(CONFIG, cache)
        cache.close()
        result = 'Created new frob cache.'
    print result
    return CONFIG

def flickr_api_call(domain, method, extras):
    url = 'http://api.flickr.com/services/rest/?method=flickr.'
    url += domain
    url += '.'
    url += method
    url += '&user_id='
    url += CONFIG['user']
    url += extras
    url = flickrsign(url)
    response = urllib2.urlopen(url)
    dom = xml.dom.minidom.parse(response)
    return dom

def get_stream_page(page, stream):
    extras = '&per_page=500' + '&page=' + str(page)
    dom = flickr_api_call('people', 'getPhotos', extras)
    stream.append(dom)
    stream_pages = int(dom.getElementsByTagName('photo')[0].parentNode.getAttribute('pages'))
    # do stuff for each photo
    for photo in dom.getElementsByTagName('photo')[0:1]:
        id = photo.getAttribute('id')
        print 'Processing photo ' + id
        info = get_photo_info(id)
        contexts = get_photo_contexts(id)
        comments = get_photo_comments(id)
        # print comments.getElementsByTagName('comments')
        faves = get_photo_faves(id)
        # print faves.getElementsByTagName('person').toxml()
        photo_file = id + '.jpg'
        getphoto(id, photo_file)
        data_file = id + '.txt'
        metadata = '<?xml version="1.0" ?>'
        
        comments.unlink()
        faves.unlink()
        info.unlink()
        contexts.unlink()
    dom.unlink()
    return

def get_photo_comments(id):
    extras = '&photo_id=' + id
    response = flickr_api_call('photos', 'comments.getList', extras)
    # form <comments><comment></comment></comments>
    # validate that the request succeeded
    # there should be a log
    return response

def get_photo_contexts(id):
    extras = '&photo_id=' + id
    response = flickr_api_call('photos', 'getAllContexts', extras)
    return response

def get_photo_faves(id):
    extras = '&photo_id=' + id + '&per_page=50'
    response = flickr_api_call('photos', 'getFavorites', extras)
    # <photo><person></person></photo>
    return response

def get_photo_info(id):
    extras = '&photo_id=' + id
    response = flickr_api_call('photos', 'getInfo', extras)
    return response

def get_user_data():
    user = flickr_api_call('people', 'getInfo', '')
    return user
    
# http://www.flickr.com/services/api/flickr.photosets.comments.getList.html
# http://www.flickr.com/services/api/flickr.photosets.getInfo.html

######## Main Application ##########
if __name__ == '__main__':
    # The first, and only argument needs to be a directory
    try:
        os.chdir(sys.argv[1])
    except:
        print 'Usage: %s [directory]' % sys.argv[0]
        sys.exit(1)
    
    config = flickr_frob_cache()
    
    stream = []
    # get user photo list
    stream_pages = stream_page = 1
    stream_pages_counted = False
    while stream_page <= stream_pages:
        get_stream_page(stream_page, stream)
        stream_page += 1
    
    # # this file will contain all photo nodes, overwritten if exists
    # photos = open('index.xml', 'w')
    
    # photos.close()