from PyWeChatSpy import WeChatSpy
from PyWeChatSpy.command import *
from PyWeChatSpy.proto import spy_pb2

from lxml import etree
import time
import logging
import os
import shutil
from queue import Queue
import json
import random
from apscheduler.schedulers.background import BackgroundScheduler
import re
import uuid

import BotAPIs



logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s [%(threadName)s] %(levelname)s: %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
sh.setLevel(logging.INFO)
logger.addHandler(sh)

SELF_WXID = 'wxid_a0msbb5jvugs22'

groups = []


file = open('Bot.conf', 'r')
conf = json.load(file)
file.close()

USER = conf['USERNAME']


WECHAT_PROFILE = rf"C:\Users\{USER}\Documents\WeChat Files"
PATCH_PATH = rf"C:\Users\{USER}\AppData\Roaming\Tencent\WeChat\patch"
if not os.path.exists(WECHAT_PROFILE):
    logger.error("请先设置计算机用户名，并完善WECHAT_PROFILE和PATCH_PATH")
    exit()
if os.path.isdir(PATCH_PATH):
    shutil.rmtree(PATCH_PATH)
if not os.path.exists(PATCH_PATH):
    with open(PATCH_PATH, "a") as wf:
        wf.write("")
my_response_queue = Queue()

def save_status():
    global old_variables
    global variables
    if variables != old_variables:
        file = open('status.json', 'w')
        json.dump(variables, file)
        file.close()
        print("Status Saved")
        old_variables = variables

