__author__ = 'Alexander'
from PyQt4 import QtGui, uic, QtCore
import os
import threading
import time
import resources.resourcefile

THREADS = list()
TEMP_DIR = 'temp'
LOAD_DIR = 'Загрузки'

def AsThread(func):
    global THREADS
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

def hashstr(line):
    res = list()
    for i in line:
        res.append(str(ord(i)))
    return ''.join(res)

class Timer:
    def __init__(self):
        self.__elapsed = 0
        self.__stop = True
        threading.Thread(target=self.__runproc).start()

    def start(self):
        self.__stop = False

    def __runproc(self):
        while True:
            if not self.__stop:
                time.sleep(0.1)
                self.__elapsed += 0.1
            else:
                time.sleep(0.01)

    def pause(self):
        self.__stop = True

    def get(self):
        return self.__elapsed

    def stop(self):
        self.__stop = True
        self.__elapsed = 0
        return self.__elapsed

class LoadForm(QtGui.QWidget):
    def __init__(self, args, api, parent):
        super(LoadForm, self).__init__()
        uic.loadUi("resources\\loadform.ui", self)
        self.setFixedSize(self.size())

        self.tree = self.set_childs(self)
        self.timer = Timer()

        self.parent = parent
        self.parent.main_form.setDisabled(True)
        self.api = api
        self.stop_load = False
        self.pause_load = False
        self.moreInfoShowed = False
        self.count = 0
        self.loaded = 0
        self.failed = 0
        self.total = 0
        self.totalsize = 0

        self.set_connections()

        if 'albums' in args:
            self.loadAlbums(args['albums'])
        if 'photos' in args:
            self.loadPhotos(args['photos'])

    def set_connections(self):
        self.connect(self, QtCore.SIGNAL('updateBars(int, int)'), self.updatePBars)
        self.tree['abortButton']['self'].clicked.connect(self.abort)
        self.tree['pauseButton']['self'].clicked.connect(self.pause)
        self.tree['moreInfoButton']['self'].clicked.connect(self.moreInfoPushed)
        self.tree['continueButton']['self'].clicked.connect(self.resume)

    def set_childs(self, parent):
        if len(parent.children())!=0:
            childs = dict()
            childs['self'] = parent
            for child in parent.children():
                childs[child.objectName()] = self.set_childs(child)
            return childs
        return {'self':parent}

    def loadAlbum(self, album, dirname):
        photos = self.api.call('photos.get', oid=album['owner_id'], aid=album['aid'])
        sizes = ['src_xxxbig', 'src_xxbig', 'src_xbig',
            'src_big', 'src_small', 'src']

        for n, photo in enumerate(photos, 1):
            if self.pause_load:
                while True:
                    if not self.pause_load:
                        break
                    time.sleep(0.1)
            if self.stop_load:
                break

            self.timer.start()

            for i in sizes:
                if i in photo:
                    link = photo[i]
                    break
            filename = LOAD_DIR+os.sep+dirname+os.sep+str(album['aid'])+'_'+str(photo['pid'])+'.'+link.split('.')[-1]
            if os.path.exists(filename):
                self.emit( QtCore.SIGNAL('updateBars(int, int)'), n/len(photos)*100, self.loaded/self.total*100)
                continue

            try:
                self.api.download_res(link, filename)
            except:
                self.failed += 1
                self.tree['moreInfoFrame']['errorCountLabel']['self'].setText(str(self.failed))
            else:
                self.loaded += 1
                self.tree['moreInfoFrame']['loadedCountLabel']['self'].setText(str(self.loaded))

            self.tree['moreInfoFrame']['leftCountLabel']['self'].setText(str(self.total-self.loaded))

            self.totalsize += os.path.getsize(filename)
            mod = 1
            suffix = 'Б'
            if self.totalsize>=1024:
                suffix = 'Кб'
                mod = 1024
            if self.totalsize>=1024*1024:
                suffix = 'Мб'
                mod = 1024*1024
            self.tree['moreInfoFrame']['loadedSizeLabel']['self'].setText(str(self.totalsize//mod)+suffix)

            speed = os.path.getsize(filename)//self.timer.get()*60
            self.timer.stop()
            suffix = 'Б/c'
            mod = 1
            if speed>=1024:
                 mod = 1024
                 suffix = 'Кб/c'
            if speed>=1024*1024:
                mod = 1024*1024
                suffix = 'Мб/c'
            self.tree['moreInfoFrame']['speedLabel']['self'].setText(str(int(speed//mod))+suffix)

            self.emit( QtCore.SIGNAL('updateBars(int, int)'), n/len(photos)*100, self.loaded/self.total*100)

    @AsThread
    def loadAlbums(self, albums):
        for album in albums:
            if not album['size'] is None:
                self.total += int(album['size'])
        self.tree['frame']['loadCountLabel']['self'].setText(str(self.total))
        if int(str(self.total)[-1])==1:
            self.tree['frame']['loadSuffixLabel']['self'].setText('элемент')
        if 1<int(str(self.total)[-1])<5:
            self.tree['frame']['loadSuffixLabel']['self'].setText('элементa')
        if int(str(self.total)[-1])>=5 or int(str(self.total)[-1])==0:
            self.tree['frame']['loadSuffixLabel']['self'].setText('элементов')

        for n, album in enumerate(albums, 1):
            if album['size'] is None:
                continue
            try:
                dirname = str(album['owner_id'])+'_'+str(album['aid'])+' '+album['title']
                if not os.path.exists(LOAD_DIR+os.sep+dirname):
                    os.mkdir(LOAD_DIR+os.sep+dirname)
            except:
                dirname = str(album['owner_id'])+'_'+str(album['aid'])+' '+hashstr(album['title'])[:4]
                if not os.path.exists(LOAD_DIR+os.sep+dirname):
                    os.mkdir(LOAD_DIR+os.sep+dirname)

            self.tree['loadDestLabel']['self'].setText('Альбом {0} в {1}{2}{3}'.format(album['title'], LOAD_DIR, os.sep, dirname))
            self.loadAlbum(album, dirname)
        self.abort()

    @AsThread
    def loadPhotos(self, photos):
        self.total = len(photos)
        self.tree['frame']['loadCountLabel']['self'].setText(str(self.total))
        if int(str(self.total)[-1])==1:
            self.tree['frame']['loadSuffixLabel']['self'].setText('элемент')
        if 1<int(str(self.total)[-1])<5:
            self.tree['frame']['loadSuffixLabel']['self'].setText('элементa')
        if int(str(self.total)[-1])>=5 or int(str(self.total)[-1])==0:
            self.tree['frame']['loadSuffixLabel']['self'].setText('элементов')

        try:
            dirname = str(photos[0][1]['owner_id'])+'_'+str(photos[0][1]['aid'])+' '+photos[0][1]['title']
            if not os.path.exists(LOAD_DIR+os.sep+dirname):
                os.mkdir(LOAD_DIR+os.sep+dirname)
        except:
            dirname = str(photos[0][1]['owner_id'])+'_'+str(photos[0][1]['aid'])+' '+hashstr(photos[0][1]['title'])[:4]
            if not os.path.exists(LOAD_DIR+os.sep+dirname):
                os.mkdir(LOAD_DIR+os.sep+dirname)

        self.tree['loadDestLabel']['self'].setText('Альбом {0} в {1}{2}{3}'.format(photos[0][1]['title'], LOAD_DIR, os.sep, dirname))

        sizes = ['src_xxxbig', 'src_xxbig', 'src_xbig',
            'src_big', 'src_small', 'src']

        for n, photo in enumerate(photos, 1):
            if self.pause_load:
                while True:
                    if not self.pause_load:
                        break
                    time.sleep(0.1)
            if self.stop_load:
                break

            self.timer.start()

            for i in sizes:
                if i in photo[0]:
                    link = photo[0][i]
                    break
            filename = 'Загрузки'+os.sep+dirname+os.sep+str(photo[0]['aid'])+'_'+str(photo[0]['pid'])+'.'+link.split('.')[-1]
            if os.path.exists(filename):
                self.emit( QtCore.SIGNAL('updateBars(int, int)'), n/self.total*100, self.loaded/self.total*100)
                continue

            try:
                self.api.download_res(link, filename)
            except:
                self.failed += 1
                self.tree['moreInfoFrame']['errorCountLabel']['self'].setText(str(self.failed))
            else:
                self.loaded += 1
                self.tree['moreInfoFrame']['loadedCountLabel']['self'].setText(str(self.loaded))

            self.tree['moreInfoFrame']['leftCountLabel']['self'].setText(str(self.total-self.loaded))
            self.totalsize += os.path.getsize(filename)

            mod = 1
            suffix = 'Б'
            if self.totalsize>=1024:
                suffix = 'Кб'
                mod = 1024
            if self.totalsize>=1024*1024:
                suffix = 'Мб'
                mod = 1024*1024
            self.tree['moreInfoFrame']['loadedSizeLabel']['self'].setText(str(self.totalsize//mod)+suffix)

            speed = os.path.getsize(filename)//self.timer.get()*60
            suffix = 'Б/c'
            mod = 1
            if speed>=1024:
                 mod = 1024
                 suffix = 'Кб/c'
            if speed>=1024*1024:
                mod = 1024*1024
                suffix = 'Мб/c'
            self.tree['moreInfoFrame']['speedLabel']['self'].setText(str(int(speed//mod))+suffix)

            self.emit( QtCore.SIGNAL('updateBars(int, int)'), n/self.total*100, self.loaded/self.total*100)
        self.timer.stop()
        self.abort()

    def updatePBars(self, value1, value2):
        self.tree['totalPBar']['self'].setValue(value2)
        self.tree['albumPBar']['self'].setValue(value1)

    def pause(self):
        self.pause_load = True
        self.tree['continueButton']['self'].setEnabled(True)
        self.tree['pauseButton']['self'].setDisabled(True)

    def resume(self):
        self.pause_load = False
        self.tree['continueButton']['self'].setDisabled(True)
        self.tree['pauseButton']['self'].setEnabled(True)

    def abort(self):
        self.stop_load = True
        self.pause_load = False
        self.parent.main_form.setEnabled(True)
        self.close()

    def moreInfoPushed(self):
        if self.moreInfoShowed:
            self.moreInfoShowed = False
            self.setFixedHeight(190)
            self.setFixedSize(self.size())
            self.tree['moreInfoButton']['self'].setIcon(QtGui.QIcon(':/icons/icons/downicon.ico'))
        else:
            self.moreInfoShowed = True
            self.setFixedHeight(325)
            self.setFixedSize(self.size())
            self.tree['moreInfoButton']['self'].setIcon(QtGui.QIcon(':/icons/icons/upicon.ico'))

    def closeEvent(self, event):
        self.stop_load = True
        self.pause_load = False
        self.parent.main_form.setEnabled(True)
        event.accept()