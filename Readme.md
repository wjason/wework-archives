## 企业微信消息存档-Python

### 前言
企业微信消息存档的文档和SDK文档材料相对比较少，也只提供了C和JAVA
版本的SDK，文档和案例也比较缺，踩了一天的坑，用Python调用C版本linux的
so库实现了下，加解密流程相对比较复杂。
  
做了个脚本示例，可以跑通拉取存档消息存档的信息数据和解密的。
  
已经完成：  
* 在Python引入SDK so库初始化
* 加解密和秘钥秘钥处理
* 拉取消息存档加密信息
* 解密信息获取内容并结构化

### Todo
~~根据media_id 获取媒体材料~~ [done]


### 提示
1. 先阅读企业微信的文档，文档地址：https://developer.work.weixin.qq.com/document/path/91774
2. 脚本中使用的是Linux C版的so库，SDK接口调用参数见文档
3. 企业微信提供了C/JAVA的SDK只支持Linux和win，mac版本不可用linux版本，会提示so出错，用源代码编译后也不能使用，这个要注意。
4. 脚本运行环境Python3.x，2.x未测试