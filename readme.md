# What

This Python script downloads all of your Flickr photos, and creates files containing their stats, comments, and other information.



# How

Create an app on Flickr by going to You > Your Apps or going here: http://www.flickr.com/services/apps/. This will provide you with an API key and shared secret.

Create a file in the same directory called flickr_keys.py which contains the following:

    API_KEY = "[your API key]"
    SHARED_SECRET = "[your shared secret]"

The .gitignore in the repo ignores this file so that you don't have to share this data with the whole world. Now you're set. Run the script like this:

    $ mkdir [backup folder]
    $ python flickr_backup.py [backup folder]

You'll be prompted to authorize with Flickr, and then the magic happens.



# Who

Forked by Peter Behr from Dan Benjamin's fork of Colm MacCárthaigh's original work, called FlickrTouchr. Nice.



# Why

The original forks this is based off went about the problem by taking all of your photosets and then downloading all of the photos contained therein, including photos not in any set. A fine approach, but also one that eliminates the stream, which to me is one of the most important aspects of the Flickr experience. So I went the other way, backing up all of the photos in your stream, and adding a file for each one with information about which sets it is in, and additional data like faves and comments from other users.

The philosophy is that from this raw data you can later manipulate it in various ways to reproduce sets, collections, and whatever else you want.