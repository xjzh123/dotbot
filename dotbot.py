# -*- coding: utf-8 -*-
'''
dotbot alpha 是 dotbot 的第一个稳定版本，一般可以正常运行。
需要注意的是，请选择合理的执行方式。
目前发现如果使用 Windows 打开方式，直接用 Python 打开，会发生路径错误。
最好使用 cmd，在程序所在目录下使用[python dotbot.py]执行。
基于 Light 制作的 Foolishbird 。
'''

import json
import os
import random
import re
import threading
import time
from multiprocessing import Process, Queue
from tkinter import *
from tkinter import scrolledtext

import websocket

import fanyi


def sendData(text):
    '''
            将发送的内容组装成json数据，以发送到服务器。
    '''
    return json.dumps({"cmd": "chat", "text": str(text)})  # 把后面的部分转换成字符串


class Runbox:  # 自动回复等功能逻辑
    def __init__(self, room, name, logpath):
        # 包含了房间名称，bot的名称
        self.auto = True
        self.room = room
        self.name = name
        self.logpath = logpath
        self.onlineuser = []
        self.colordict = {
            '404r': 'ff5722',
            'r': 'ff5722',
            '404b': 'c0ffee',
            'b': 'c0ffee',
            'wikidot': 'f02727',
            'vscode': '007acc'
        }

    def sendmsg(self, msg):
        '''
                自动调用组装json并发送到服务器。
        '''
        self.ws.send(sendData(msg))

    def wsendmsg(self, msg):
        '''
                自动使用私聊功能私聊触发功能的消息的发送者。
        '''
        self.sendmsg('/whisper '+self.nick+' '+msg)

    def handle(self, json_data, ws):
        '''
                根据不同的服务器数据调用不同的自动回复函数
        '''
        self.ws = ws
        self.json_data = json_data
        if "nick" in self.json_data:
            self.nick = self.json_data["nick"]
        if "text" in self.json_data:
            self.text = self.json_data["text"]
        if "color" in self.json_data:
            self.color = self.json_data["color"]
            if not self.nick in self.colordict.keys():
                self.colordict[self.nick] = self.color
            elif self.colordict[self.nick] != self.color:
                self.colordict[self.nick] = self.color
        if "trip" in self.json_data:
            self.trip = self.json_data["trip"]
        if "nicks" in self.json_data:
            self.nicks = self.json_data["nicks"]
        if "cmd" in self.json_data:    # 如果接受到了包含cmd的json数据
            self.cmd = self.json_data["cmd"]
            if self.auto:
                # 说话类型
                if self.cmd == "chat":
                    self.chat()  # 调用和机器人聊天

                # 用户进入类型
                elif self.cmd == "onlineAdd":
                    self.onlineadd()  # 调用打招呼

                # 进入聊天时用户的列表
                elif self.cmd == "onlineSet":
                    self.onlineset()  # 调用给所有人打招呼

                # 用户离开类型
                elif self.cmd == "onlineRemove":
                    self.onlineremove()

                else:
                    pass

    def chat(self):
        '''
                当返回数据是有人说话时调用
        '''
        if self.text[0:1] == '.':
            self.chatcommand()

    def chatcommand(self):
        '''
                处理聊天命令
        '''
        ccmdtxt = self.text.replace('.', '', 1)
        ccmdlist = ccmdtxt.split(' ', 1)
        ccmd = ccmdlist[0]
        if len(ccmdlist) > 1:
            cobj = ccmdlist[1]
        else:
            cobj = ''
        if ccmd == '':  # 防止“.”触发命令
            pass
        elif '.' in ccmd:  # 防止“...”触发命令
            pass
        elif ccmd == 'help':  # 命令帮助
            self.wsendmsg('''
## [.] + command name + command obj = command

|command name<other names>|command obj|command effect|
|----|----|----|
|color<c>|[the nickname of a user whose nickname has special color]|Gives you a command to change the color of your name. | 
|translate<t,fy>|[what you wanna translate]|Translates the text into English or Chinese. VERY POOR TRANSLATION. Not responsible for the translated content. |
|history<h>|[a number from 1 to how many messages dotbot can show]|Shows you messages which are sent before you use this command. Useful when you are new to a channel and want to know what has happened. May not work. |
|help|[no object]|Shows you how to use the commands above. |
|[more]|[to be developed]|[in the future.]|
            ''')

        elif ccmd == 'c' or ccmd == 'color':  # 快速获取颜色代码
            cobj = cobj.lstrip('@').rstrip()
            if cobj in self.colordict.keys():
                getcolor = self.colordict[cobj]
                self.wsendmsg("`/color #"+getcolor+'`')
            else:
                self.wsendmsg("请输入正确的颜色代码。")

        elif ccmd == 'fy' or ccmd == 't' or ccmd == 'translate':  # 翻译功能，可能由于爬虫检测，翻译质量极差
            self.sendmsg("[youdao translator]"+fanyi.fanyi(cobj) +
                         "\n[not responsible for the translated content. ]")

        elif ccmd == 'history' or ccmd == 'h':  # 聊天记录查询功能
            if cobj.isdigit() == True and len(cobj) > 0:
                cobj = int(cobj)
                # 如果聊天记录小于1mb
                if os.path.getsize(self.logpath) < 1024576:
                    with open(self.logpath, 'r') as chatHistory:
                        historyList = chatHistory.readlines()
                        if cobj >= 1 and cobj <= len(historyList):
                            chstr = ''.join(historyList[-cobj-1:-1])
                            self.wsendmsg('以下是最近的'+str(cobj)+'条消息：\n'+chstr)
                        else:
                            self.wsendmsg(
                                '当前仅记录了'+str(len(historyList)) + '条聊天记录。无法查询'+str(cobj)+'条聊天记录。')
                else:
                    self.wsendmsg('当前记录聊天记录过文件过大。拒绝查询。')
            else:
                self.wsendmsg('请输入合法的查询条数。')
        elif ccmd == 'online' or ccmd == 'o':
            self.wsendmsg('Online user: '+','.join(self.onlineuser))
        else:
            self.wsendmsg(
                'Unknown dotbot command. Use ".help" to get help for dotbot commands. ')  # 未知命令

    def onlineadd(self):
        '''
                当返回数据是有人加入时调用
        '''
        self.onlineuser.append(self.nick)
        self.sendmsg("Hello,{}.".format(self.nick))
        self.wsendmsg(
            "To Chinese user: 可以试试说中文哦。your-channel一般有中国用户，即使有时他们正好都在说英文。\n")

    def onlineset(self):
        '''
                当返回数据是onlineset（加入一个新房间时会发生）将会调用
        '''
        self.onlineuser = self.nicks
        self.sendmsg('/color #ffffff')  # 自动设置名字颜色
        self.sendmsg(
            "Hi! Dotbot is here. \nDotbot is based on Foolishbird by Light and is made by 4n0n4me. ")

    def onlineremove(self):
        '''
                当返回数据是有人离开时调用
        '''
        self.onlineuser.remove(self.nick)


