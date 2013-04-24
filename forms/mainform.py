__author__ = 'Alexander'
from PyQt4 import QtGui, uic, QtCore
import os
import re
import ctypes
import threading
from resources import resourcefile
from modules import mylistitems

TEMPDIR = 'temp'
LOAD_DIR = 'Загрузки'
THREADS = list()

def AsThread(func):
    global THREADS  # Обожаю велосипеды
    for i  in THREADS:
        try:
            i.join()
            i = ''
        except:
            continue
    THREADS = [i for i in THREADS if i!='']
    def wrapper(*args):
        thread = threading.Thread(target=func, args=args)
        THREADS.append(thread)
        thread.start()
    return wrapper

class MainForm(QtGui.QMainWindow):
    def __init__(self, api, parent):
        super(MainForm, self).__init__()
        uic.loadUi("resources\mainform.ui", self)
        self.setFixedSize(self.size())

        appid = 'AGCorp.loader.photoloader.4'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)

        self.tree = self.set_childs(self.children()[2])
        self.set_connections()

        self.api = api
        self.parent = parent
        self.albums_load_stop = False
        self.photos_load_stop = False
        self.refresh_load_stop = False
        self.myfriends = list()
        self.mygroups = list()

        self.setUser()
        self.setFriends()
        self.setGroups()

    def set_childs(self, parent):
        if len(parent.children())!=0:
            childs = dict()
            childs['self'] = parent
            for child in parent.children():
                childs[child.objectName()] = self.set_childs(child)
            return childs
        return {'self':parent}

    def set_connections(self):
        self.tree['tabWidget']['qt_tabwidget_stackedwidget']['userTab']['userList']['self'].itemClicked.connect(self.userListItemClicked)
        self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].itemClicked.connect(self.friendsListItemClicked)
        self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsFoundEdit']['self'].textChanged.connect(self.friendsFoundEditChanged)
        self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].itemClicked.connect(self.groupsListItemClicked)
        self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsFoundEdit']['self'].textChanged.connect(self.groupsFoundEditChanged)

        self.tree['stackedWidget']['albumsPage']['checkAllButton']['self'].clicked.connect(self.checkAllAlbums)
        self.tree['stackedWidget']['albumsPage']['uncheckAllButton']['self'].clicked.connect(self.uncheckAllAlbums)
        self.tree['stackedWidget']['albumsPage']['albumsList']['self'].itemChanged.connect(self.albumsListItemChecked)
        self.tree['stackedWidget']['albumsPage']['albumsList']['self'].itemDoubleClicked.connect(self.albumsListItemClicked)
        self.tree['stackedWidget']['albumsPage']['albumsStopButton']['self'].clicked.connect(self.albumsStopButtonClicked)
        self.tree['stackedWidget']['albumsPage']['loadAlbums']['self'].clicked.connect(self.loadAlbumsClicked)

        self.tree['stackedWidget']['photosPage']['photosList']['self'].itemChanged.connect(self.photosListItemChecked)
        self.tree['stackedWidget']['photosPage']['photosList']['self'].itemDoubleClicked.connect(self.photosListItemClicked)
        self.tree['stackedWidget']['photosPage']['checkAllButton_2']['self'].clicked.connect(self.checkAllPhotos)
        self.tree['stackedWidget']['photosPage']['uncheckAllButton_2']['self'].clicked.connect(self.uncheckAllPhotos)
        self.tree['stackedWidget']['photosPage']['backButton']['self'].clicked.connect(self.backButtonClicked)
        self.tree['stackedWidget']['photosPage']['photosStopButton']['self'].clicked.connect(self.photosStopButtonClicked)
        self.tree['stackedWidget']['photosPage']['loadPhotos']['self'].clicked.connect(self.loadPhotosClicked)

        self.connect(self, QtCore.SIGNAL('setIcon(QString, int)'), self.setIcon)
        self.connect(self, QtCore.SIGNAL('setFriendsLoadPbar(int)'),
            self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsLoadPBar']['self'].setValue)
        self.connect(self, QtCore.SIGNAL('setGroupsLoadPbar(int)'),
            self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsLoadPBar']['self'].setValue)

    @AsThread
    def setUser(self):
        user = self.api.call('users.get', fields='photo')[0]
#    except Exception as E:
#            print(E)
#            # Error!
#            return
        item = mylistitems.userListItem(user, self)
        self.tree['tabWidget']['qt_tabwidget_stackedwidget']['userTab']['userList']['self'].addItem(item)
        self.emit(QtCore.SIGNAL('setIcon(QString, int)'),
            'userList',
            int(item.itemid))
        self.userListItemClicked(item)
        item.setSelected(True)

    @AsThread
    def setFriends(self):
    
        friends = self.api.call('friends.get',
            fields='photo', order='hints')
#        except Exception as E:
#            print(E)
#            # Error!
#            return
        for n, friend in enumerate(friends, 1):
            item = mylistitems.friendsListItem(friend, self)
            self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].addItem(item)
            self.emit(QtCore.SIGNAL('setIcon(QString, int)'),
                'friendsList',
                int(item.itemid))
            self.emit(QtCore.SIGNAL('setFriendsLoadPbar(int)'), n/len(friends)*100)
            self.myfriends.append((friend, item))

    @AsThread
    def setGroups(self):
    
        groups = self.api.call('groups.get',
            extended=1)[1:]
#        except Exception as E:
#            print(E)
#            # Error!
#            return
        for n, group in enumerate(groups, 1):
            if self.refresh_load_stop:
                return
            item = mylistitems.groupsListItem(group, self)
            self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].addItem(item)
            self.emit(QtCore.SIGNAL('setIcon(QString, int)'),
                'groupsList',
                int(item.itemid))
            self.emit(QtCore.SIGNAL('setGroupsLoadPbar(int)'), n/len(groups)*100)
            self.mygroups.append((group, item))

    @AsThread
    def setAlbums(self, oid=0):
        self.backButtonClicked()
        self.tree['stackedWidget']['albumsPage']['albumsList']['self'].clear()
        self.tree['stackedWidget']['albumsPage']['loadAlbums']['self'].setDisabled(True)
        self.tree['stackedWidget']['albumsPage']['checkAllButton']['self'].setDisabled(True)
        self.tree['stackedWidget']['albumsPage']['uncheckAllButton']['self'].setDisabled(True)
        self.tree['stackedWidget']['albumsPage']['albumsStopButton']['self'].setEnabled(True)
    
        albums = self.api.call('photos.getAlbums',
            oid=oid, need_system=1, need_covers=1)
