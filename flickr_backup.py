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
PAGES = 1000



#
# utility functions for dealing with flickr authentication
#
def get_text(nodelist):
	rc = ""
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc = rc + node.data
	return rc.encode("utf-8")

#
# get the frob based on our API_KEY and shared secret
#
def get_frob():
	# Create our signing string
	string = SHARED_SECRET + "api_key" + API_KEY + "methodflickr.auth.getFrob"
	hash = md5.new(string).digest().encode("hex")
	
	# Formulate the request
	url = "http://api.flickr.com/services/rest/?method=flickr.auth.getFrob"
	url += "&api_key=" + API_KEY + "&api_sig=" + hash
	
	try:
		# Make the request and extract the frob
		response = urllib2.urlopen(url)
		
		# Parse the XML
		dom = xml.dom.minidom.parse(response)
		
		# get the frob
		frob = get_text(dom.getElementsByTagName("frob")[0].childNodes)
		
		# Free the DOM 
		dom.unlink()
		
		# Return the frob
		return frob
		
	except:
		print "Could not retrieve frob"

#
# login and get a token
#
def frob_login(frob, perms):
	string = SHARED_SECRET + "api_key" + API_KEY + "frob" + frob + "perms" + perms
	hash = md5.new(string).digest().encode("hex")
	
	# Formulate the request
	url = "http://api.flickr.com/services/auth/?"
	url += "api_key=" + API_KEY + "&perms=" + perms
	url += "&frob=" + frob + "&api_sig=" + hash
	
	# Tell the user what's happening
	print "To authenticate with Flickr, you'll be directed here:"
	print url
	print "Waiting for you to press return"
	
	# We now have a login url, open it in a web-browser
	webbrowser.open_new(url)
	
	# Wait for input
	sys.stdin.readline()
	
	# Now, try and retrieve a token
	string = SHARED_SECRET + "api_key" + API_KEY + "frob" + frob + "methodflickr.auth.getToken"
	hash = md5.new(string).digest().encode("hex")
	
	# Formulate the request
	url = "http://api.flickr.com/services/rest/?method=flickr.auth.getToken"
	url += "&api_key=" + API_KEY + "&frob=" + frob
	url += "&api_sig=" + hash
	
	# See if we get a token
	try:
		# Make the request and extract the frob
		response = urllib2.urlopen(url)
		
		# Parse the XML
		dom = xml.dom.minidom.parse(response)
		
		# get the token and user-id
		token = get_text(dom.getElementsByTagName("token")[0].childNodes)
		nsid = dom.getElementsByTagName("user")[0].getAttribute("nsid")
		
		# Free the DOM
		dom.unlink()
		
		# Return the token and userid
		return (nsid, token)
	except:
		print "Login failed =["

# 
# sign an arbitrary Flickr request with a token
# 
def flickr_sign(url):
	token = CONFIG['token']
	query = urlparse.urlparse(url).query
	query += "&api_key=" + API_KEY + "&auth_token=" + token
	params = query.split('&') 
	
	# Create the string to hash
	string = SHARED_SECRET
	
	# Sort the arguments alphabettically
	params.sort()
	for param in params:
		string += param.replace('=', '')
	hash = md5.new(string).digest().encode("hex")
	
	# Now, append the api_key, and the api_sig args
	url += "&api_key=" + API_KEY + "&auth_token=" + token + "&api_sig=" + hash
	
	# Return the signed url
	return url

#
# Grab the photo from the server
#
def get_photo(id, filename):
	try:
		with open(filename) as f:
			print 'Photo ' + id + ' already downloaded'
			return filename
	except IOError as e:
		try:
			# contruct a request to find the sizes
			url = "http://api.flickr.com/services/rest/?method=flickr.photos.getSizes"
			url += "&photo_id=" + id
			
			# sign the request
			url = flickr_sign(url)
			
			# make the request
			response = urllib2.urlopen(url)
			
			# parse the XML
			dom = xml.dom.minidom.parse(response)
			
			# get the list of sizes
			sizes = dom.getElementsByTagName("size")
			
			# get the URL for the original if it exists
			if (sizes[-1].getAttribute("label") == "Original"):
				imgurl = sizes[-1].getAttribute("source")
			else:
				imgurl = sizes[-1].getAttribute("source")
				print "No original for photo " + id + ", getting largest available"
			
			# free the DOM memory
			dom.unlink()
			
			# grab the image file
			response = urllib2.urlopen(imgurl)
			data = response.read()
			
			# save the file!
			fh = open(filename, "w")
			fh.write(data)
			fh.close()
			print "Photo " + id + " now downloaded"
			return filename
		except:
			print "Failed to retrieve photo " + id