class Main:  # 主进程主要功能
    def __init__(self, room, name, msgToShowQ, msgToSendQ, cmdToExecQ):  # 初始化
        '''
                从ProBot传来的参数
        '''
        self.room = room
        self.name = name
        self.msgToShowQ = msgToShowQ         # 将从hackchat收到的消息发送到Tkhand
        self.msgToSendQ = msgToSendQ         # 接收从Tkhand传来的消息并发送到hackchat
        self.cmdToExecQ = cmdToExecQ         # 接收来自Tkhand 传来的指令
        self.inittime = time.strftime("%Y-%m-%d %H_%M_%S", time.localtime())
        self.logpath = './log/'+self.room+' '+self.inittime+'.txt'
        with open(self.logpath, 'x') as log:  # 创建日志文件
            pass
        self.runbox = Runbox(room, name, self.logpath)   # 处理信息库，主要负责自动回复

    def askMsgToSend(self, ws):
        '''
                从msgToSendQ队列获取界面输入框发送的消息
        '''
        while True:
            if not self.msgToSendQ.empty():
                self.runbox.sendmsg(self.msgToSendQ.get())

    def askCmdToExec(self, ws):  # 控制bot的命令
        '''
                从cmdToExecQ队列获取界面命令框执行的命令
        '''
        while True:
            if not self.cmdToExecQ.empty():
                execing = self.cmdToExecQ.get().strip()  # 获取cmdToExecQ；移除字符串头尾的空格

                cmd_name = r"(\w+) \[.+\]"  # r声明字符串不转义。这些是正则表达式
                obj = r"\w+ \[(.+)\]"
                alone_cmd = r"^(\w+)$"

                cmd_name_m = re.findall(cmd_name, execing)
                obj_m = re.findall(obj, execing)
                alone_cmd_m = re.findall(alone_cmd, execing)
                try:
                    cmd = cmd_name_m[0]
                    obj = obj_m[0]
                except:
                    cmd = None
                    obj = None

                try:
                    alone_cmd = alone_cmd_m[0]
                except:
                    alone_cmd = None

                # cmd : 命令的名称
                ## args : 包含命令的列表
                # obj : 对象的名称

                if cmd == "fuck":  # 怼人，有怼的对象就艾特他，没有就直接怼人
                    with open("./ma.txt", "r") as fp:
                        ma_list = fp.readlines()
                        if obj != "":
                            self.msgToSendQ.put(
                                "@{},{}".format(obj, random.choice(ma_list)))
                        else:
                            self.msgToSendQ.put(
                                "{}".format(random.choice(ma_list)))

    def tkshow(self, text):
        '''
                将需要显示的内容发送到msgToShow队列，并写入聊天记录
        '''
        self.msgToShowQ.put(text)
        with open(self.logpath, 'a') as chatHistory:
            if os.path.getsize(self.logpath) < 1024576:
                chatHistory.write(text + '\n')

    def on_message(self, ws, message):
        '''
                服务器有数据返回时调用，根据不同的服务器数据调用自动回复与显示到界面聊天框
        '''
        js_ms = json.loads(message)  # 把信息装载成json
        # print('######\n'+message+'\n######')
        self.runbox.handle(js_ms, ws)
        # 向界面发送需要显示在聊天框的内容
        if js_ms["cmd"] == "emote":
            self.tkshow("[INFO]:{}".format(js_ms["text"]))
        if js_ms["cmd"] == "onlineSet":  # 显示在线用户
            self.tkshow('Online user: '+','.join(js_ms["nicks"]))
        if js_ms["cmd"] == "chat":
            self.tkshow("{}:{}".format(js_ms["nick"], js_ms["text"]))  # 直接转述
        if js_ms["cmd"] == "onlineAdd":
            self.tkshow("* {} join".format(js_ms["nick"]))  # 显示有人加入
        if js_ms["cmd"] == "onlineRemove":
            self.tkshow("* {} left".format(js_ms["nick"]))  # 显示有人离开
        if js_ms["cmd"] == "info":
            self.tkshow("[INFO]:{}".format(js_ms["text"]))  # 显示信息

    def on_error(self, ws, error):
        '''
            如果发生错误了则调用
        '''
        self.tkshow("error:{}".format(error))

    def on_close(self, ws):
        '''
            如果退出了则调用
        '''
        print("### closed ###")

    def on_open(self, ws):
        '''
            连接上服务器了则调用
        '''
        self.readmsgToSendQ = threading.Thread(
            target=self.askMsgToSend, args=(ws,))
        self.readmsgToSendQ.start()
        self.readcmdToExecQ = threading.Thread(
            target=self.askCmdToExec, args=(ws,))
        self.readcmdToExecQ.start()
        ws.send(json.dumps({"cmd": "join", "channel": str(
            self.room), "nick": str(self.name)}))