#        except Exception as E:
#            print(E)
#            # Error!
#            return
        self.tree['stackedWidget']['albumsPage']['albumsCountLabel']['self'].setText(str(len(albums)))
        self.albums_load_stop = False
        self.tree['stackedWidget']['albumsPage']['albumsList']['self'].clear()
        for n, album in enumerate(albums, 1):
            if self.refresh_load_stop:
                return
            if self.albums_load_stop:
                break
            item = mylistitems.albumsListItem(album, self)
            if 'description' in album:
                item.setToolTip(album['description'])
            self.tree['stackedWidget']['albumsPage']['albumsList']['self'].addItem(item)
            self.emit(QtCore.SIGNAL('setIcon(QString, int)'),
                'albumsList',
                int(item.itemid))
        if self.tree['stackedWidget']['albumsPage']['albumsList']['self'].count()>0:
            self.tree['stackedWidget']['albumsPage']['checkAllButton']['self'].setEnabled(True)
            self.tree['stackedWidget']['albumsPage']['uncheckAllButton']['self'].setEnabled(True)
        self.tree['stackedWidget']['albumsPage']['albumsStopButton']['self'].setDisabled(True)

    @AsThread
    def setPhotos(self, album):
        self.tree['stackedWidget']['photosPage']['currentAlbumLabel']['self'].setText(album['title'])
        self.tree['stackedWidget']['photosPage']['photosList']['self'].clear()
        self.tree['stackedWidget']['photosPage']['checkAllButton_2']['self'].setDisabled(True)
        self.tree['stackedWidget']['photosPage']['uncheckAllButton_2']['self'].setDisabled(True)
        self.tree['stackedWidget']['photosPage']['loadPhotos']['self'].setDisabled(True)
        self.tree['stackedWidget']['photosPage']['photosStopButton']['self'].setEnabled(True)
    
        photos = self.api.call('photos.get',
            aid=album['aid'], oid=album['owner_id'])
