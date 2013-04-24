__author__ = 'Alexander'
import PyQt4
import os

TEMP_DIR = 'temp'

class userListItem(PyQt4.QtGui.QListWidgetItem):
    def __init__(self, user, parent):
        self.user = user

        try:
            self.filename = parent.api.download_res(self.user['photo'])
        except:
            self.filename = 'resources\\blank.gif'

        text = self.user['first_name']+' '+self.user['last_name']
        self.itemid = self.user['uid']

        super(userListItem, self).__init__(text)


class friendsListItem(PyQt4.QtGui.QListWidgetItem):
    def __init__(self, friend, parent):
        self.friend = friend

        try:
            self.filename = parent.api.download_res(self.friend['photo'])
        except:
            self.filename = 'resources\\blank.gif'

        text = self.friend['first_name']+' '+self.friend['last_name']
        self.itemid = self.friend['uid']

        super(friendsListItem, self).__init__(text)


class groupsListItem(PyQt4.QtGui.QListWidgetItem):
    def __init__(self, group, parent):
        self.group = group

        try:
            self.filename = parent.api.download_res(self.group['photo'])
        except:
            self.filename = 'resources\\blank.gif'

        text = group['name']
        self.itemid = self.group['gid']

        super(groupsListItem, self).__init__(text)


class albumsListItem(PyQt4.QtGui.QListWidgetItem):
    def __init__(self, album, parent):
        self.album = album

        try:
            self.filename = parent.api.download_res(self.album['thumb_src'])
        except:
            self.filename = 'resources\\blank.gif'

        text = album['title']
        self.itemid = self.album['aid']

        super(albumsListItem, self).__init__(text)
        self.setCheckState(0)


class photosListItem(PyQt4.QtGui.QListWidgetItem):
    def __init__(self, album, photo, parent):
        self.album = album
        self.photo = photo

        try:
            self.filename = parent.api.download_res(self.photo['src'])
        except :
            self.filename = 'resources\\blank.gif'

        self.itemid = photo['pid']

        super(photosListItem, self).__init__('')
        self.setCheckState(2)