class Tkhand(Process):  # 用户界面控制
    def __init__(self, msgToShowQ, msgToSendQ, cmdToExecQ):
        Process.__init__(self)
        self.msgToShowQ = msgToShowQ
        self.msgToSendQ = msgToSendQ
        self.cmdToExecQ = cmdToExecQ

    def run(self):
        '''
                定义进程活动。显示界面。
        '''
        # tkinter 框架
        # row 行
        # column 列
        # sticky
        self.top = Tk()
        self.top.title("Control")
        # self.top.configure(bg="#FAF9DE")
        self.show_text = scrolledtext.ScrolledText(
            self.top, width=105, relief=GROOVE, height=35)
        self.show_text.grid(row=0, column=0, columnspan=2)

        self.enter_text = scrolledtext.ScrolledText(
            self.top, width=88, height=5, relief=GROOVE)
        self.enter_text.grid(row=2, column=0, rowspan=1, ipady=0)

        self.send_button = Button(
            self.top, text="SEND", width=15, relief=GROOVE, height=3, command=self.sendmsg)
        self.send_button.grid(row=2, column=1, rowspan=1)

        self.exec_button = Button(
            self.top, text="EXEC", width=15, height=1, relief=GROOVE, command=self.exec)
        self.exec_button.grid(row=1, column=1, sticky="s")

        self.exec_label = Label(self.top, text="$")
        self.exec_label.grid(row=1, column=0, padx=3, sticky="w")

        self.exec_text = Text(self.top, width=85, height="1p",
                              relief=GROOVE, foreground="red")
        self.exec_text.grid(row=1, column=0, sticky="e", ipady=6)

        #self.exec_s = Text(self.top,width=55,height=1,relief=GROOVE,foreground="blue")
        # self.exec_s.grid(row=1,column=0,columnspan=2,sticky="w")

        # threadread以线程的形式一直运行
        self.readmsgToShowQ = threading.Thread(target=self.askMsgToShow)
        self.readmsgToShowQ.start()

        self.top.mainloop()

    def askMsgToShow(self):
        '''
                从msgToShowQ队列获取消息
        '''
        while True:
            if not self.msgToShowQ.empty():
                self.show_text.insert(END, self.msgToShowQ.get())
                self.show_text.insert(END, "\n\n")
                self.show_text.see(END)

    def sendmsg(self):
        '''
                将输入框中的信息发送到msgToSendQ队列
        '''
        msg = self.enter_text.get(1.0, END)
        if msg != "":
            self.enter_text.delete(1.0, END)
            self.msgToSendQ.put(msg)

    def exec(self):
        self.cmdToExecQ.put(self.exec_text.get(1.0, END).strip())