#        except Exception as E:
#            print(E)
#            # Error!
#            return
        self.tree['stackedWidget']['photosPage']['photosCountLabel']['self'].setText(str(len(photos)))
        self.photos_load_stop = False
        for n, photo in enumerate(photos, 1):
            if self.photos_load_stop:
                break
            if self.refresh_load_stop:
                return
            item = mylistitems.photosListItem(album, photo, self)
            if 'text' in photo:
                item.setToolTip(photo['text'])
            self.tree['stackedWidget']['photosPage']['photosList']['self'].addItem(item)
            self.emit(QtCore.SIGNAL('setIcon(QString, int)'),
                'photosList',
                int(item.itemid))
        if self.tree['stackedWidget']['photosPage']['photosList']['self'].count()>0:
            self.tree['stackedWidget']['photosPage']['checkAllButton_2']['self'].setEnabled(True)
            self.tree['stackedWidget']['photosPage']['uncheckAllButton_2']['self'].setEnabled(True)
            self.tree['stackedWidget']['photosPage']['loadPhotos']['self'].setEnabled(True)
        self.tree['stackedWidget']['photosPage']['photosStopButton']['self'].setDisabled(True)

    def checkAllAlbums(self):
        count = self.tree['stackedWidget']['albumsPage']['albumsList']['self'].count()
        for i in range(count):
            self.tree['stackedWidget']['albumsPage']['albumsList']['self'].item(i).setCheckState(2)

    def uncheckAllAlbums(self):
        count = self.tree['stackedWidget']['albumsPage']['albumsList']['self'].count()
        for i in range(count):
            self.tree['stackedWidget']['albumsPage']['albumsList']['self'].item(i).setCheckState(0)

    def checkAllPhotos(self):
        count = self.tree['stackedWidget']['photosPage']['photosList']['self'].count()
        for i in range(count):
            self.tree['stackedWidget']['photosPage']['photosList']['self'].item(i).setCheckState(2)

    def uncheckAllPhotos(self):
        count = self.tree['stackedWidget']['photosPage']['photosList']['self'].count()
        for i in range(count):
            self.tree['stackedWidget']['photosPage']['photosList']['self'].item(i).setCheckState(0)

    def loadAlbumsClicked(self):
        count = self.tree['stackedWidget']['albumsPage']['albumsList']['self'].count()
        albums = list()
        for i in range(count):
            item = self.tree['stackedWidget']['albumsPage']['albumsList']['self'].item(i)
            if item.checkState()==2:
                albums.append(item.album)
        self.albums_load_stop = True
        self.parent.show_load_form(albums=albums, api=self.api, parent=self)

    def loadPhotosClicked(self):
        count = self.tree['stackedWidget']['photosPage']['photosList']['self'].count()
        photos = list()
        for i in range(count):
            item = self.tree['stackedWidget']['photosPage']['photosList']['self'].item(i)
            if item.checkState()==2:
                photos.append((item.photo, item.album))
        self.photos_load_stop = True
        self.parent.show_load_form(photos=photos, api=self.api, parent=self)

    def setIcon(self, ListName, itemid):
        if ListName=='userList':
            QList = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['userTab']['userList']['self']
        if ListName=='friendsList':
            QList = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self']
        if ListName=='groupsList':
            QList = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self']
        if ListName=='albumsList':
            QList = self.tree['stackedWidget']['albumsPage']['albumsList']['self']
        if ListName=='photosList':
            QList = self.tree['stackedWidget']['photosPage']['photosList']['self']
        count = QList.count()
        for i in range(count):
            if int(QList.item(i).itemid) == itemid:
                QList.item(i).setIcon(QtGui.QIcon(QList.item(i).filename))
                break

    def friendsFoundEditChanged(self, line):
        if line:
            count = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].count()
            for i in range(count):
                item = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].item(i)
                if re.match(line.lower(), item.friend['first_name'].lower()) or re.match(line.lower(), item.friend['last_name'].lower()):
                    self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].scrollToItem(item)
                    item.setSelected(True)
        else:
            self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].scrollToItem(self.tree['tabWidget']['qt_tabwidget_stackedwidget']['friendsTab']['friendsList']['self'].item(0))

    def groupsFoundEditChanged(self, line):
        if line:
            count = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].count()
            for i in range(count):
                item = self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].item(i)
                if re.match(line.lower(), item.group['name'].lower()):
                    self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].scrollToItem(item)
                    item.setSelected(True)
        else:
            self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].scrollToItem(self.tree['tabWidget']['qt_tabwidget_stackedwidget']['groupsTab']['groupsList']['self'].item(0))

    @AsThread
    def userListItemClicked(self, item):
        self.albums_load_stop = True
        self.photos_load_stop = True
        name = self.api.call('users.get', name_case='gen')[0]['first_name']
        self.tree['stackedWidget']['albumsPage']['currentLabel']['self'].setText(name)
        self.setAlbums()

    @AsThread
    def friendsListItemClicked(self, item):
        self.albums_load_stop = True
        self.photos_load_stop = True
        name = self.api.call('users.get', uids=item.friend['uid'], name_case='gen')[0]['first_name']
        self.tree['stackedWidget']['albumsPage']['currentLabel']['self'].setText(name)
        self.setAlbums(item.friend['uid'])

    @AsThread
    def groupsListItemClicked(self, item):
        self.albums_load_stop = True
        self.photos_load_stop = True
        name = 'сообщества ' + item.group['name']
        self.tree['stackedWidget']['albumsPage']['currentLabel']['self'].setText(name)
        self.setAlbums(-item.group['gid'])

    def albumsListItemClicked(self, item):
        self.tree['stackedWidget']['self'].setCurrentIndex(1)
        self.setPhotos(item.album)

    @AsThread
    def photosListItemClicked(self, item):
        sizes = ['src_xxxbig', 'src_xxbig', 'src_xbig',
            'src_big', 'src_small', 'src']
        for i in sizes:
            if i in item.photo:
                link = item.photo[i]
                break
        filename = TEMPDIR+os.sep+os.path.split(link)[1]
        self.api.download_res(link, filename)
        os.startfile(filename)

    def albumsListItemChecked(self, item):
        if item.checkState()==2:
            self.tree['stackedWidget']['albumsPage']['loadAlbums']['self'].setEnabled(True)
        else:
            var = True
            count = self.tree['stackedWidget']['albumsPage']['albumsList']['self'].count()
            for i in range(count):
                if self.tree['stackedWidget']['albumsPage']['albumsList']['self'].item(i).checkState()==2:
                    var = False
                    break
            if var:
                self.tree['stackedWidget']['albumsPage']['loadAlbums']['self'].setDisabled(True)

    def photosListItemChecked(self, item):
        if item.checkState()==2:
            self.tree['stackedWidget']['photosPage']['loadPhotos']['self'].setEnabled(True)
        else:
            var = True
            count = self.tree['stackedWidget']['photosPage']['photosList']['self'].count()
            for i in range(count):
                if self.tree['stackedWidget']['photosPage']['photosList']['self'].item(i).checkState()==2:
                    var = False
                    break
            if var:
                self.tree['stackedWidget']['photosPage']['loadPhotos']['self'].setDisabled(True)

    def backButtonClicked(self):
        self.photos_load_stop = True
        self.tree['stackedWidget']['self'].setCurrentIndex(0)

    def albumsStopButtonClicked(self):
        self.albums_load_stop = True

    def photosStopButtonClicked(self):
        self.photos_load_stop = True

    def closeEvent(self, event):
        self.photos_load_stop = True
        self.albums_load_stop = True
        self.refresh_load_stop = True
        self.parent.closeEvent(event, self)