def handle_response(data):
    try:

        global variables
        global contacts_list
        global conf
        if data.type == PROFESSIONAL_KEY:
            if not data.code:
                logger.warning(data.message)
        elif data.type == WECHAT_CONNECTED:  # 微信接入
            print(f"微信客户端已接入 port:{data.port}")
            time.sleep(1)
            # spy.get_login_qrcode()  # 获取登录二维码
        elif data.type == HEART_BEAT:  # 心跳
            pass
        elif data.type == WECHAT_LOGIN:  # 微信登录
            print("微信登录")
            spy.get_account_details()  # 获取登录账号详情
        elif data.type == WECHAT_LOGOUT:  # 微信登出
            print("微信登出")
        elif data.type == CHAT_MESSAGE:  # 微信消息
            chat_message = spy_pb2.ChatMessage()
            chat_message.ParseFromString(data.bytes)
            for message in chat_message.message:
                _type = message.type  # 消息类型 1.文本|3.图片...自行探索
                _from = message.wxidFrom.str  # 消息发送方
                _to = message.wxidTo.str  # 消息接收方
                content = message.content.str  # 消息内容
                _from_group_member = ""
                if _from.endswith("@chatroom"):  # 群聊消息
                    _from_group_member = message.content.str.split(':\n', 1)[0]  # 群内发言人
                    content = message.content.str.split(':\n', 1)[-1]  # 群聊消息内容
                image_overview_size = message.imageOverview.imageSize  # 图片缩略图大小
                image_overview_bytes = message.imageOverview.imageBytes  # 图片缩略图数据
                # with open("img.jpg", "wb") as wf:
                #     wf.write(image_overview_bytes)
                overview = message.overview  # 消息缩略
                timestamp = message.timestamp  # 消息时间戳
                if _type == 1:
                    try:
                        # 文本消息
                        print("from ", _from, "to ", _to, _from_group_member, content)
                        if content == "ping":
                            spy.send_text(_from, "Hello, 乡村熊2.0\n" + content, at_wxid=_from_group_member)
                            continue
                        if _from == SELF_WXID:
                            continue
                        if variables['run'][_from]:
                            # 启动状态
                            if content[0] == "#":
                                continue
                            elif content == "关闭":
                                variables['run'][_from] = False
                                spy.send_text(_from, "机器人已关闭", at_wxid=_from_group_member)
                            elif content == "开始聊天":
                                variables['Bot'][_from] = random.choice(('Xiaosi', 'Qingyun'))
                                spy.send_text(_from, "HI！我来了", at_wxid=_from_group_member)
                            elif content == "结束聊天" and variables['Bot'][_from] == 'Xiaosi':
                                variables['Bot'][_from] = ''
                                spy.send_text(_from, "今天就聊到这里吧！", at_wxid=_from_group_member)
                            elif content[:5] == "给TA送信":
                                try:
                                    _uuid = variables['ano_uuid'][_from][-1]
                                except KeyError:
                                    variables['ano_uuid'][_from] = []
                                    _uuid = str(uuid.uuid4())
                                    variables['ano_uuid'][_from].append(_uuid)
                                try:
                                    parameter = content.split('\n', 2)
                                    to = parameter[1]
                                    text = parameter[2]
                                    print(to, text)
                                except IndexError:
                                    spy.send_text(_from, "命令有问题，发送失败。请使用如下格式\n给TA送信\nTA的昵称\n内容")
                                else:
                                    _flag = False
                                    for contact in contacts_list.contactDetails:
                                        if contact.nickname.str == to:
                                            spy.send_text(contact.wxid.str,
                                                          "【乡村熊】Ding~收到一条留言，请查看\n" + text + "\n\n如要回复请输入“\n回复\n" + _uuid + "\n回复内容”")
                                            spy.send_text(_from, "发送完成，不要提醒TA哦~")
                                            _flag = True
                                    if not _flag:
                                        spy.send_text(_from, "我的好友里面好像没有" + to + "，请检查输入，或者把我推荐给TA吧！")
                            elif content[:2] == "回复":
                                try:
                                    parameter = content.split('\n', 2)
                                    print(parameter)
                                    _uuid = parameter[1]
                                    text = parameter[2]
                                    _flag = False
                                    for key in variables['ano_uuid']:
                                        print(key)
                                        print(variables['ano_uuid'][key])
                                        if _uuid in variables['ano_uuid'][key]:
                                            to = key
                                            _flag = True
                                    if _flag:
                                        _flag2 = False
                                        for contact in contacts_list.contactDetails:
                                            if contact.wxid == _from:
                                                nick = contact.nickname.str
                                                _flag2 = True
                                        if _flag2:
                                            spy.send_text(to, "【乡村熊】Ding~收到一条回复，请查看\n" + text + "来自" + nick)
                                        else:
                                            spy.send_text(to, "【乡村熊】Ding~收到一条回复，请查看\n" + text)
                                        spy.send_text(_from, "发送成功")
                                    else:
                                        spy.send_text(_from, "有些小问题，发送失败")
                                except IndexError:
                                    spy.send_text(_from, "命令有问题，发送失败。请使用如下格式\n回复\nuuid\n回复内容")
                            elif content == "更新uuid":
                                _uuid = str(uuid.uuid4())
                                variables['ano_uuid'][_from].append(_uuid)
                                spy.send_text(_from, "成功，新的uuid为" + _uuid)
                            elif content[:6] == "给TA发短信":
                                try:
                                    parameter = content.split('\n', 2)
                                    phonenum = parameter[1]
                                    text = parameter[2]
                                except IndexError:
                                    spy.send_text(_from, "命令有问题，发送失败。请使用如下格式\n给TA发短信\n手机号\n内容")
                                else:
                                    for staff in conf['staff']:
                                        spy.send_text(staff, "短信请求：\n" + phonenum + "\n" + "【乡村熊】Ding~收到一条留言，请查看\n" +
                                                      text + "\n请勿回复，发送自私人手机。如要回复请添加乡村熊微信好友，微信号XiangCunxiongBot。如不想接到短信请回复TD")
                                    spy.send_text(_from, "已将请求发送至志愿者，不过请放心不会泄露来源。天知地知你知我知~", at_wxid=_from_group_member)
                            elif content == "帮助":
                                spy.send_text(_from, "命令列表：\n\n开启\n关闭\n开始聊天\n结束聊天\n给TA送信\n回复\n更新uuid\n给TA发短信\n帮助")

                            elif variables['Bot'][_from] == 'Xiaosi':
                                # 调用思科
                                content = content.replace("乡村熊", "小思")
                                content = content.replace("\n", "{br}")
                                res = BotAPIs.requestXiaosi(content)
                                if res['message'] == 'success':
                                    results = res['data']['info']['text']
                                    results = results.replace("小思", "乡村熊")
                                    results = results.replace("{br}", "\n")
                                    spy.send_text(_from, results, at_wxid=_from_group_member)

                            elif variables['Bot'][_from] == 'Qingyun':
                                # 调用青云
                                content = content.replace("乡村熊", "菲菲")
                                content = content.replace("\n", "{br}")
                                res = BotAPIs.requestQingyun(content)
                                if res['result'] == 0:
                                    results = res['content']
                                    results = results.replace("菲菲", "乡村熊")
                                    results = results.replace("{br}", "\n")
                                    spy.send_text(_from, results, at_wxid=_from_group_member)

                            else:
                                spy.send_text(_from, "未知命令，回复“帮助”，或者“开始聊天”与乡村熊聊天", at_wxid=_from_group_member)

                        else:
                            # 待机状态
                            if not _from.endswith("@chatroom"):
                                spy.send_text(_from, "机器人未开启，如要开启请输入”开启“")
                            if content == "开启":
                                variables['run'][_from] = True
                                spy.send_text(_from, "机器人已开启")
                    except KeyError:
                        variables['run'][_from] = True
                elif _type == 3:  # 图片消息
                    file_path = message.file
                    file_path = os.path.join(WECHAT_PROFILE, file_path)
                    time.sleep(3)
                    spy.decrypt_image(file_path, "a.jpg")
                elif _type == 43:  # 视频消息
                    pass
                elif _type == 49:  # XML报文消息
                    print(_from, _to, message.file)
                    xml = etree.XML(content)
                    xml_type = xml.xpath("/msg/appmsg/type/text()")[0]
                    if xml_type == "5":
                        xml_title = xml.xpath("/msg/appmsg/title/text()")[0]
                        print(xml_title)
                        if xml_title == "邀请你加入群聊":
                            url = xml.xpath("/msg/appmsg/url/text()")[0]
                            print(url)
                            time.sleep(1)
                            spy.get_group_enter_url(_from, url)
                elif _type == 37:  # 好友申请
                    print("新的好友申请")
                    obj = etree.XML(message.content.str)
                    encryptusername, ticket = obj.xpath("/msg/@encryptusername")[0], obj.xpath("/msg/@ticket")[0]
                    spy.accept_new_contact(encryptusername, ticket)  # 接收好友请求
                elif _type == 10000:  # 判断是微信拍一拍系统提示
                    # 因为微信系统消息很多 因此需要用正则匹配消息内容进一步过滤拍一拍提示
                    m = re.search('".*" 拍了拍我', content)
                    if m:  # 搜索到了匹配的字符串 判断为拍一拍
                        image_path = f"images/{random.randint(1, 7)}.jpg"  # 随机选一张回复用的图片
                        spy.send_file(_from, image_path)  # 发送图片
        elif data.type == ACCOUNT_DETAILS:  # 登录账号详情
            if data.code:
                account_details = spy_pb2.AccountDetails()
                account_details.ParseFromString(data.bytes)
                print(account_details)
                spy.get_contacts()  # 获取联系人列表
            else:
                logger.warning(data.message)
        elif data.type == CONTACTS_LIST:  # 联系人列表
            if data.code:
                contacts_list = spy_pb2.Contacts()
                print('CONTACTS_LIST')
                contacts_list.ParseFromString(data.bytes)
                for contact in contacts_list.contactDetails:  # 遍历联系人列表
                    wxid = contact.wxid.str  # 联系人wxid
                    nickname = contact.nickname.str  # 联系人昵称
                    remark = contact.remark.str  # 联系人备注
                    id = contact.wechatId
                    print(wxid, nickname, remark, id)
                    if wxid.endswith("chatroom"):  # 群聊
                        groups.append(wxid)
                # spy.get_contact_details("20646587964@chatroom")  # 获取群聊详情
            else:
                logger.error(data.message)
        elif data.type == CONTACT_DETAILS:
            if data.code:
                contact_details_list = spy_pb2.Contacts()
                print('CONTACT_DETAILS')
                contact_details_list.ParseFromString(data.bytes)
                for contact_details in contact_details_list.contactDetails:  # 遍历联系人详情
                    wxid = contact_details.wxid.str  # 联系人wxid
                    nickname = contact_details.nickname.str  # 联系人昵称
                    remark = contact_details.remark.str  # 联系人备注
                    if wxid.endswith("chatroom"):  # 判断是否为群聊
                        group_member_list = contact_details.groupMemberList  # 群成员列表
                        member_count = group_member_list.memberCount  # 群成员数量
                        for group_member in group_member_list.groupMember:  # 遍历群成员
                            member_wxid = group_member.wxid  # 群成员wxid
                            member_nickname = group_member.nickname  # 群成员昵称
                            # print(member_wxid, member_nickname)
                        pass
            else:
                logger.error(data.message)
        elif data.type == GET_CONTACTS_LIST and not data.code:
            logger.error(data.message)
        elif data.type == CREATE_GROUP_CALLBACK:  # 创建群聊回调
            callback = spy_pb2.CreateGroupCallback()
            callback.ParseFromString(data.bytes)
            print(callback)
        elif data.type == GROUP_MEMBER_DETAILS:  # 群成员详情
            group_member_details = spy_pb2.GroupMemberDetails()
            group_member_details.ParseFromString(data.bytes)
            # print(group_member_details)
        elif data.type == GROUP_MEMBER_EVENT:  # 群成员进出事件
            group_member_event = spy_pb2.GroupMemberEvent()
            group_member_event.ParseFromString(data.bytes)
            # print(group_member_event)
        elif data.type == LOGIN_QRCODE:  # 登录二维码
            qrcode = spy_pb2.LoginQRCode()
            qrcode.ParseFromString(data.bytes)
            with open("qrcode.png", "wb") as _wf:
                _wf.write(qrcode.qrcodeBytes)
        elif data.type == GROUP_ENTER_URL:  # 进群链接
            group_enter_url = spy_pb2.GroupEnterUrl()
            group_enter_url.ParseFromString(data.bytes)
            print(group_enter_url)
            # 进群直接post请求链接
            # try:
            #     requests.post(group_enter_url.url)
            # except requests.exceptions.InvalidSchema:
            #     pass
            # except Exception as e:
            #     logger.error(f"进群失败：{e}")
        else:
            print(data)
    except:
        try:
            for staff in conf['staff']:
                spy.send_text(staff, "未知错误，发生于"+time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()))
        except:
            pass



if __name__ == '__main__':
    file = open('key.txt', 'r')
    KEY = file.read()
    file.close()
    
    try:
        file = open('status.json', 'r')
        variables = json.load(file)
        file.close()
    except FileNotFoundError:
        file = open('status.json', 'w')
        variables = {'run': {},
                     'Bot': {},
                     'ano_uuid': {}
                     }
        v = json.dumps(variables)
        file.write(v)
        file.close()
    old_variables = variables
    scheduler = BackgroundScheduler()
    scheduler.add_job(save_status, 'interval', seconds=60)
    scheduler.start()

    spy = WeChatSpy(response_queue=my_response_queue, key=KEY, logger=logger)
    pid = spy.run(r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe")
    while True:
        data = my_response_queue.get()
        handle_response(data)