def flickr_frob_cache():
	global CONFIG # not going to go back and make a settings hash
	# see if we have a cached user and auth token
	try:
		cache = open('flickr_frob_cache.txt', 'r')
		CONFIG = cPickle.load(cache)
		cache.close()
		result = 'Read cache from previously existing file'
	# if not, make a new one
	except:
		(user, token) = frob_login(get_frob(), 'read')
		CONFIG = { 'version':1 , 'user':user, 'token':token }
		# Save it for future use
		cache = open('flickr_frob_cache.txt', 'w')
		cPickle.dump(CONFIG, cache)
		cache.close()
		result = 'Created new frob cache'
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
	url = flickr_sign(url)
	response = urllib2.urlopen(url)
	dom = xml.dom.minidom.parse(response)
	return dom

def get_stream_page(page, stream):
	extras = '&per_page=500' + '&page=' + str(page)
	dom = flickr_api_call('people', 'getPhotos', extras)
	stream.append(dom)
	global PAGES
	PAGES = int(dom.getElementsByTagName('photos')[0].getAttribute('pages'))
	print 'Getting stream page ' + str(page) + ' of ' + str(PAGES)
	return

def get_page_photos(stream_page):
	for photo in stream_page.getElementsByTagName('photo'): # [0:1]
		id = photo.getAttribute('id')
		print 'Processing photo ' + id
		photo_file = id + '.jpg'
		get_photo(id, photo_file)
		for keyword in ['info', 'contexts', 'comments', 'faves']:
			try:
				handle = open(id + '_' + keyword + '.xml', 'r')
				print 'Photo ' + id + ' already has ' + keyword + ' file'
				handle.close()
			except:
				handle = open(id + '_' + keyword + '.xml', 'w')
				data = get_photo_data(id, keyword)
				handle.write(data.toxml('utf-8'))
				print 'Photo ' + id + ' now has ' + keyword + ' file'
				data.unlink()
				handle.close()
	stream_page.unlink()
	return

def get_photo_data(id, keyword):
	id = str(id) # cast id as a string to be sure
	if keyword == 'comments':
		extras = '&photo_id=' + id
		response = flickr_api_call('photos', 'comments.getList', extras)
	if keyword == 'contexts':
		extras = '&photo_id=' + id
		response = flickr_api_call('photos', 'getAllContexts', extras)
	if keyword == 'faves':
		extras = '&photo_id=' + id + '&per_page=50'
		response = flickr_api_call('photos', 'getFavorites', extras)
	if keyword == 'info':
		extras = '&photo_id=' + id
		response = flickr_api_call('photos', 'getInfo', extras)
		# user = flickr_api_call('people', 'getInfo', '')
		# return user
	return response


def generate_index(stream_page, number):
	header = '''
<html>
	<head>
		<title>Flickr Backup</title>
		<style>
			html, body {
				margin: 0;
				padding: 0;
				width: 100%;
				min-height: 100%;
			}
			
			h2 {
				padding: 0.25em 0px;
				text-align: center;
				font-size: 4em;
			}
			
			img {
				width: 100%;
				display: block;
				margin: 0;
			}
		</style>
	</head>
	<body>
'''
	footer = '''
	</body>
</html>'''
	filename = 'page_' + str(number) + '.html'
	with open(filename, 'a') as index:
		index.write(header)
		for photo in stream_page.getElementsByTagName('photo'):
			id = photo.getAttribute('id')
			title = photo.getAttribute('title').encode('utf-8') or '[untitled]'
			img = '\t\t<img src="' + id + '.jpg" />\n'
			title = '\t\t<h2>' + title + '</h2>\n'
			index.write(title)
			index.write(img)
		index.write(footer)
		index.close()
	return

# main application
if __name__ == '__main__':
	# the first, and only argument needs to be a directory
	try:
		os.chdir(sys.argv[1])
		print 'Backing up your Flickr stream, welcome'
		print 'Your backup directory is: %s' % sys.argv[1]
	except:
		print 'Usage: %s [directory]' % sys.argv[0]
		sys.exit(1)
	
	flickr_frob_cache()
	
	# get user photo list
	stream = []
	stream_page = 1
	counter = 1
	while stream_page <= PAGES:
		get_stream_page(stream_page, stream)
		stream_page += 1
	for page in stream:
		get_page_photos(page)
		generate_index(page, counter)
		counter += 1
	print 'Backup complete =]'
