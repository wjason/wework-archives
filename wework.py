import base64
import ctypes
import json
import os
import Crypto
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import time

class WxWork:
    #企业微信 corp_id
    CORP_ID = ''
    #消息存单的secret_key
    CHAT_SECRET = ''
    #打开读取秘钥，文件为秘钥文件的存储地址，我这里放同级目录下
    with open('private.pem','r') as f:
         PRI_KEY = f.read()
    @classmethod
    def sync_msg(cls):
        # libWeWorkFinanceSdk_C的文件位置，我这里放同级目录下
        dll = ctypes.cdll.LoadLibrary(os.getcwd() + "/libWeWorkFinanceSdk_C.so")
        new_sdk = dll.NewSdk()
        result = dll.Init(new_sdk, cls.CORP_ID.encode(), cls.CHAT_SECRET.encode())
        if result != 0:
            print("inti_error")
            return
        private_key = RSA.import_key(cls.PRI_KEY)
        cipher = Crypto.Cipher.PKCS1_v1_5.new(private_key)
        #设置步长，真实环境可以用Redis存储
        seq = 0
        while 1:
            #这里设置了轮询的请求时间，可以不要，根据自己需求，企业微信接口有限制每分钟请求数，一分钟600次
            time.sleep(3)
            slice = dll.NewSlice()
            #d是一个状态值判断，0标识成功，函数参数/返回/处理内容看企业微信文档
            d = dll.GetChatData(new_sdk, seq, 1000, '', '', 5, ctypes.c_long(slice))
            data = dll.GetContentFromSlice(slice)
            OriginData = ctypes.string_at(data, -1).decode("utf-8")
            dll.FreeSlice(slice)
            data = (json.loads(OriginData))["chatdata"]
            #定时轮训如果没有chatdata数据也有返回，但是chadata为空，返回： {"errcode":0,"errmsg":"ok","chatdata":[]}
            if not data:
                print("this moment no chatdata!")

            if data:
                #获取设置步长，SDK下次请求是 seq+1开始拉消息
                seq = data[-1].get('seq')
                for msg in data:
                    #根据上面的密文解密明文，函数参数/返回/处理内容看企业微信文档
                    encrypt_key = cipher.decrypt(base64.b64decode(msg.get('encrypt_random_key')), "ERROR")
                    slices = dll.NewSlice()
                    dll.DecryptData(encrypt_key, msg.get('encrypt_chat_msg').encode(), ctypes.c_long(slices))
                    result = dll.GetContentFromSlice(slices)
                    result = ctypes.string_at(result, -1).decode("utf-8")
                    result = json.loads(result)
                    #把步长添加如解析后数据，方便入库，看需求
                    result["seq"] = msg.get('seq')
                    dll.FreeSlice(slices)
                    print(result)
        dll.DestroySdk(new_sdk)

if __name__ == '__main__':
    WxWork.sync_msg()