import urllib.request
import urllib.parse
import json
import os.path

class VKError(Exception):
    """
    VK error class
    """
    def __init__(self, errno, msg, response=None):
        self.errno = errno
        self.msg = msg
        self.response = response

    def __str__(self):
        return '[{0}] {1}'.format(self.errno, self.msg)


class VKapi:  
    def __init__(self, access_token=None, user_id=None):
        """
        high-level access to vk.com api
        """
        self.token = access_token
        self.user_id = user_id
        self._submethod = None

    def call_api(self, method, params):
        """
        low-level function to call api method with parameters
        params is a list of tuples ('field', value)
        """
        params_list = list()
        if len(params)!=0:
            params_list = [element for element in params]
        if self.token:
            params_list.append(("access_token", self.token))
        url = "https://api.vk.com/method/{0}?{1}".format(method,
            urllib.parse.urlencode(params_list))
        try:
            response = urllib.request.urlopen(url).read()
        except urllib.error.URLError:
            raise VKError(1024, 'Internet connection failed')
        return json.loads(response.decode())

    def compile_params(self, kwargs):
        """
        turns dictionary of parameters into valid list type
        for call_api method
        """
        params = list()
        for key in kwargs:
            if len(str(kwargs[key]))!=0:
                if isinstance(kwargs[key], list):
                    params.append((key, ','.join(kwargs[key])))
                else:
                    params.append((key, kwargs[key]))
        return params

    def call(self, method, **params):
        """
        compiles parameters, calls api and handles exceptions
        """
        response = self.call_api(method, self.compile_params(params))
        if 'error' in response:
            raise VKError(response['error']['error_code'],
                response['error']['error_msg'], response['error'])
        if len(str(response['response']))==0:
            raise VKError(1025, 'Empty response')
        return response['response']

    def download_res(self, link, filename='', dirname=''):
        """
        Downloads resource from link to filename
        """
        # urllib.urlretrieve
        if not filename:
            if dirname:
                filename = dirname+os.sep+os.path.split(link)[-1]
            else:
                filename = os.path.split(link)[-1]
        with open(filename, 'wb') as f:
            block_size = 128*1024  # 128 килобайт
            req = urllib.request.urlopen(link)
            while True:
                block = req.read(block_size)
                if not block:
                    break
                f.write(block)

    def upload_res(self, link, filename, res_type):
        """
        Upload resource from filename to link using http POST request

        res_type is the resource type, can be
        - album_upload - filename is list with names of images for
          uploading. 1<=len(filename)<=5
        - wall_upload - filename is a filename of single image
        - profile_upload - filename is a filename of single image
        - message_upload - filename is a filename of single image
        - audio_upload - filename is a filename of single audiofile
        - video_upload - filename is a filename of single videofile
        - doc_upload - filename is a filename of single document
        """

        headers = {
            'Content-Type': 'multipart/form-data; boundary=BoUn/*DaryAlxasf'
        }

        if not isinstance(filename, list):
            filename = [filename]

        # LOL
        if res_type=='album_upload':
            for i in range(len(filename)):
                body =  '\r\n--BoUn/*DaryAlxasf'
                body += '\r\nContent-Disposition: form-data; name="file{0}"; filename="{1}"'.format(i+1, filename[i])
                body += '\r\nContent-Transfer-Encoding: binary\r\n\r\n'
                body = body.encode()
                with open(filename[i], 'rb') as f:
                    body += f.read()
        if res_type=='wall_upload' or res_type=='profile_upload' or res_type=='message_upload':
                body =  '\r\n--BoUn/*DaryAlxasf'
                body += '\r\nContent-Disposition: form-data; name="photo"; filename="{1}"'.format(filename)
                body += '\r\nContent-Transfer-Encoding: binary\r\n\r\n'
                body = body.encode()
                with open(filename, 'rb') as f:
                    body += f.read()
        if res_type=='audio_upload' or res_type=='doc_upload':
                body =  '\r\n--BoUn/*DaryAlxasf'
                body += '\r\nContent-Disposition: form-data; name="file"; filename="{1}"'.format(filename)
                body += '\r\nContent-Transfer-Encoding: binary\r\n\r\n'
                body = body.encode()
                with open(filename, 'rb') as f:
                    body += f.read()
        if res_type=='video_upload':
                body =  '\r\n--BoUn/*DaryAlxasf'
                body += '\r\nContent-Disposition: form-data; name="video_file"; filename="{1}"'.format(filename)
                body += '\r\nContent-Transfer-Encoding: binary\r\n\r\n'
                body = body.encode()
                with open(filename, 'rb') as f:
                    body += f.read()

        body += '\r\n--BoUn/*DaryAlxasf--\r\n\r\n'.encode()

        request = urllib.request.Request(link, body, headers)
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode())

if __name__=='__main__':
    worker = VKapi()
    print(worker.call('status.get'))
    
