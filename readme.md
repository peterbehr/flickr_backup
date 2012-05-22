# What

This Python script downloads all of your Flickr photos, and creates files containing their stats, comments, and other information.



# How

Create an app on Flickr by going to You > Your Apps or going here: http://www.flickr.com/services/apps/. This will provide you with an API key and shared secret.

Create a file in the same directory called flickr_keys.py which contains the following:

    API_KEY = "[your API key]"
    SHARED_SECRET = "[your shared secret]"

Now you're set. Run the script like this:

    $ mkdir [backup folder]
    $ python flickr_backup.py [backup folder]

You'll be prompted to authorize with Flickr, and then the magic happens.



# Who

Forked by Peter Behr from Dan Benjamin's fork of Colm MacCárthaigh's original work, called FlickrTouchr. Nice.
