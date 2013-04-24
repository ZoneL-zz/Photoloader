__author__ = 'Alexander'
import imp
import os
import shutil
from urllib.parse import urlparse
from PyQt4 import QtGui, QtCore, QtWebKit
from modules import vkapi
from forms import mainform
from forms import loadform

TEMPDIR = 'temp'
LOAD_DIR = 'Загрузки'


class Main:
    def __init__(self):
        SCOPE = ['friends', 'photos', 'groups']
        CLIENT_ID = '3588045'

        self.app = QtGui.QApplication([])

        self.login_browser = QtWebKit.QWebView()
        self.login_browser.urlChanged.connect(self.login_browser_url_changed)
        url = 'http://oauth.vk.com/oauth/authorize?'+\
            'redirect_uri=oauth.vk.com/blank.html&'+\
            'response_type=token&'+\
            'client_id={0}&scope={1}&'.format(CLIENT_ID,
                ','.join(SCOPE))+\
            'display=wap'
        self.login_browser.load(QtCore.QUrl(url))
        self.login_browser.show()
        self.app.exec_()

    def show_main_form(self):
        if not os.path.exists(TEMPDIR):
            os.mkdir(TEMPDIR)
        imp.reload(mainform)
        self.main_form = mainform.MainForm(self.api, self)
        self.main_form.show()

    def login_browser_url_changed(self, url):
        url = url.toString()
        if urlparse(url).path != '/blank.html':
            return
        self.login_browser.close()
        self.params = {
            p_pair.split('=')[0]:p_pair.split('=')[1]
            for p_pair in url.split('#')[1].split('&')
            }
        self.api = vkapi.VKapi(self.params['access_token'],
                               int(self.params['user_id']))
        with open('token', 'w') as F:
            F.write(self.params['access_token']+' '+self.params['user_id'])
        self.show_main_form()

    def show_load_form(self, **kwargs):
        imp.reload(loadform)
        if not os.path.exists(LOAD_DIR):
            os.mkdir(LOAD_DIR)
        self.load_form = loadform.LoadForm(args=kwargs, api=self.api, parent=self)
        self.load_form.show()

    def closeEvent(self, Event, window):
        reply = QtGui.QMessageBox.question(window, 'Выход',
            "Закрыть приложение?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        try:
            shutil.rmtree(TEMPDIR)
        except:
            pass

        if reply == QtGui.QMessageBox.Yes:
            Event.accept()
        else:
            Event.ignore()
            self.show_main_form()

if __name__=='__main__':
    Main()