class ProBot(Process):  # 继承进程类，定义Bot进程：由main处理信息；连接服务器
    def __init__(self, hcroom, botname, msgToShowQ, msgToSendQ, cmdToExecQ):
        '''
                hcroom:聊天室名称
                botname:机器人的名称
                msgToShowQ:队列，从Main发送到Tkhand
                msgToSendQ:队列，从Tkhand发送到Main
                cmdToExecQ:队列，从Tkhand发送到Main
        '''
        Process.__init__(self)
        self.main = Main(room=hcroom, name=botname, msgToShowQ=msgToShowQ,
                         msgToSendQ=msgToSendQ, cmdToExecQ=cmdToExecQ)  # 处理服务器传来的信息

    def run(self):
        '''
                定义进程活动。Probot进程连接hackchat，定义了服务器发送信息、出现错误、从服务器踢出时执行的方法。
        '''
        websocket.enableTrace(False)  # 禁用控制台输出
        ws = websocket.WebSocketApp("wss://hack.chat/chat-ws",
                                    on_message=self.main.on_message,
                                    on_error=self.main.on_error,
                                    on_close=self.main.on_close)
        ws.on_open = self.main.on_open
        ws.run_forever()


if __name__ == '__main__':
    print('### main ###')
    hcroom = input('input room name. e.g: your-channel. ')
    if hcroom == 'yc':
        hcroom = 'your-channel'
    elif hcroom == 'ts':
        hcroom = 'test'
    elif hcroom.lower() == 'cn':
        hcroom = 'chinese'
    msgToShowQ = Queue()   # 如果收到消息就发送到这个队列，并由Tkhand显示出内容
    msgToSendQ = Queue()   # 在Tkhand中把消息发送到ttomp这个队列，并由main处理发送到hackchat
    cmdToExecQ = Queue()   # 在Tkhand中把指令发送到cmdToExecQ这个队列，并在main中处理
    # 2个进程处理后端和前端
    p1 = ProBot(hcroom=hcroom, botname="dotbot", msgToShowQ=msgToShowQ,
                msgToSendQ=msgToSendQ, cmdToExecQ=cmdToExecQ)
    p2 = Tkhand(msgToShowQ=msgToShowQ,
                msgToSendQ=msgToSendQ, cmdToExecQ=cmdToExecQ)
    p1.start()
    p2.start()
    p1.join()
    p1.join()
