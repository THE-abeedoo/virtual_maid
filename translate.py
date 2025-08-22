# import json
# import sys
# import uuid
# import requests
# import hashlib
# from imp import reload
# import time

# reload(sys)

# YOUDAO_URL = 'https://openapi.youdao.com/api'
# APP_KEY = '5b5ffdbe0758b2ab'
# APP_SECRET = 'W5CNREE4Y0upb3q9KvEgfrAiexxXz955'


# def encrypt(signStr):
#     hash_algorithm = hashlib.sha256()
#     hash_algorithm.update(signStr.encode('utf-8'))
#     return hash_algorithm.hexdigest()


# def truncate(q):
#     if q is None:
#         return None
#     size = len(q)
#     return q if size <= 20 else q[0:10] + str(size) + q[size - 10:size]


# def do_request(data):
#     headers = {'Content-Type': 'application/x-www-form-urlencoded'}
#     return requests.post(YOUDAO_URL, data=data, headers=headers)


# def connect(q):

#     data = {}
#     data['from'] = 'auto'
#     data['to'] = 'ja'
#     data['signType'] = 'v3'
#     curtime = str(int(time.time()))
#     data['curtime'] = curtime
#     salt = str(uuid.uuid1())
#     signStr = APP_KEY + truncate(q) + salt + curtime + APP_SECRET
#     sign = encrypt(signStr)
#     data['appKey'] = APP_KEY
#     data['q'] = q
#     data['salt'] = salt
#     data['sign'] = sign
#     data['vocabId'] = "您的用户词表ID"

#     response = do_request(data)
#     contentType = response.headers['Content-Type']
#     if contentType == "audio/mp3":
#         millis = int(round(time.time() * 1000))
#         filePath = "合成的音频存储路径" + str(millis) + ".mp3"
#         fo = open(filePath, 'wb')
#         fo.write(response.content)
#         fo.close()
#     else:
#         return json.loads(response.content.decode())["translation"][0]


# if __name__ == '__main__':
#     print(connect(input()))

import translators as ts

def connect(text):
    translated_text = ts.translate_text(text, to_language='ja',from_language='zh',translator="alibaba")
    return translated_text