import faulthandler

import base64
import ctypes
import json
import os
import Crypto
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import time
faulthandler.enable()
class WxWork:
    #企业微信 corp_id
    CORP_ID = ''
    #消息存档的secret_key
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
            print("inti_error", result)
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
            #print("=--=-=-=-=-:",ctypes.string_at(data))
            OriginData = ctypes.string_at(data, -1).decode("utf-8")
            dll.FreeSlice(slice)
            data = (json.loads(OriginData))["chatdata"]
            #定时轮询如果没有chatdata数据也有返回，但是chadata为空，返回： {"errcode":0,"errmsg":"ok","chatdata":[]}
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

                    # 拉取媒体文件，这个举个例子，具体业务逻辑根据情况封装。
                    # 图片文件类型是 jpg
                    # 语音文件类型是 amr
                    # 视频文件类型是 mp4
                    # 这里举例拉取视频类型
                    if result['msgtype'] == "video":
                        sdkfileid = result["video"]["sdkfileid"]
                        #初始化媒体文件拉取的buf
                        #媒体文件每次拉取的最大size为512k，因此超过512k的文件需要分片拉取。若该文件未拉取完整，sdk的IsMediaDataFinish接口会返回0，同时通过GetOutIndexBuf接口返回下次拉取需要传入GetMediaData的indexbuf。
                        #indexbuf一般格式如右侧所示，”Range: bytes = 524288 - 1048575“，表示这次拉取的是从524288到1048575的分片。单个文件首次拉取填写的indexbuf为空字符串，拉取后续分片时直接填入上次返回的indexbuf即可。

                        indexbuf = ""
                        while 1:
                            media_data = dll.NewMediaData()
                            ret = dll.GetMediaData(new_sdk,indexbuf,sdkfileid.encode(), "","",5, ctypes.c_long(media_data))
                            if (ret!=0):
                                print("获取失败:", ret)
                                dll.FreeMediaData(media_data)
                                break
                            #用msgid作为文件名，这里根据需求制定文件名
                            filename = os.getcwd() + "/images/" + result["msgid"] + '.mp4'
                            #ab为二进制文件追加读写，用于分片写入不会覆盖前面已经写入的
                            with open(filename,'ab') as f:
                                #这里注意ctypes.string_at的参数（address，size）,size就是分片长度，得到 bytes
                                res = ctypes.string_at(dll.GetData(media_data), dll.GetDataLen(media_data))
                                f.write(res)
                                f.close
                            #拉取完最后一个分片
                            if(dll.IsMediaDataFinish(media_data) == 1):
                                dll.FreeMediaData(media_data)
                                break
                            else:
                                #获取下一个分片的indexbuf
                                indexbuf = ctypes.string_at(dll.GetOutIndexBuf(media_data))
        dll.DestroySdk(new_sdk)

if __name__ == '__main__':
    WxWork.sync_msg()
