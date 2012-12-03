import os
import xml.dom.minidom
import shutil

source_path = 'flickr_backup/' # fill this in
set_path = 'set/' # fill this in
docs = os.listdir(source_path)

for doc in docs:
	if 'contexts' in doc:
		id = doc[0:-13]
		#print 'Checking contexts for photo ' + id
		contexts = xml.dom.minidom.parse(source_path + doc)
		for photoset in contexts.getElementsByTagName('set'):
			if 'Sandblast' in photoset.getAttribute('title'):
				info = xml.dom.minidom.parse(source_path + id + '_info.xml')
				taken = info.getElementsByTagName('dates')[0].getAttribute('taken')
				taken = taken.replace(':', '').replace('-', '').replace(' ', '_')
				print taken
				shutil.copyfile(source_path + id + '.jpg', set_path + taken + '_' + id + '.jpg')