import json
import os
import time
from calendar import monthcalendar
from random import randint
from socket import socket
from threading import Thread
from tkinter import Event
from webbrowser import open_new
from winsound import PlaySound
from zipfile import ZipFile

import constants
import tkintertools
import tools

__author__ = '小康2022'
__version__ = '2.6.0'


# 创建窗口并使其居中于屏幕
root = tkintertools.Tk('超级游戏盒子', '1000x500', shutdown=lambda: close())
root.geometry('1000x500+%d+%d' % (
    (root.winfo_screenwidth() - 1000) // 2,
    (root.winfo_screenheight() - 500) // 2))


# 加载程序默认的设定值
with open('config.json', 'r', encoding='utf-8') as config:
    config: dict[str, str] = json.load(config)
# 加载程序所需的资源的路径
with open('path.json', 'r', encoding='utf-8') as path:
    path: dict[str, str] = json.load(path)


# 资源字典初始化
res: dict[str, dict[str, tkintertools.PhotoImage]] = {
    'main': {},
    'chess': [],
    'gobang': {},
    'snake': {}
}


def loader():
    """ 资源加载生成器 """

    res['main']['login'] = tkintertools.PhotoImage(path['login'])
    for _ in res['main']['login'].parse():
        yield 1, '正在加载登录界面资源...'

    res['main']['home'] = tkintertools.PhotoImage(path['home'])
    for _ in res['main']['home'].parse():
        yield 1, '正在加载主界面资源...'

    for image in path['chinachess']:
        res['chess'].append(tkintertools.PhotoImage(image))
        yield 1, '正在加载游戏资源...'

    res['gobang']['background'] = tkintertools.PhotoImage(
        path['gobang']['background'])
    res['gobang']['white'] = tkintertools.PhotoImage(
        path['gobang']['white'])
    res['gobang']['black'] = tkintertools.PhotoImage(
        path['gobang']['black'])

    yield 3, '加载完毕！'


class PageLoad:
    """ 加载界面 """

    canvas = tkintertools.Canvas(root, 1000, 500)
    image_list = [tkintertools.PhotoImage(path['face_1']),
                  tkintertools.PhotoImage(path['face_2']),
                  tkintertools.PhotoImage(path['face_3'])]
    background_list = [canvas.create_image(500, 250, image=image_list[0]),
                       canvas.create_image(1500, 250, image=image_list[1]),
                       canvas.create_image(2500, 250, image=image_list[2])]
    kw = {'text': '超级游戏盒子', 'font': ('consolas', 80, 'bold')}
    canvas.create_text(502, 142, fill='grey', **kw)
    canvas.create_text(500, 140, fill='yellow', **kw)
    tkintertools.CanvasLabel(canvas, -1, 415, 1001, 86, 0,
                             color_fill=('#1F1F1F', '#1F1F1F'),
                             color_outline=('grey', '#F1F1F1'))
    canvas.create_text(
        500, 240, font=('楷体', 15), justify='center',
        text='—— Made By 小康2022 ——\nv%s' % __version__, fill='white')
    canvas.create_text(500, 488, text=constants.HEALTH, fill='white')
    bar = tkintertools.ProcessBar(canvas, 50, 450, 900, 25, borderwidth=2,
                                  color_outline=('grey', 'white'),
                                  color_bar=('', 'orange'),
                                  color_text=('white', 'white', 'white'))
    info = canvas.create_text(
        500, 435, font=('楷体', 15), fill='white', text='正在连接服务器...')
    canvas.place(x=0, y=0)

    loader = loader()

    @classmethod
    def __init__(cls):
        root.after(5000, cls.face_change)
        Thread(target=Client.connect, daemon=True).start()

    @classmethod
    def face_change(cls) -> None:
        """ 封面切换 """
        if PageLogin.canvas.lock:
            return
        for bg in cls.background_list:
            if cls.canvas.coords(bg)[0] < -100:
                cls.canvas.move(bg, 3000*cls.canvas.rate_x, 0)
            tkintertools.move(
                cls.canvas, bg, -1000*cls.canvas.rate_x, 0, 250, 'smooth')
        root.after(5000, cls.face_change)

    @classmethod
    def update(cls, size: int) -> None:
        """ 更新文件 """
        open('Temp', 'w').close()  # 清除文件
        file, _size = open('Temp', 'ab'), 0
        try:
            while size-_size:
                download = Client.client.recv(8192)
                if not download:
                    raise TimeoutError
                _size += len(download)
                cls.canvas.itemconfigure(
                    cls.info, text='正在下载更新文件...%.1fMB/%.1fMB' % (_size/1048576, size/1048576))
                cls.bar.load(_size/size)
                file.write(download)
            file.close()
            cls.canvas.itemconfigure(cls.info, text='正在解压资源...')
            Thread(target=cls.unzip, daemon=True).start()
        except TimeoutError:
            tools.Popup(root, '更新中断', '网络波动异常！\n请重新更新！',
                        ('取消更新', close), ('重新更新', Thread(target=Client.reconnect, daemon=True).start))

    @classmethod
    def unzip(cls) -> None:
        """ 解压文件 """
        try:
            with ZipFile("Temp", "r") as res:
                res.extractall()
            cls.canvas.itemconfigure(cls.info, text='更新完成！')
            os.remove("Temp")
            tools.Popup(root, '更新成功', '已完成更新！\n请重新启动客户端！',
                        ('', None), ('关闭程序', close))
        except:
            tools.Popup(root, '解压失败', '更新文件不完整或已损坏！\n请重新更新！',
                        ('取消', close), ('重新更新', Thread(target=Client.reconnect, daemon=True).start))

    @classmethod
    def load(cls, delta, text, num: int = 0) -> None:
        """ 加载文件 """
        cls.bar.load(num/88)
        cls.canvas.itemconfigure(cls.info, text=text)
        try:
            cls.canvas.after(1, cls.load, *next(cls.loader), num+delta)
        except StopIteration:
            cls.canvas.destroy()
            PageLogin.canvas.place(x=0, y=0)
            PageLogin.canvas.set_lock(True)
            res['main']['login'].play(
                PageLogin.canvas, PageLogin.background, 10)


class PageLogin:
    """ 登录界面 """

    canvas = tkintertools.Canvas(root, 1000, 500, False, bg='black')
    background = canvas.create_image(500, 220)
    canvas.create_text(
        502, 82, text='超级游戏盒子',
        font=('consolas', 70, 'bold'),
        fill='grey')
    canvas.create_text(
        500, 80, text='超级游戏盒子',
        font=('consolas', 70, 'bold'),
        fill='white')
    canvas.create_text(
        5, 500 - 5, text='版本:v%s\n作者:小康2022' % __version__,
        anchor='sw', fill='grey',
        font=('楷体', 12))

    widget_login: list[tkintertools.CanvasEntry | tkintertools.CanvasButton] = [
        tkintertools.CanvasEntry(  # 账号输入框
            canvas, 375, 310, 250, 30, 5,
            ('账 号', '点击输入账号'),
            justify='center',
            color_text=('grey', 'white', 'white'),
            color_fill=tkintertools.COLOR_NONE,
            color_outline=('grey', 'white', 'white')),
        tkintertools.CanvasEntry(  # 密码输入框
            canvas, 375, 350, 250, 30, 5,
            ('密 码', '点击输入密码'), '•',
            justify='center',
            color_text=('grey', 'white', 'white'),
            color_fill=tkintertools.COLOR_NONE,
            color_outline=('grey', 'white', 'white')),
        tkintertools.CanvasButton(  # 注册按钮
            canvas, 375, 390, 120, 30, 5, '注 册',
            command=lambda: PageLogin.page_change(1),
            color_text=('grey', 'orange', 'orange'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'orange', 'orange')),
        tkintertools.CanvasButton(  # 登录按钮
            canvas, 505, 390, 120, 30, 5, '登 录',
            command=lambda: PageLogin.login(),
            color_text=('grey', 'springgreen', 'springgreen'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'springgreen', 'springgreen'))]

    widget_register: list[tkintertools.CanvasEntry | tkintertools.CanvasButton] = [
        tkintertools.CanvasEntry(  # 新账号输入框
            canvas, -625, 310, 250, 30, 5,
            ('新 账 号', '点击输入新账号'),
            justify='center',
            color_text=('grey', 'white', 'white'),
            color_fill=tkintertools.COLOR_NONE,
            color_outline=('grey', 'white', 'white')),
        tkintertools.CanvasEntry(  # 新密码输入框
            canvas, -625, 350, 250, 30, 5,
            ('新 密 码', '点击输入新密码'),
            justify='center',
            color_text=('grey', 'white', 'white'),
            color_fill=tkintertools.COLOR_NONE,
            color_outline=('grey', 'white', 'white')),
        tkintertools.CanvasButton(  # 确定注册按钮
            canvas, -625, 390, 120, 30, 5, '确 定',
            command=lambda: PageLogin.register(),
            color_text=('grey', 'springgreen', 'springgreen'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'springgreen', 'springgreen')),
        tkintertools.CanvasButton(  # 返回按钮
            canvas, -495, 390, 120, 30, 5, '返 回',
            command=lambda: PageLogin.page_change(-1),
            color_text=('grey', 'cyan', 'cyan'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'cyan', 'cyan'))]

    if config['account']:
        widget_login[0].set(config['account'])  # 显示默认账号（上次登录）
        widget_login[1].set(config['password'])  # 显示默认密码（上次登录）

    @classmethod
    def page_change(cls, key: int, ind: int = 0):
        """ 页面切换 """
        if key == 1:
            lis = cls.widget_login + cls.widget_register
        else:
            lis = cls.widget_register + cls.widget_login
        tkintertools.move(
            cls.canvas, lis[ind], key * 1000 * cls.canvas.rate_x, 0, 350, 'rebound', 60)
        if ind != 7:
            cls.canvas.after(40, cls.page_change, key, ind+1)

    @classmethod
    def login(cls):
        """ 登录账号 """
        if cls.canvas.lock:
            if not cls.widget_login[0].value:
                tools.Tip(cls.canvas, '— 提示 —\n请您输入账号!').fly(3)
            elif not cls.widget_login[1].value:
                tools.Tip(cls.canvas, '— 提示 —\n请您输入密码!').fly(3)
            else:
                Client.send(
                    cmd='Login', act=cls.widget_login[0].value, psd=cls.widget_login[1].value)

                if Client.recv()['value']:
                    config['account'] = cls.widget_login[0].value
                    config['password'] = cls.widget_login[1].value
                    with open('config.json', 'w') as file:
                        json.dump(config, file)

                    PageHome()
                else:
                    tools.Tip(cls.canvas, '— 提示 —\n账号或密码有误!').fly(3)

    @classmethod
    def register(cls):
        """ 注册账号 """
        if not cls.widget_register[0].value:
            tools.Tip(cls.canvas, '— 提示 —\n请您输入新账号!').fly(3)
        elif not cls.widget_register[1].value:
            tools.Tip(cls.canvas, '— 提示 —\n请您输入新密码!').fly(3)
        else:
            Client.send(
                cmd='Register', act=cls.widget_register[0].value, psd=cls.widget_register[1].value)
            if Client.recv()['value']:
                cls.page_change(-1)
                cls.widget_login[0].set(cls.widget_register[0].value)
                cls.widget_login[1].set(cls.widget_register[1].value)
                tools.Tip(cls.canvas, '— 提示 —\n注册成功!').fly(3)
            else:
                tools.Tip(cls.canvas, '— 提示 —\n账号已存在!').fly(3)


class PageHome(tkintertools.Singleton):
    """ 主界面 """

    # 创建主界面画布
    canvas = tkintertools.Canvas(root, 1000, 500, False, bg='#1F1F1F')
    canvas.place(x=0, y=-500)

    tkintertools.CanvasLabel(canvas, -1, -1, 1001, 71, 0,
                             color_fill=('black', 'black'),
                             color_outline=('grey', 'white'))
    tkintertools.CanvasLabel(canvas, -1, 430, 1001, 71, 0,
                             color_fill=('black', 'black'),
                             color_outline=('grey', 'white'))

    tkintertools.CanvasButton(canvas, 10, 10, 50, 50, 5,
                              color_fill=tkintertools.COLOR_NONE,
                              color_outline=('grey', 'white', 'white'))
    tkintertools.ProcessBar(canvas, 70, 40, 200, 15,
                            color_outline=('grey', 'white'),
                            color_bar=('', '#444'),
                            color_text=tkintertools.COLOR_NONE).load(0.5)

    head = tkintertools.PhotoImage(path['head_'])
    head = canvas.create_image(35, 35, image=head)

    # 账号名称显示
    name = canvas.create_text(70, 25, fill='cyan', font=('楷体', 15), anchor='w')
    # 延迟显示
    delay = canvas.create_text(
        930, 465, fill='white', font=('楷体', 15), text='-ms')

    tkintertools.CanvasButton(canvas, 340, 20, 120, 30, 5, '签 到',
                              command=lambda: PageHome.function_attendance(),
                              color_text=('grey', 'orange', 'orange'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'orange', 'orange'))
    tkintertools.CanvasButton(canvas, 470, 20, 120, 30, 5, '聊 天',
                              command=lambda: PageHome.function_talk(),
                              color_text=('grey', 'yellow', 'yellow'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'yellow', 'yellow'))
    tkintertools.CanvasButton(canvas, 600, 20, 120, 30, 5, '邮 箱',
                              command=lambda: PageHome.function_mailbox(),
                              color_text=('grey', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'springgreen', 'springgreen'))
    tkintertools.CanvasButton(canvas, 730, 20, 120, 30, 5, '背 包',
                              command=lambda: PageHome.function_backpack(),
                              color_text=('grey', 'cyan', 'cyan'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'cyan', 'cyan'))
    tkintertools.CanvasButton(canvas, 860, 20, 120, 30, 5, '设 置',
                              command=lambda: PageHome.function_set(),
                              color_text=('grey', 'white', 'white'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'white', 'white'))
    tkintertools.CanvasButton(canvas, 310, 450, 120, 30, 5, '支持作者',
                              command=lambda: PageHome.function_like(),
                              color_text=('grey', 'yellow', 'yellow'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'yellow', 'yellow'))
    tkintertools.CanvasButton(canvas, 440, 450, 120, 30, 5, '游戏公告',
                              command=lambda: PageHome.function_announcement(),
                              color_text=('grey', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'springgreen', 'springgreen'))
    tkintertools.CanvasButton(canvas, 570, 450, 120, 30, 5, '反馈问题',
                              command=lambda: PageHome.function_feedback(),
                              color_text=('grey', 'cyan', 'cyan'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'cyan', 'cyan'))

    # 中国象棋游戏卡
    text = '[网络游戏]\n两军对阵!\n究竟谁才是最后的赢家?' + '\n' * 6
    chinachess = tools.GameCard(
        canvas, '1.中国象棋', 'red', text, 20, 100, 250, 400)
    chinachess.start.command = lambda: PageHome.play('中国象棋')

    # 五子棋游戏卡
    text = '[网络游戏]\n简单且益智!\n快来玩五子棋吧!' + '\n' * 6
    gobang = tools.GameCard(canvas, '2.五子棋', 'orange',
                            text, 260, 100, 490, 400)
    gobang.start.command = lambda: PageHome.play('五子棋')

    # 大鱼吃小鱼游戏卡
    text = '[单机游戏]\n一款简单朴实的\n休闲小游戏!' + '\n' * 6
    fish = tools.GameCard(canvas, '3.大鱼吃小鱼', 'yellow',
                          text, 500, 100, 730, 400)
    fish.start.command = lambda: PageHome.play('大鱼吃小鱼')

    # 贪吃蛇游戏卡
    text = '[经典游戏]\n经典贪吃蛇!\n吃到撑为止!' + '\n' * 6
    snake = tools.GameCard(
        canvas, '4.贪吃蛇', 'springgreen', text, 740, 100, 970, 400)
    snake.start.command = lambda: PageHome.play('贪吃蛇')

    # 2048游戏卡
    text = '[单机游戏]\n挑战你的智力吧！\n最强大佬就是你了!' + '\n' * 6
    num = tools.GameCard(canvas, '5.2048', 'lightgreen',
                         text, 980, 100, 1210, 400)
    num.start.command = lambda: PageHome.play('2048')

    # 生存游戏卡
    text = '[竞技游戏]\n新式2.5D游戏!\n小心点，别挂了!' + '\n' * 6
    fight = tools.GameCard(canvas, '6.生存', 'cyan', text, 1220, 100, 1450, 400)
    fight.start.command = lambda: PageHome.play('生存')

    # 跑酷游戏卡
    text = '[单机游戏]\n跑酷小游戏!\n一直跑，不要停!' + '\n' * 6
    run = tools.GameCard(canvas, '7.跑酷', 'purple', text, 1460, 100, 1690, 400)
    run.start.command = lambda: PageHome.play('跑酷')

    # 俄罗斯方块游戏卡
    text = '[经典游戏]\n经典俄罗斯方块!\n又消去一行!' + '\n' * 6
    tetris = tools.GameCard(canvas, '8.俄罗斯方块', 'pink',
                            text, 1700, 100, 1930, 400)
    tetris.start.command = lambda: PageHome.play('俄罗斯方块')

    # 扫雷游戏卡
    text = '[经典游戏]\n还原经典扫雷游戏!\n踩雷了哇哇哇!' + '\n' * 6
    boom = tools.GameCard(canvas, '9.扫雷', 'gold', text, 1940, 100, 2170, 400)
    boom.start.command = lambda: PageHome.play('扫雷')

    # 翻翻棋游戏卡
    text = '[棋类游戏]\n中国象棋的改版游戏!\n你的运气还不够好!' + '\n' * 6
    flip = tools.GameCard(canvas, '10.翻翻棋', 'white',
                          text, 2180, 100, 2410, 400)
    flip.start.command = lambda: PageHome.play('翻翻棋')

    _ = tkintertools.PhotoImage(path['_chinachess'])
    canvas.itemconfigure(chinachess.image, image=_)
    _ = tkintertools.PhotoImage(path['_gobang'])
    canvas.itemconfigure(gobang.image, image=_)

    # 游戏卡片栏列表
    widget = [chinachess, gobang, fish, snake, num,
              fight, run, tetris, boom, flip]

    # 鼠标左键按下的横坐标
    move_x = None
    # 游戏栏范围控制变量
    game_x = 0

    # 绑定鼠标左键按下
    root.bind('<Button-1>', lambda event: PageHome.bind_b1_button(event))
    # 绑定鼠标左键按下移动
    root.bind('<B1-Motion>', lambda event: PageHome.bind_b1_motion(event))
    # 绑定鼠标滚轮滚动
    root.bind('<MouseWheel>', lambda event: PageHome.bind_mousewheel(event))

    @classmethod
    def __init__(cls):
        cls.canvas.itemconfigure(
            cls.name, text=PageLogin.widget_login[0].value)
        tkintertools.move(root, cls.canvas, 0, 500, 500, 'smooth')
        tkintertools.move(root, PageLogin.canvas, 0, 500, 500, 'smooth')
        PageLogin.canvas.set_lock(False)
        cls.canvas.set_lock(True)
        cls.function_announcement()
        Thread(target=Client.check_delay, daemon=True).start()

    @classmethod
    def play(cls, game: str):
        """ 开始游戏 """
        # 关闭界面锁
        cls.canvas.set_lock(False)
        cls.canvas.place_forget()
        # 打开游戏房间界面锁
        Room.display(game)

    @classmethod
    def bind_mousewheel(cls, event: Event):
        """ 绑定鼠标滚轮 """
        if cls.canvas.lock:
            dx = event.delta * cls.canvas.rate_x * 2
            # 更新游戏栏位置数据
            cls.game_x -= dx / cls.canvas.rate_x

            if cls.game_x < 0:
                # 左移限制
                dx += cls.game_x * cls.canvas.rate_x
                cls.game_x = 0
            if cls.game_x > 1430:
                # 右移限制
                dx += (cls.game_x - 1430) * cls.canvas.rate_x
                cls.game_x = 1430

            for widget in cls.widget:
                # 移动游戏卡片栏
                widget.move(dx)

    @classmethod
    def bind_b1_button(cls, event: Event):
        """ 记录鼠标左键按下的位置 """
        if cls.canvas.lock:
            # 更新鼠标左键按下的位置数据
            cls.move_x = event.x

    @classmethod
    def bind_b1_motion(cls, event: Event):
        """ 更新鼠标左键拖动位置 """
        if cls.canvas.lock:
            dx = event.x - cls.move_x
            # 更新鼠标左键按下的位置数据
            cls.move_x += dx
            # 更新游戏栏位置数据
            cls.game_x -= dx / cls.canvas.rate_x

            if cls.game_x < 0:
                # 左移限制
                dx += cls.game_x * cls.canvas.rate_x
                cls.game_x = 0
            if cls.game_x > 1430:
                # 右移限制
                dx += (cls.game_x - 1430) * cls.canvas.rate_x
                cls.game_x = 1430
            for widget in cls.widget:
                # 移动游戏卡片栏
                widget.move(dx)

    @classmethod
    def function_attendance(cls):
        """ 签到按钮功能函数 """
        if cls.canvas.lock:
            if not Client.flag:
                # 没有网络
                tools.Tip(cls.canvas, '— 提示 —\n无法连接至服务器!',
                          bg='#1F1F1F').fly(3)
            else:
                cls.canvas.set_lock(False)
                cls.canvas.place_forget()
                Attendance.display()

    @classmethod
    def function_talk(cls):
        """ 聊天按钮功能函数 """
        if cls.canvas.lock:
            if not Client.flag:
                # 没有网络
                tools.Tip(cls.canvas, '— 提示 —\n无法连接至服务器!',
                          bg='#1F1F1F').fly(3)
            # else:
            #     cls.canvas.set_lock(False)
            #     cls.canvas.place_forget()
            #     Talk.display()

    @classmethod
    def function_mailbox(cls):
        """ 邮箱按钮功能函数 """
        if cls.canvas.lock:
            if not Client.flag:
                # 没有网络
                tools.Tip(cls.canvas, '— 提示 —\n无法连接至服务器!',
                          bg='#1F1F1F').fly(3)
            else:
                tools.Tip(cls.canvas, '— 提示 —\n功能正在开发!', bg='#1F1F1F').fly(3)

    @classmethod
    def function_backpack(cls):
        """ 背包按钮功能函数 """
        if cls.canvas.lock:
            if not Client.flag:
                # 没有网络
                tools.Tip(cls.canvas, '— 提示 —\n无法连接至服务器!',
                          bg='#1F1F1F').fly(3)
            else:
                tools.Tip(cls.canvas, '— 提示 —\n功能正在开发!', bg='#1F1F1F').fly(3)

    @classmethod
    def function_set(cls):
        """ 设置按钮功能函数 """
        if cls.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            Set.display()

    @classmethod
    def function_like(cls):
        """ 支持按钮功能函数 """
        if cls.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            Like.display()

    @classmethod
    def function_announcement(cls):
        """ 游戏公告按钮功能函数 """
        if cls.canvas.lock:
            if not Client.flag:
                # 没有网络
                tools.Tip(cls.canvas, '— 提示 —\n无法连接至服务器!',
                          bg='#1F1F1F').fly(3)
            else:
                cls.canvas.set_lock(False)
                Announcement.display()

    @classmethod
    def function_feedback(cls):
        """ 反馈按钮功能函数 """
        if cls.canvas.lock:
            if not Client.flag:
                # 没有网络
                tools.Tip(cls.canvas, '— 提示 —\n无法连接至服务器!',
                          bg='#1F1F1F').fly(3)
            else:
                cls.canvas.set_lock(False)
                cls.canvas.place_forget()
                Feedback.display()


class Attendance(tkintertools.Singleton):
    """ 签到页面 """

    canvas = tkintertools.Canvas(root, 1000, 500, False)
    background = tkintertools.PhotoImage(path['attendance'])
    canvas.create_image(500, 250, image=background)
    gold5 = tkintertools.PhotoImage(path['gold5'])
    gold10 = tkintertools.PhotoImage(path['gold10'])

    canvas.create_text(360, 40,
                       text='— 签到 —',
                       font=('楷体', 40),
                       fill='white')

    tkintertools.CanvasLabel(canvas, 10, 130, 710, 360, 5,
                             color_fill=('', '', 'grey'),
                             color_outline=('grey', 'white', 'white'))
    tkintertools.CanvasLabel(canvas,
                             730, 130, 260, 360, 5,
                             '签到奖励' + '\n' * 11,
                             font=('楷体', 20),
                             color_text=('grey', 'white', 'white'),
                             color_fill=('', '', 'grey'),
                             color_outline=('grey', 'white', 'white'))
    tkintertools.CanvasLabel(canvas, 740, 190, 240, 240, 5,
                             color_fill=('', '', 'grey'),
                             color_outline=('grey', 'white', 'white'))

    tkintertools.CanvasButton(canvas, 890, 10, 100, 30, 5, '返 回',
                              command=lambda: Attendance.back(),
                              color_text=('grey', 'yellow', 'yellow'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'yellow', 'yellow'))

    date = time.localtime()

    month = monthcalendar(date[0], date[1])

    for i in range(7):
        canvas.create_text(i * 100 + 65, 110,
                           text='星期%s' % '一二三四五六日'[i],
                           font=('楷体', 15),
                           fill='white')

    for y, week in enumerate(month):
        for x, day in enumerate(week):
            if day:
                pos_x, pos_y = x * 100 + 20, y * 70 + 140
                if day == date[2]:
                    # 当天
                    tkintertools.CanvasLabel(canvas, pos_x, pos_y, 90, 60, 5, str(day), font=('楷体', 20),
                                             color_text=(
                        'red', 'springgreen', 'springgreen'),
                        color_fill=('', '', 'grey'),
                        color_outline=('red', 'springgreen', 'springgreen'))
                elif day < date[2]:
                    # 过去
                    tkintertools.CanvasLabel(canvas, pos_x, pos_y, 90, 60, 5, str(day), font=('楷体', 20),
                                             color_text=(
                        'black', 'black', 'black'),
                        color_fill=('', '', 'grey'),
                        color_outline=('black', 'black', 'black'))
                elif x == 5 or x == 6:
                    # 周末
                    tkintertools.CanvasLabel(canvas, pos_x, pos_y, 90, 60, 5, str(day), font=('楷体', 20),
                                             color_text=(
                        'orange', 'springgreen', 'springgreen'),
                        color_fill=('', '', 'grey'),
                        color_outline=('orange', 'springgreen', 'springgreen'))
                else:
                    tkintertools.CanvasLabel(canvas, pos_x, pos_y, 90, 60, 5, str(day), font=('楷体', 20),
                                             color_text=(
                        'grey', 'springgreen', 'springgreen'),
                        color_fill=('', '', 'grey'),
                        color_outline=('grey', 'springgreen', 'springgreen'))

    date_label = tkintertools.CanvasLabel(canvas, 730, 50, 260, 70, 5,
                                          color_text=(
                                              'grey', 'white', 'white'),
                                          color_fill=('', '', 'grey'),
                                          color_outline=('grey', 'white', 'white'))

    tkintertools.CanvasButton(canvas, 810, 445, 100, 30, 5, '领取奖励',
                              command=lambda: Attendance.get_reward(),
                              color_text=('grey', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'springgreen', 'springgreen'))

    reward = canvas.create_image(860, 310)
    reward_text_ = canvas.create_text(862, 362,
                                      font=('方正舒体', 40),
                                      fill='grey')
    reward_text = canvas.create_text(860, 360,
                                     font=('方正舒体', 40),
                                     fill='yellow')

    @classmethod
    def display(cls):
        cls.canvas.place(x=0, y=0)
        cls.canvas.set_lock(True)
        if cls.date[6] == 5 or cls.date[6] == 6:
            cls.canvas.itemconfigure(cls.reward, image=cls.gold10)
            cls.canvas.itemconfigure(cls.reward_text_, text='大捧金币')
            cls.canvas.itemconfigure(cls.reward_text, text='大捧金币')
        else:
            cls.canvas.itemconfigure(cls.reward, image=cls.gold5)
            cls.canvas.itemconfigure(cls.reward_text_, text='小捧金币')
            cls.canvas.itemconfigure(cls.reward_text, text='小捧金币')
        cls.date_label.configure(text='%s年%s月%s日\n星期%s' % (
            cls.date[0], cls.date[1], cls.date[2],
            '一二三四五六日'[cls.date[6]]))

    @classmethod
    def get_reward(cls):
        """ 领取奖励 """

        Client.send(cmd='Attendance',
                    account=config['account'], date=cls.date[:3])

        result = Client.recv()['value']
        if result == True:
            tools.Tip(cls.canvas, '— 提示 —\n领取成功!', bg='#1F1F1F').fly(3)
        elif result == False:
            tools.Tip(cls.canvas, '— 提示 —\n今日已签到!\n请勿重复领取奖励!',
                      bg='#1F1F1F').fly(5)
        elif result == None:
            tools.Tip(cls.canvas, '— 提示 —\n签到异常!', bg='#1F1F1F').fly(3)

    @classmethod
    def back(cls):
        """ 返回 """
        if cls.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            PageHome.canvas.place(x=0, y=0)
            PageHome.canvas.set_lock(True)


# class Talk(tkintertools.Singleton):
#     """ 聊天页面 """

#     canvas = tkintertools.Canvas(root, 1000, 500, False)
#     background = tkintertools.PhotoImage(path['hall'])
#     canvas.create_image(500, 250, image=background)

#     tkintertools.CanvasLabel(canvas, 700, 45, 290,
#                              405, 5, '信息查询' + '\n' * 13, font=('楷体', 20),
#                              color_text=('grey', 'white', 'white'),
#                              color_fill=('', '', 'grey'),
#                              color_outline=('grey', 'white', 'white'))

#     text = canvas.create_text(500, 20,
#                               text='— 聊天大厅 —',
#                               font=('楷体', 20),
#                               fill='white')

#     tkintertools.CanvasButton(canvas, 890, 460, 100, 30, 5, '返 回',
#                               command=lambda: Talk.back(),
#                               color_text=('grey', 'yellow', 'yellow'),
#                               color_fill=('', '', 'grey'),
#                               color_outline=('grey', 'yellow', 'yellow'))

#     tkintertools.CanvasButton(canvas, 590, 460, 100, 30, 5, '发 送',
#                               command=lambda: Talk.send(),
#                               color_text=('grey', 'springgreen',
#                                           'springgreen'),
#                               color_fill=('', '', 'grey'),
#                               color_outline=('grey', 'springgreen', 'springgreen'))

#     message = tkintertools.CanvasText(canvas, 10, 45, 680, 295, 5,
#                                       read=True,
#                                       color_text=('grey', 'white', 'white'),
#                                       color_fill=tkintertools.COLOR_NONE,
#                                       color_outline=('grey', 'white', 'white'))
#     entry = tkintertools.CanvasText(canvas, 10, 350, 680, 100, 5,
#                                     limit=1024,
#                                     color_text=('grey', 'white', 'white'),
#                                     color_fill=tkintertools.COLOR_NONE,
#                                     color_outline=('grey', 'white', 'white'))
#     search = tkintertools.CanvasEntry(canvas,
#                                       710, 100, 200, 30, 5,
#                                       ('账号查询', '点击输入'),
#                                       justify='center',
#                                       color_text=('grey', 'white', 'white'),
#                                       color_fill=tkintertools.COLOR_NONE,
#                                       color_outline=('grey', 'white', 'white'))
#     tkintertools.CanvasButton(canvas, 920, 100, 60, 30, 5, '查询',
#                               command=lambda: Talk.query(),
#                               color_text=('grey', 'orange', 'orange'),
#                               color_fill=('', '', 'grey'),
#                               color_outline=('grey', 'orange', 'orange'))
#     account = canvas.create_text(850, 295,
#                                  font=('楷体', 18),
#                                  fill='white')

#     @classmethod
#     def display(cls):
#         cls.canvas.place(x=0, y=0)
#         cls.canvas.set_lock(True)

#     @classmethod
#     def send(cls):
#         """ 发送消息 """
#         if cls.entry.value:
#             Client.send(
#                 cmd='Chat', account=config['account'], message=cls.entry.get())
#             cls.entry.set('')
#         else:
#             tools.Tip(cls.canvas, '— 提示 —\n请输入消息内容!', bg='#1F1F1F').fly(3)

#     @classmethod
#     def query(cls):
#         """ 查询信息 """
#         if cls.search.value:
#             Client.send(cmd='Query', account=cls.search.value)
#             if (result := Client.recv()['data']) == False:
#                 cls.canvas.itemconfigure(cls.account, text='账号不存在!')
#             else:
#                 cls.canvas.itemconfigure(cls.account,
#                                          text=Account.account(cls.search.value, result))
#         else:
#             tools.Tip(cls.canvas, '— 提示 —\n请输入查询账号!', bg='#1F1F1F').fly(3)

#     @classmethod
#     def back(cls):
#         """ 返回 """
#         if cls.canvas.lock:
#             cls.canvas.set_lock(False)
#             cls.canvas.place_forget()
#             PageHome.canvas.place(x=0, y=0)
#             PageHome.canvas.set_lock(True)


class Set(tkintertools.Singleton):
    """ 设置页面 """

    canvas = tkintertools.Canvas(root, 1000, 500, False)

    canvas.create_line(10, 50, 990, 50)
    canvas.create_line(140, 50, 140, 490)

    tkintertools.CanvasButton(
        canvas, 890, 10, 100, 30, 5, '返回',
        command=lambda: Set.back(),
        color_outline=tkintertools.COLOR_NONE,
        color_fill=('', '#DDD', '#DDD'),
        color_text=('grey', 'black', 'springgreen'))
    general = tkintertools.CanvasButton(
        canvas, 10, 10, 100, 30, 5, '常规',
        command=lambda: Set.change_canvas('general'),
        color_outline=tkintertools.COLOR_NONE,
        color_fill=('#DDD', '#DDD', '#DDD'),
        color_text=('black', 'black', 'black'))
    game = tkintertools.CanvasButton(
        canvas, 111, 10, 100, 30, 5, '游戏',
        command=lambda: Set.change_canvas('game'),
        color_outline=tkintertools.COLOR_NONE,
        color_fill=('', '#DDD', '#DDD'),
        color_text=('grey', 'black', 'black'))
    other = tkintertools.CanvasButton(
        canvas, 212, 10, 100, 30, 5, '其它',
        command=lambda: Set.change_canvas('other'),
        color_outline=tkintertools.COLOR_NONE,
        color_fill=('', '#DDD', '#DDD'),
        color_text=('grey', 'black', 'black'))

    set_general = [
        tkintertools.CanvasButton(
            canvas, 10, 60, 120, 30, 5, '账号',
            command=None,
            color_outline=tkintertools.COLOR_NONE,
            color_fill=('#DDD', '#DDD', '#DDD'),
            color_text=('black', 'black', 'black')),
        tkintertools.CanvasButton(
            canvas, 10, 91, 120, 30, 5, '网络',
            command=None,
            color_outline=tkintertools.COLOR_NONE,
            color_fill=('', '#DDD', '#DDD'),
            color_text=('grey', 'black', 'black')),
        tkintertools.CanvasButton(
            canvas, 10, 122, 120, 30, 5, '窗口',
            command=None,
            color_outline=tkintertools.COLOR_NONE,
            color_fill=('', '#DDD', '#DDD'),
            color_text=('grey', 'black', 'black')),
        tkintertools.CanvasButton(
            canvas, 10, 153, 120, 30, 5, '声音',
            command=None,
            color_outline=tkintertools.COLOR_NONE,
            color_fill=('', '#DDD', '#DDD'),
            color_text=('grey', 'black', 'black')),
        tkintertools.CanvasButton(
            canvas, 10, 184, 120, 30, 5, '账号',
            command=None,
            color_outline=tkintertools.COLOR_NONE,
            color_fill=('', '#DDD', '#DDD'),
            color_text=('grey', 'black', 'black'))]

    @classmethod
    def display(cls):
        cls.canvas.place(x=0, y=0)
        cls.canvas.set_lock(True)

    @classmethod
    def change_canvas(cls, _set: str):
        """ 画布切换 """
        if _set == 'general':
            # 常规设置页
            cls.general.configure(color_fill=('#DDD', '#DDD', '#DDD'),
                                  color_text=('black', 'black', 'black'))
            cls.game.configure(color_fill=('', '#DDD', '#DDD'),
                               color_text=('grey', 'black', 'black'))
            cls.other.configure(color_fill=('', '#DDD', '#DDD'),
                                color_text=('grey', 'black', 'black'))
        elif _set == 'game':
            # 游戏设置页
            cls.game.configure(color_fill=('#DDD', '#DDD', '#DDD'),
                               color_text=('black', 'black', 'black'))
            cls.general.configure(color_fill=('', '#DDD', '#DDD'),
                                  color_text=('grey', 'black', 'black'))
            cls.other.configure(color_fill=('', '#DDD', '#DDD'),
                                color_text=('grey', 'black', 'black'))
        else:
            # 其它设置页
            cls.other.configure(color_fill=('#DDD', '#DDD', '#DDD'),
                                color_text=('black', 'black', 'black'))
            cls.general.configure(color_fill=('', '#DDD', '#DDD'),
                                  color_text=('grey', 'black', 'black'))
            cls.game.configure(color_fill=('', '#DDD', '#DDD'),
                               color_text=('grey', 'black', 'black'))

    @classmethod
    def back(cls):
        """ 返回 """
        if cls.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            PageHome.canvas.place(x=0, y=0)
            PageHome.canvas.set_lock(True)


class Like(tkintertools.Singleton):
    """ 支持作者页面 """

    canvas = tkintertools.Canvas(root, 1000, 500, False)
    background = tkintertools.PhotoImage(path['like'])
    canvas.create_image(500, 250, image=background)
    text = canvas.create_text(500, 680,
                              text=constants.TEXT,
                              font=('楷体', 20),
                              justify='center')

    head = tkintertools.PhotoImage(path['head'])
    canvas.create_image(150, 150, image=head)
    csdn = tkintertools.PhotoImage(path['csdn'])
    canvas.create_image(150, 150, image=csdn)
    canvas.create_text(150, 225, text='CSDN主页!', font=('楷体', 15))
    tkintertools.CanvasButton(canvas, 95, 95, 110, 110, 5,
                              command=lambda: Like.open(1),
                              color_fill=tkintertools.COLOR_NONE,
                              color_outline=('grey', 'white', 'white'))
    code = tkintertools.PhotoImage(path['QRcode'])
    canvas.create_image(150, 300, image=code)
    canvas.create_text(150, 375, text='加QQ细聊!', font=('楷体', 15))
    tkintertools.CanvasLabel(canvas, 95, 245, 110, 110, 5,
                             color_fill=tkintertools.COLOR_NONE,
                             color_outline=('grey', 'skyblue', 'skyblue'))
    good = tkintertools.PhotoImage(path['good'])
    canvas.create_image(850, 150, image=good)
    canvas.create_text(850, 225, text='点赞支持!', font=('楷体', 15))
    tkintertools.CanvasButton(canvas, 795, 95, 110, 110, 5,
                              command=lambda: Like.open(2),
                              color_fill=tkintertools.COLOR_NONE,
                              color_outline=('grey', 'red', 'red'))
    support = tkintertools.PhotoImage(path['support'])
    canvas.create_image(850, 300, image=support)
    canvas.create_text(850, 375, text='打赏作者!', font=('楷体', 15))
    tkintertools.CanvasLabel(canvas, 795, 245, 110, 110, 5,
                             color_fill=tkintertools.COLOR_NONE,
                             color_outline=('grey', 'springgreen', 'springgreen'))

    tkintertools.CanvasButton(canvas, 10, 460, 100, 30, 5, '返 回',
                              command=lambda: Like.back(),
                              color_text=('white', 'cyan', 'cyan'),
                              color_fill=('', '', 'grey'),
                              color_outline=('white', 'cyan', 'cyan'))

    @classmethod
    def display(cls):
        cls.canvas.place(x=0, y=0)
        cls.canvas.set_lock(True)
        cls.play_text()

    @classmethod
    def play_text(cls, move=0):
        """ 文本滚动播放 """
        if move == 0:
            cls.canvas.coords(cls.text,
                              500 * cls.canvas.rate_x, 680 * cls.canvas.rate_y)
        elif move < 440:
            cls.canvas.move(cls.text, 0, -cls.canvas.rate_y)
        if cls.canvas.lock:
            cls.canvas.after(50, cls.play_text, move + 1)

    @classmethod
    def open(cls, page: int):
        """ 打开网页 """
        if cls.canvas.lock:
            if page == 1:
                open_new('https://blog.csdn.net/weixin_62651706')
            else:
                open_new('https://blog.csdn.net/weixin_62651706/category_11600888')

    @classmethod
    def back(cls):
        """ 返回 """
        if cls.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            PageHome.canvas.place(x=0, y=0)
            PageHome.canvas.set_lock(True)


class Announcement(tkintertools.Singleton):
    """ 游戏公告页面 """

    canvas = tkintertools.Canvas(root, 900, 450, False)
    background = tkintertools.PhotoImage(path['like'])
    canvas.create_image(450, 225, image=background)
    canvas.create_text(450, 40, text='— 游戏公告 —', font=('方正舒体', 50))
    tkintertools.CanvasButton(canvas, 400, 410, 100, 30, 5, '我知道了',
                              command=lambda: Announcement.back(),
                              color_text=('grey', 'black', 'black'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'black', 'black'))

    text = tkintertools.CanvasLabel(canvas, 80, 80, 740, 320, 5,
                                    justify='center',
                                    color_text=('grey', 'black', 'black'),
                                    color_fill=('', '', 'grey'),
                                    color_outline=('grey', 'black', 'black'))

    @classmethod
    def display(cls):
        """ 显示界面 """
        cls.canvas.place(x=50, y=25)
        cls.canvas.set_lock(True)
        cls.update()

    @classmethod
    def update(cls):
        """ 接收公告信息 """
        Client.send(cmd='Announcement')
        cls.text.configure(text=Client.recv()['data'])

    @classmethod
    def back(cls):
        """ 返回函数 """
        if not PageHome.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            PageHome.canvas.place(x=0, y=0)
            PageHome.canvas.set_lock(True)


class Feedback(tkintertools.Singleton):
    """ 反馈页面 """

    canvas = tkintertools.Canvas(root,
                                 1000, 500, False,
                                 highlightbackground='grey',
                                 bg='#1F1F1F')
    canvas.create_text(150, 50,
                       text='意见反馈',
                       font=('楷体', 35),
                       fill='grey')
    canvas.create_text(150, 250,
                       text=constants.FEEDBACK,
                       font=('楷体', 15),
                       fill='grey',
                       justify='center')
    tkintertools.CanvasButton(canvas,
                              890, 460, 100, 30,
                              5, '返 回',
                              command=lambda: Feedback.back(),
                              color_text=('grey', 'white', 'white'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'white', 'white'))
    tkintertools.CanvasButton(canvas,
                              780, 460, 100, 30,
                              5, '发 送',
                              command=lambda: Feedback.send(),
                              color_text=('grey', 'white', 'white'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'white', 'white'))

    text = tkintertools.CanvasText(canvas, 300, 10, 690, 440, 5, limit=512,
                                   color_text=('grey', 'white', 'white'),
                                   color_fill=tkintertools.COLOR_NONE,
                                   color_outline=('grey', 'white', 'white'))

    @classmethod
    def display(cls):
        cls.canvas.place(x=0, y=0)
        cls.canvas.set_lock(True)

    @classmethod
    def send(cls):
        """ 发送反馈 """
        if cls.canvas.lock:
            if cls.text.value:
                Client.send(cmd='Feedback',
                            account=config['account'], feedback=cls.text.value)
                tools.Tip(cls.canvas, '— 提示 —\n反馈已发送!', bg='#1F1F1F').fly(3)
                cls.text.set('1')
            else:
                tools.Tip(cls.canvas, '— 提示 —\n请输入内容!', bg='#1F1F1F').fly(3)

    @classmethod
    def back(cls):
        """ 返回 """
        if cls.canvas.lock:
            cls.canvas.set_lock(False)
            cls.canvas.place_forget()
            PageHome.canvas.place(x=0, y=0)
            PageHome.canvas.set_lock(True)


class Room(tkintertools.Singleton):
    """ 网络游戏房间 """

    # 创建画布
    canvas = tkintertools.Canvas(root, 1000, 500, False)
    # 背景图片
    background = tkintertools.PhotoImage(path['room'])
    canvas.create_image(500, 250, image=background)
    # 必要文本显示
    canvas.create_text(500, 160,
                       text='— 请选择模式 —',
                       font=('楷体', 25),
                       fill='white')
    # 游戏标题
    title = canvas.create_text(500, 70,
                               font=('方正舒体', 70),
                               fill='yellow')
    # 模式选中框
    rectangle = canvas.create_rectangle(-3, -3, -3, -3,
                                        outline='yellow', width=4)

    # 网络对抗模式按钮
    mode_1 = tkintertools.CanvasButton(canvas, 150, 250, 100, 100, 5, '网络\n对抗', font=('楷体', 20),
                                       command=lambda: Room.mode_change(
        '网络对抗'),
        color_text=(
        'grey', 'springgreen', 'springgreen'),
        color_fill=('', '', 'grey'),
        color_outline=('grey', 'springgreen', 'springgreen'))

    # 双人对弈模式按钮
    mode_2 = tkintertools.CanvasButton(canvas, 300, 250, 100, 100, 5, '双人\n对弈', font=('楷体', 20),
                                       command=lambda: Room.mode_change(
        '双人对弈'),
        color_text=(
        'grey', 'orange', 'orange'),
        color_fill=('', '', 'grey'),
        color_outline=('grey', 'orange', 'orange'))

    # 人机对战模式按钮
    mode_3 = tkintertools.CanvasButton(canvas, 450, 250, 100, 100, 5, '人机\n对战', font=('楷体', 20),
                                       command=lambda: Room.mode_change(
        '人机对战'),
        color_text=('grey', 'cyan', 'cyan'),
        color_fill=('', '', 'grey'),
        color_outline=('grey', 'cyan', 'cyan'))
    # 单人模式按钮
    mode_4 = tkintertools.CanvasButton(canvas, 600, 250, 100, 100, 5, '单人\n模式', font=('楷体', 20),
                                       command=lambda: Room.mode_change(
        '单人模式'),
        color_text=('grey', 'white', 'white'),
        color_fill=('', '', 'grey'),
        color_outline=('grey', 'white', 'white'))
    # 闯关挑战模式按钮
    mode_5 = tkintertools.CanvasButton(canvas, 750, 250, 100, 100, 5, '闯关\n挑战', font=('楷体', 20),
                                       command=lambda: Room.mode_change(
        '闯关挑战'),
        color_text=(
        'grey', 'magenta', 'magenta'),
        color_fill=('', '', 'grey'),
        color_outline=('grey', 'magenta', 'magenta'))

    # 开始游戏按钮
    begin = tkintertools.CanvasButton(canvas, 440, 450, 120, 30, 5, '开始游戏',
                                      command=lambda: Room.start(),
                                      color_text=('grey', 'red', 'red'),
                                      color_fill=('', '', 'grey'),
                                      color_outline=('grey', 'red', 'red'))

    # 返回按钮
    tkintertools.CanvasButton(canvas, 890, 10, 100, 30, 5, '返 回',
                              command=lambda: Room.back(),
                              color_text=('grey', 'yellow', 'yellow'),
                              color_fill=('', '', 'grey'),
                              color_outline=('grey', 'yellow', 'yellow'))

    canvas_online: list[tkintertools.CanvasLabel | tkintertools.CanvasButton] = [
        tkintertools.CanvasLabel(canvas, 350, -300, 300, 200, 5, '— 选择玩家 —' + '\n' * 4, font=('楷体', 25),
                                 color_text=('grey', 'white', 'white'),
                                 color_fill=('#1F1F1F', '#1F1F1F', '#1F1F1F'),
                                 color_outline=('grey', 'white', 'white')),
        tkintertools.CanvasButton(canvas, 370, -150, 120, 30, 5, '确 定',
                                  command=lambda: Room.online('OK'),
                                  color_text=(
                                      'grey', 'springgreen', 'springgreen'),
                                  color_fill=('', '', 'grey'),
                                  color_outline=('grey', 'springgreen', 'springgreen')),
        tkintertools.CanvasButton(canvas, 510, -150, 120, 30, 5, '取 消',
                                  command=lambda: Room.online('cancel'),
                                  color_text=('grey', 'cyan', 'cyan'),
                                  color_fill=('', '', 'grey'),
                                  color_outline=('grey', 'cyan', 'cyan')),
        tkintertools.CanvasEntry(canvas, 370, -215, 260, 30, 5, ('对方账号或IP', '点击输入对方账号或IP'),
                                 justify='center',
                                 color_text=('grey', 'white', 'white'),
                                 color_fill=tkintertools.COLOR_NONE,
                                 color_outline=('grey', 'white', 'white'))]

    # 房间游戏类型
    game = ''
    # 当前选中的模式（默认为没有选择）
    mode = ''
    # 连接下拉框标识
    canvas_online_flag = False

    @classmethod
    def display(cls, game: str):
        cls.canvas.place(x=0, y=0)
        cls.canvas.set_lock(True)
        # 确定房间游戏类型
        cls.game = game
        # 放置画布（显示出来）
        cls.canvas.place(x=0, y=0)
        # 设置房间游戏标题
        cls.canvas.itemconfigure(cls.title, text=game)

        # 重设模式的选择
        cls.mode = ''
        # 重设模式选择框的位置
        cls.canvas.coords(cls.rectangle, -3, -3, -3, -3)

    @classmethod
    def mode_change(cls, mode: str):
        """ 模式切换 """
        # 改变当前选中的模式
        cls.mode = mode

        if mode == '网络对抗':
            # 网络模式
            cls.canvas.coords(cls.rectangle,
                              140 * cls.canvas.rate_x,
                              240 * cls.canvas.rate_y,
                              260 * cls.canvas.rate_x,
                              360 * cls.canvas.rate_y)
        elif mode == '双人对弈':
            # 双人模式
            cls.canvas.coords(cls.rectangle,
                              290 * cls.canvas.rate_x,
                              240 * cls.canvas.rate_y,
                              410 * cls.canvas.rate_x,
                              360 * cls.canvas.rate_y)
        elif mode == '人机对战':
            # 电脑模式
            cls.canvas.coords(cls.rectangle,
                              440 * cls.canvas.rate_x,
                              240 * cls.canvas.rate_y,
                              560 * cls.canvas.rate_x,
                              360 * cls.canvas.rate_y)
        elif mode == '单人模式':
            # 单人模式
            cls.canvas.coords(cls.rectangle,
                              590 * cls.canvas.rate_x,
                              240 * cls.canvas.rate_y,
                              710 * cls.canvas.rate_x,
                              360 * cls.canvas.rate_y)
        elif mode == '闯关挑战':
            # 残局模式
            cls.canvas.coords(cls.rectangle,
                              740 * cls.canvas.rate_x,
                              240 * cls.canvas.rate_y,
                              860 * cls.canvas.rate_x,
                              360 * cls.canvas.rate_y)

    @classmethod
    def online_move(cls, key: int):  # NOTE: 可能存在问题
        """ 游戏连接框的移动 """
        for widget in cls.canvas_online:
            tkintertools.move(cls.canvas, widget,
                              0, key * 500 * cls.canvas.rate_y,
                              300, 'smooth')

    @classmethod
    def start(cls):
        """ 开始游戏 """
        if not cls.mode:
            # 没选择模式就开始游戏
            tools.Tip(cls.canvas, '— 提示 —\n请选择游戏模式!', bg='#1F1F1F').fly(3)
        else:
            if cls.game == '中国象棋':
                if cls.mode == '网络对抗':
                    if Client.flag:
                        tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                                  bg='#1F1F1F').fly(3)
                    else:
                        # 没有网络，无法进行网络游戏
                        tools.Tip(cls.canvas, '— 提示 —\n正在使用局域网\n进行游戏!',
                                  bg='#1F1F1F').fly(5)
                elif cls.mode == '单人模式':
                    # 无此模式
                    tools.Tip(cls.canvas, '— 提示 —\n该游戏无此模式!',
                              bg='#1F1F1F').fly(3)
                else:
                    tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                              bg='#1F1F1F').fly(3)
            elif cls.game == '五子棋':
                if cls.mode == '网络对抗':
                    for button in [cls.mode_1, cls.mode_2, cls.mode_3, cls.mode_4, cls.begin]:
                        button.live = False
                    cls.canvas_online_flag = True
                    cls.online_move(1)
                    if not Client.flag:
                        # 没有网络，无法进行网络游戏
                        tools.Tip(cls.canvas, '— 提示 —\n正在使用局域网\n进行游戏!!',
                                  bg='#1F1F1F').fly(5)
                elif cls.mode == '单人模式':
                    # 无此模式
                    tools.Tip(cls.canvas, '— 提示 —\n该游戏无此模式!',
                              bg='#1F1F1F').fly(3)
                elif cls.mode == '闯关挑战':
                    tools.Tip(cls.canvas, '— 提示 —\n该模式仍处于开发阶段!',
                              bg='#1F1F1F').fly(3)
                else:
                    # 画布上锁，防止按钮误点
                    cls.canvas.set_lock(False)
                    # 转到五子棋游戏界面
                    Gobang(cls.mode)
                    # 隐藏画布
                    cls.canvas.place_forget()
            elif cls.game == '翻翻棋':
                if cls.mode == '网络对抗':
                    if Client.flag:
                        tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                                  bg='#1F1F1F').fly(3)
                    else:
                        # 没有网络，无法进行网络游戏
                        tools.Tip(cls.canvas, '— 提示 —\n网络未连接!',
                                  bg='#1F1F1F').fly(3)
                elif cls.mode == '单人模式':
                    # 无此模式
                    tools.Tip(cls.canvas, '— 提示 —\n该游戏无此模式!',
                              bg='#1F1F1F').fly(3)
                else:
                    tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                              bg='#1F1F1F').fly(3)
            elif cls.game == '大鱼吃小鱼':
                if cls.mode == '单人模式':
                    tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                              bg='#1F1F1F').fly(3)
                elif cls.mode == '双人对弈':
                    tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                              bg='#1F1F1F').fly(3)
                elif cls.mode == '人机对战':
                    tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                              bg='#1F1F1F').fly(3)
                else:
                    # 无此模式
                    tools.Tip(cls.canvas, '— 提示 —\n该游戏无此模式!',
                              bg='#1F1F1F').fly(3)
            elif cls.game == '贪吃蛇':
                if cls.mode in ['网络对抗', '双人对弈', '人机对战', '闯关挑战']:
                    tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!',
                              bg='#1F1F1F').fly(3)
                elif cls.mode == '单人模式':
                    cls.canvas.set_lock(False)
                    # Snake(cls.mode) NOTE: 待写
                    cls.canvas.place_forget()
            else:
                tools.Tip(cls.canvas, '— 提示 —\n模式正在开发中!', bg='#1F1F1F').fly(3)

    @classmethod
    def online(cls, button: str):
        """ 网络游戏 """
        if button == 'cancel':
            # 取消
            cls.canvas_online_flag = False
            cls.online_move(-1)
            for button in [cls.mode_1, cls.mode_2, cls.mode_3, cls.mode_4, cls.begin]:
                button.live = True
            cls.canvas_online[3].configure(text='')
        elif button == 'OK':
            if account := cls.canvas_online[3].value:
                if Client.flag:
                    if account == config['account']:
                        tools.Tip(cls.canvas, '— 提示 —\n我连我自己!?\n你搁这儿卡BUG呢?',
                                  bg='#1F1F1F').fly(5)
                    else:
                        Client.send('Game', 'Connect', 'Gobang',
                                    config['account'], account)

                        result = Client.recv()[2]
                        if result == 'Online':
                            tools.Tip(cls.canvas, '— 提示 —\n等待对方回应中',
                                      bg='#1F1F1F').fly(5)

                        elif result == 'Offline':
                            tools.Tip(cls.canvas, '— 提示 —\n对方离线中\n请稍后再试!',
                                      bg='#1F1F1F').fly(5)
                        elif result == None:
                            tools.Tip(cls.canvas, '— 提示 —\n不存在此账号\n请检查账号是否正确!',
                                      bg='#1F1F1F').fly(5)
                else:
                    try:
                        raise Exception  # NOTE: 待写
                    except:
                        tools.Tip(cls.canvas, '— 提示 —\nIP有误或无法连接\n请检查IP是否正确!',
                                  bg='#1F1F1F').fly(5)
            else:
                tools.Tip(cls.canvas, '— 提示 —\n请输入内容!', bg='#1F1F1F').fly(3)

    @classmethod
    def back(cls):
        """ 返回 """
        if cls.canvas.lock:
            # 画布上锁，防止按钮误点
            cls.canvas.set_lock(False)
            # 隐藏画布
            cls.canvas.place_forget()
            # 主界面画布解锁
            PageHome.canvas.place(x=0, y=0)
            PageHome().canvas.set_lock(True)

            if cls.canvas_online_flag:
                cls.canvas_online_flag = False
                cls.online_move(-1)
                for button in [cls.mode_1, cls.mode_2, cls.mode_3, cls.mode_4, cls.begin]:
                    button.live = True

    @classmethod
    def online_start(cls, game: str, first: bool):
        """ 网络对抗 """
        # 画布上锁，防止按钮误点
        cls.canvas.set_lock(False)
        # 隐藏画布
        cls.canvas.place_forget()
        if game == 'Gobang':
            # 转到五子棋游戏界面
            Gobang('网络对抗')
            Gobang.chat.append('[系统]\n黑方先手!\n')
            if first:
                Gobang.play = True
                tools.Tip(Gobang.canvas, '— 提示 —\n您为黑方\n您先走棋!',
                          bg='#1F1F1F').fly(5)
            else:
                tools.Tip(Gobang.canvas, '— 提示 —\n您为白方\n黑方先走棋!',
                          bg='#1F1F1F').fly(5)


class Client:
    """ 客户端类 """

    client = socket()
    client.settimeout(5)
    flag = None  # 服务器连接标识

    @classmethod
    def send(cls, **kw) -> None:
        """ 消息发送函数 """
        cls.client.send(kw.__repr__().encode('UTF-8'))

    @classmethod
    def recv(cls) -> dict:
        """ 数据接收函数 """
        msg = eval(cls.client.recv(4096).decode('UTF-8'))
        if isinstance(msg, dict):
            return msg
        return {}

    @classmethod
    def reconnect(cls):
        """ 重新连接 """
        try:
            cls.send(cmd='Quit')
        except:
            pass
        cls.client.close()
        cls.client = socket()
        cls.client.settimeout(5)
        cls.connect()

    @classmethod
    def connect(cls):
        """ 连接服务器 """
        try:
            cls.client.connect(
                (config['address'], int(config['port'])))  # 尝试连接目标地址的服务器
            cls.send(cmd='Identity')  # 身份验证
            cls.flag = True
            cls.recv()  # 身份信息获取
            cls.send(cmd='Update', version=__version__)
            msg = cls.recv()
            if msg['value'] == True:
                PageLoad.update(msg['size'])
            else:
                PageLoad.load(*next(PageLoad.loader))
        except (ConnectionError, TimeoutError, OSError):
            cls.flag = False
            tools.Popup(root, '网络异常', '无法连接至服务器！\n请检查网络！',
                        ('关闭程序', close), ('重新连接', Thread(target=cls.reconnect, daemon=True).start))

    @classmethod
    def check_delay(cls, time_out: int = 0):  # BUG
        """ 延迟检测 """
        while True:
            try:
                # 检测间隔为2秒
                time.sleep(2)
                time_send = time.time()
                cls.send(cmd='Delay')
                cls.recv()
                time_recv = time.time()
                delta = round((time_recv - time_send) * 500)
                color = 'springgreen' if delta < 100 else 'orange' if delta < 300 else 'red'
                # 更新延迟显示
                PageHome.canvas.itemconfigure(
                    PageHome.delay, text='%dms' % delta, fill=color)
                time_out, cls.flag = 0, True
            except TimeoutError:
                # 断线重连
                time_out += 1
                cls.flag = False
                if time_out == 10:
                    PageHome.canvas.itemconfigure(PageHome.delay, text='连接断开')
                    break
                PageHome.canvas.itemconfigure(
                    PageHome.delay, fill='red', text='断线重连-%d' % time_out)
            except ConnectionResetError:
                cls.flag = False
                cls.client.close()
                PageHome.canvas.itemconfigure(PageHome.delay, text='连接断开')
                cls.connect()
            except ConnectionAbortedError:
                print('ConnectionAbortedError')

    # @classmethod
    # def chat_info(cls):
    #     """ 接收聊天信息 """
    #     while True:
    #         try:
    #             time.sleep(0.01)
    #             cls.client.setblocking(False)
    #             msg = cls.recv()
    #             if msg['cmd'] == 'Chat':
    #                 Talk.message.append('[%s]\n%s\n' %
    #                                     (msg['account'], msg['message']))
    #             cls.client.setblocking(True)
    #         except BlockingIOError:
    #             cls.client.setblocking(True)


### 游戏类 ###


class Gobang:
    """ 五子棋游戏 """

    # 创建画布
    canvas = tkintertools.Canvas(root, 1000, 500, False)
    # 创建背景图片
    background = canvas.create_image(500, 250)

    # 棋盘外框
    canvas.create_rectangle(270, 20, 730, 480, width=3)
    # 聊天记录外框
    canvas.create_rectangle(750, 20, 980, 355, width=2)
    # 聊天输入框外框
    canvas.create_rectangle(750, 365, 980, 480, width=2)
    # 棋步记录外框
    canvas.create_rectangle(20, 20, 250, 395, width=2)
    # 按钮外框
    canvas.create_rectangle(20, 405, 250, 480, width=2)
    # 聊天记录标题
    canvas.create_text(865, 40, text='聊天记录', font=('华文新魏', 18))
    # 棋步记录标题
    canvas.create_text(135, 40, text='棋步记录', font=('华文新魏', 18))

    # 棋盘背景文字显示（重影）
    text_ = canvas.create_text(501, 251, font=(
        '华文行楷', 70), fill='grey', justify='center')
    # 棋盘背景文字显示
    text = canvas.create_text(500, 250, font=(
        '华文行楷', 70), fill='white', justify='center')

    # 棋盘网格横线
    for y in range(26, 475, 32):
        canvas.create_line(276, y, 724, y)
    # 棋盘网格竖线
    for x in range(276, 725, 32):
        canvas.create_line(x, 26, x, 474)

    # 棋盘的五个定位黑点
    canvas.create_oval(369, 119, 375, 125, fill='black')
    canvas.create_oval(369, 375, 375, 381, fill='black')
    canvas.create_oval(625, 119, 631, 125, fill='black')
    canvas.create_oval(625, 375, 631, 381, fill='black')
    canvas.create_oval(497, 247, 503, 253, fill='black')

    # 红色标明框（提前隐藏）
    point_red = [
        canvas.create_line(484, -86, 484, -78, fill='red', width=2),
        canvas.create_line(484, -54, 484, -62, fill='red', width=2),
        canvas.create_line(516, -86, 516, -78, fill='red', width=2),
        canvas.create_line(516, -54, 516, -62, fill='red', width=2),
        canvas.create_line(484, -86, 492, -86, fill='red', width=2),
        canvas.create_line(516, -86, 508, -86, fill='red', width=2),
        canvas.create_line(484, -54, 492, -54, fill='red', width=2),
        canvas.create_line(516, -54, 508, -54, fill='red', width=2)]

    # 绿色标明框（置于中心）
    point_green = [
        canvas.create_line(484, 234, 484, 242, fill='springgreen', width=2),
        canvas.create_line(484, 266, 484, 258, fill='springgreen', width=2),
        canvas.create_line(516, 234, 516, 242, fill='springgreen', width=2),
        canvas.create_line(516, 266, 516, 258, fill='springgreen', width=2),
        canvas.create_line(484, 234, 492, 234, fill='springgreen', width=2),
        canvas.create_line(516, 234, 508, 234, fill='springgreen', width=2),
        canvas.create_line(484, 266, 492, 266, fill='springgreen', width=2),
        canvas.create_line(516, 266, 508, 266, fill='springgreen', width=2)]

    # 棋步记录文本框
    record = tkintertools.CanvasText(canvas, 25, 60, 220, 330, 5, read=True,
                                     color_text=('black', 'black', 'black'),
                                     color_fill=tkintertools.COLOR_NONE,
                                     color_outline=('black', 'springgreen', 'springgreen'))
    # 聊天记录文本框
    chat = tkintertools.CanvasText(canvas, 755, 60, 220, 290, 5, read=True,
                                   color_text=('black', 'black', 'black'),
                                   color_fill=tkintertools.COLOR_NONE,
                                   color_outline=('black', 'springgreen', 'springgreen'))
    # 聊天输入文本框
    entry = tkintertools.CanvasText(canvas, 755, 370, 220, 70, 5, limit=30,
                                    color_text=('black', 'black', 'black'),
                                    color_fill=tkintertools.COLOR_NONE,
                                    color_outline=('black', 'springgreen', 'springgreen'))

    # 退出按钮
    tkintertools.CanvasButton(canvas, 25, 445, 107.5, 30, 5, '退 出',
                              command=lambda: Gobang.back(),
                              color_text=('black', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('black', 'springgreen', 'springgreen'))
    # 提示按钮
    tkintertools.CanvasButton(canvas, 137.5, 445, 107.5, 30, 5, '提 示',
                              command=lambda: Gobang.hint(),
                              color_text=('black', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('black', 'springgreen', 'springgreen'))
    # 重新开始按钮
    tkintertools.CanvasButton(canvas, 25, 410, 107.5, 30, 5, '重新开始',
                              command=lambda: Gobang.again(),
                              color_text=('black', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('black', 'springgreen', 'springgreen'))
    # 悔棋按钮
    tkintertools.CanvasButton(canvas, 137.5, 410, 107.5, 30, 5, '悔 棋',
                              command=lambda: Gobang.regret(),
                              color_text=('black', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('black', 'springgreen', 'springgreen'))
    # 发送消息按钮
    tkintertools.CanvasButton(canvas, 755, 445, 220, 30, 5, '发送消息',
                              command=lambda: Gobang.send(),
                              color_text=('black', 'springgreen',
                                          'springgreen'),
                              color_fill=('', '', 'grey'),
                              color_outline=('black', 'springgreen', 'springgreen'))

    # 电脑系数设定框
    canvas_computer: list[tkintertools.CanvasLabel | tkintertools.CanvasButton] = [
        tkintertools.CanvasLabel(
            canvas, 260, -370, 480, 240, 5, '— 电脑系数设定 —' + '\n' * 5, font=('楷体', 25),
            color_text=('grey', 'white', 'white'),
            color_fill=('#1F1F1F', '#1F1F1F', '#1F1F1F'),
            color_outline=('grey', 'white', 'white')),
        # 攻击系数显示框
        tkintertools.CanvasLabel(
            canvas, 400, -280, 200, 30, 5, text='电脑攻击系数:2',
            color_text=('grey', 'white', 'white'),
            color_fill=tkintertools.COLOR_NONE,
            color_outline=('grey', 'white', 'white')),
        # 防御系数显示框
        tkintertools.CanvasLabel(
            canvas, 400, -230, 200, 30, 5, text='电脑防御系数:2',
            color_text=('grey', 'white', 'white'),
            color_fill=tkintertools.COLOR_NONE,
            color_outline=('grey', 'white', 'white')),
        # 攻击系数加大按钮
        tkintertools.CanvasButton(
            canvas, 280, -280, 100, 30, 5, '加 大',
            command=lambda: Gobang.computer_set('plus_attack'),
            color_text=('grey', 'orange', 'orange'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'orange', 'orange')),
        # 防御系数加大按钮
        tkintertools.CanvasButton(
            canvas, 280, -230, 100, 30, 5, '加 大',
            command=lambda: Gobang.computer_set('plus_defense'),
            color_text=('grey', 'orange', 'orange'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'orange', 'orange')),
        # 攻击系数减小按钮
        tkintertools.CanvasButton(
            canvas, 620, -280, 100, 30, 5, '减 小',
            command=lambda: Gobang.computer_set('minus_attack'),
            color_text=('grey', 'cyan', 'cyan'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'cyan', 'cyan')),
        # 防御系数减小按钮
        tkintertools.CanvasButton(
            canvas, 620, -230, 100, 30, 5, '减 小',
            command=lambda: Gobang.computer_set('minus_defense'),
            color_text=('grey', 'cyan', 'cyan'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'cyan', 'cyan')),
        # 电脑设定确定按钮
        tkintertools.CanvasButton(
            canvas, 370, -180, 120, 30, 5, '确 定',
            command=lambda: Gobang.computer_set('OK'),
            color_text=('grey', 'springgreen', 'springgreen'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'springgreen', 'springgreen')),
        # 动态随机设定按钮
        tkintertools.CanvasButton(
            canvas, 510, -180, 120, 30, 5, '动态随机',
            command=lambda: Gobang.computer_set('random'),
            color_text=('grey', 'yellow', 'yellow'),
            color_fill=('', '', 'grey'),
            color_outline=('grey', 'yellow', 'yellow'))]

    # 鼠标位于棋盘网格坐标
    x, y = 7, 7
    # 红标的初始网格坐标
    red_x, red_y = 7, -3
    # 游戏模式
    mode = ''
    # 步数
    step = 0
    # 默认玩家（黑方）
    player = 'black'
    # 玩家是否可以落子（走棋锁）
    play = False
    # 游戏结束标识
    over = False

    # 棋盘数据
    gobang = [[0] * 15 for _ in range(15)]
    # 棋盘图片数据
    image = [[0] * 15 for _ in range(15)]

    # 电脑攻击系数
    attack = 2
    # 电脑防御系数
    defense = 2
    # 设定界面是否拉下
    computer_set_flag = False

    def __init__(self, mode: str):
        # 放置画布
        self.canvas.place(x=0, y=0)
        # 解开画布锁
        self.canvas.set_lock(True)
        # 模式更新
        Gobang.mode = mode
        # 棋盘背景文本显示（重影）
        self.canvas.itemconfigure(self.text_, text='五子棋\n' + mode)
        # 棋盘背景文本显示
        self.canvas.itemconfigure(self.text, text='五子棋\n' + mode)
        # 背景图片更新
        self.canvas.itemconfigure(
            self.background, image=res['gobang']['background'])
        # 刷新
        self.again()
        # 绿标显示绑定
        root.bind('<Motion>', self.mouse_green)
        # 走棋绑定
        root.bind('<Button-1>', self.game)

    @classmethod
    def computer_move(cls, key: int):
        """ 人机设定框的移动 """
        for widget in cls.canvas_computer:
            tkintertools.move(cls.canvas, widget,
                              0, key * 500 * cls.canvas.rate_y,
                              300, 'smooth')

    @classmethod
    def mouse_green(cls, event: Event):
        """ 绿标指示 """
        x = round((event.x - 276 * cls.canvas.rate_x) /
                  (32 * cls.canvas.rate_x))
        y = round((event.y - 26 * cls.canvas.rate_y) /
                  (32 * cls.canvas.rate_y))
        if 0 <= x <= 14 and 0 <= y <= 14:
            # 更新绿标位置
            for p in cls.point_green:
                cls.canvas.move(p, (x - cls.x) * 32 * cls.canvas.rate_x,
                                (y - cls.y) * 32 * cls.canvas.rate_y)
            # 更新绿标位置记录数据
            cls.x, cls.y = x, y

    @classmethod
    def mouse_red(cls, x: int, y: int):
        """ 红标指示 """
        # 更新红标位置
        for p in cls.point_red:
            cls.canvas.move(p, (x - cls.red_x) * 32 * cls.canvas.rate_x,
                            (y - cls.red_y) * 32 * cls.canvas.rate_y)
        # 更新红标位置记录数据
        cls.red_x, cls.red_y = x, y

    @classmethod
    def judge(cls, last_x: int, last_y: int):
        """ 判断输赢 """
        # 横向棋盘数据
        key_1 = ''.join([str(cls.gobang[last_y][x])
                        for x in range(last_x - 4, last_x + 5) if 0 <= x <= 14])
        # 列向棋盘数据
        key_2 = ''.join([str(cls.gobang[y][last_x])
                        for y in range(last_y - 4, last_y + 5) if 0 <= y <= 14])
        # 右斜棋盘数据
        key_3 = ''.join(
            [str(cls.gobang[y][x]) for x, y in zip(range(last_x - 4, last_x + 5), range(last_y - 4, last_y + 5)) if
             0 <= x <= 14 and 0 <= y <= 14])
        # 左斜棋盘数据
        key_4 = ''.join(
            [str(cls.gobang[y][x]) for x, y in zip(range(last_x - 4, last_x + 5), range(last_y + 4, last_y - 5, -1)) if
             0 <= x <= 14 and 0 <= y <= 14])

        if '11111' in key_1 or '11111' in key_2 or '11111' in key_3 or '11111' in key_4:
            # 白方胜
            cls.over = True
            return 'white'
        elif '22222' in key_1 or '22222' in key_2 or '22222' in key_3 or '22222' in key_4:
            # 黑方胜
            cls.over = True
            return 'black'

    @classmethod
    def game(cls, event: Event):
        """ 游戏操作 """
        if 260 <= round(event.x / cls.canvas.rate_x) <= 740 and 10 <= round(
                event.y / cls.canvas.rate_y) <= 490 and cls.play:
            # 点击位置为空
            if not cls.gobang[cls.y][cls.x]:
                # 步数更新
                cls.step += 1
                # 判断下棋方
                text = '[玩家]' if cls.mode == '人机对战' else '[黑方]' if cls.player == 'black' else '[白方]'
                # 下棋记录
                cls.record.append(
                    text + '(%02d,%02d) \t[%03d]\n' % (cls.x, cls.y, cls.step))
                # 更新棋盘数据
                cls.gobang[cls.y][cls.x] = 1 if cls.player == 'white' else 2
                # 更新棋盘图片数据并显示棋子
                cls.image[cls.y][cls.x] = cls.canvas.create_image((cls.x * 32 + 276) * cls.canvas.rate_x,
                                                                  (cls.y * 32 + 26) *
                                                                  cls.canvas.rate_y,
                                                                  image=res['gobang'][cls.player])
                # 更新当前下棋方
                cls.player = 'black' if cls.player == 'white' else 'white'
                # 随机选取并播放下棋音效
                PlaySound(path['gobang']['voice_%d' % randint(1, 4)], 1)

                if cls.mode != '人机对战':
                    # 更新红标位置
                    cls.mouse_red(cls.x, cls.y)
                    if cls.mode == '网络对抗':
                        cls.play = False
                        Client.send('Game', 'Play', '(%s, %s)' %
                                    (cls.x, cls.y), config['account'])

                if result := cls.judge(cls.x, cls.y):
                    # 锁定走棋锁，不让玩家走棋
                    cls.play = False
                    # 系统宣布游戏结果
                    cls.chat.append('[系统]\n%s方胜利！\n' %
                                    ('黑' if result == 'black' else '白'))
                    tools.Tip(cls.canvas, '— 提示 —\n%s方胜利!' %
                              ('黑' if result == 'black' else '白'), bg='#1F1F1F').fly(3)
                    # 游戏终止，防止电脑思考
                    return
                elif cls.step == 255:
                    # 锁定走棋锁，不让玩家走棋
                    cls.play = False
                    # 系统宣布平局
                    cls.chat.append('[系统]\n平局!\n')
                    tools.Tip(cls.canvas, '— 提示 —\n平局!', bg='#1F1F1F').fly(3)
                    # 游戏终止，防止电脑思考
                    return

                if cls.mode == '人机对战':
                    # 锁定走棋锁，让计算机思考
                    cls.play = False
                    # “电脑”发送消息“正在思考”消息
                    if randint(0, 1):
                        cls.chat.append('[电脑]\n我正在思考中...\n')
                    else:
                        cls.chat.append('[电脑]\n容我想想...\n')
                    # 开启子线程计算结果
                    Thread(target=cls.computer, daemon=True).start()

    @classmethod
    def online(cls, data: str):
        """ 网络对抗 """
        x, y = eval(data)

        cls.step += 1
        text = '[玩家]' if cls.mode == '人机对战' else '[黑方]' if cls.player == 'black' else '[白方]'
        cls.record.append(text + '(%02d,%02d) \t[%03d]\n' % (x, y, cls.step))
        cls.gobang[y][x] = 1 if cls.player == 'white' else 2
        cls.image[y][x] = cls.canvas.create_image((x * 32 + 276) * cls.canvas.rate_x,
                                                  (y * 32 + 26) *
                                                  cls.canvas.rate_y,
                                                  image=res['gobang'][cls.player])
        cls.player = 'black' if cls.player == 'white' else 'white'
        PlaySound(path['gobang']['voice_%d' % randint(1, 4)], 1)
        cls.mouse_red(x, y)
        cls.play = True

        if result := cls.judge(x, y):
            # 锁定走棋锁，不让玩家走棋
            cls.play = False
            # 系统宣布游戏结果
            cls.chat.append('[系统]\n%s方胜利！\n' %
                            ('黑' if result == 'black' else '白'))
            tools.Tip(cls.canvas, '— 提示 —\n%s方胜利!' %
                      ('黑' if result == 'black' else '白'), bg='#1F1F1F').fly(3)
        elif cls.step == 255:
            # 锁定走棋锁，不让玩家走棋
            cls.play = False
            # 系统宣布平局
            cls.chat.append('[系统]\n平局!\n')
            tools.Tip(cls.canvas, '— 提示 —\n平局!', bg='#1F1F1F').fly(3)

    @classmethod
    def computer(cls):
        """ 人机 """
        if cls.attack == 0 and cls.defense == 0:
            # 动态随机系数设定
            x, y = cls.artificial_intelligence(randint(1, 4), randint(1, 4))
        else:
            # 一般系数设定
            x, y = cls.artificial_intelligence(cls.attack, cls.defense)

        # 步数更新
        cls.step += 1
        # 棋步记录
        cls.record.append('[电脑]' + '(%02d,%02d) \t[%03d]\n' % (x, y, cls.step))
        # 棋盘数据更新
        cls.gobang[y][x] = 1
        # 棋盘图片数据更新并显示棋子
        cls.image[y][x] = cls.canvas.create_image((x * 32 + 276) * cls.canvas.rate_x,
                                                  (y * 32 + 26) *
                                                  cls.canvas.rate_y,
                                                  image=res['gobang'][cls.player])
        # 当前走棋方更新为玩家（默认为黑方）
        cls.player = 'black'
        # 红标显示
        cls.mouse_red(x, y)
        # 解开走棋锁
        cls.play = True
        # 随机选取并播放走棋音效
        PlaySound(path['gobang']['voice_%d' % randint(1, 4)], 1)

        # 计算输赢结果
        if result := cls.judge(x, y):
            # 锁定走棋锁，不让玩家走棋
            cls.play = False
            # 系统宣布游戏结果
            cls.chat.append('[系统]\n%s胜利！\n' %
                            ('玩家' if result == 'black' else '电脑'))
            tools.Tip(cls.canvas, '— 提示 —\n%s胜利' %
                      ('玩家' if result == 'black' else '电脑'), bg='#1F1F1F').fly(3)
        elif cls.step == 255:
            # 锁定走棋锁，不让玩家走棋
            cls.play = False
            # 系统宣布平局
            cls.chat.append('[系统]\n平局!\n')
            tools.Tip(cls.canvas, '— 提示 —\n平局!', bg='#1F1F1F').fly(3)

    @classmethod
    def computer_set(cls, button: str):
        """ 人机难度选择 """
        if button == 'plus_attack':
            # 电脑攻击系数加大
            if cls.attack < 4:
                cls.attack += 1
                cls.canvas_computer[1].configure(text='电脑攻击系数:%d' % cls.attack)
        elif button == 'minus_attack':
            # 电脑攻击系数减小
            if cls.attack > 1:
                cls.attack -= 1
                cls.canvas_computer[1].configure(text='电脑攻击系数:%d' % cls.attack)
        elif button == 'plus_defense':
            # 电脑防御系数加大
            if cls.defense < 4:
                cls.defense += 1
                cls.canvas_computer[2].configure(
                    text='电脑防御系数:%d' % cls.defense)
        elif button == 'minus_defense':
            # 电脑防御系数减小
            if cls.defense > 1:
                cls.defense -= 1
                cls.canvas_computer[2].configure(
                    text='电脑防御系数:%d' % cls.defense)
        else:
            # 设定框下拉标识设为False
            cls.computer_set_flag = False
            # 收起系数设定下拉框
            cls.computer_move(-1)
            # 系统宣布玩家先手
            cls.chat.append('[系统]\n玩家先手！\n')
            # 打开走棋锁，允许玩家走棋
            cls.play = True
            # 使系数设定框按钮失效，防按钮误点
            for ind, widget in enumerate(cls.canvas_computer):
                if ind >= 3:
                    widget.live = False
            # 动态随机系数
            if button == 'random':
                # 设为0以作标识
                cls.attack = 0
                cls.defense = 0
                # 更新系数显示
                cls.canvas_computer[1].configure(text='电脑攻击系数:随机')
                cls.canvas_computer[2].configure(text='电脑防御系数:随机')

    @classmethod
    def regret(cls):
        """ 悔棋 """
        if cls.canvas.lock:
            if cls.record.value and cls.play and cls.mode != '网络对抗':
                # 有记录且玩家可走棋时才可悔棋（网络对抗不许悔棋）

                if cls.mode == '双人对弈':
                    # 寻找上一步下棋位置
                    x, y = map(int, cls.record.value[-14:-9].split(','))
                    # 清空该位置的棋盘数据
                    cls.gobang[y][x] = 0
                    # 删除该位置的图片
                    cls.canvas.delete(cls.image[y][x])
                    # 删除棋步记录上的最后的下棋记录
                    cls.record.set(cls.record.value[:-19])
                    # 更新当前玩家方
                    cls.player = 'black' if cls.player == 'white' else 'white'
                    # 系统发出悔棋方消息
                    cls.chat.append('[系统]\n%s方悔棋！\n' %
                                    ('黑' if cls.player == 'black' else '白'))
                    # 步数更新
                    cls.step -= 1

                elif cls.mode == '人机对战' or cls.mode == '闯关挑战':
                    # 寻找上一步下棋位置
                    x, y = map(int, cls.record.value[-14:-9].split(','))
                    # 清空该位置的棋盘数据
                    cls.gobang[y][x] = 0
                    # 删除该位置的图片
                    cls.canvas.delete(cls.image[y][x])
                    # 删除棋步记录上的最后的下棋记录
                    cls.record.set(cls.record.value[:-19])

                    # 重复上述步骤
                    x, y = map(int, cls.record.value[-14:-9].split(','))
                    cls.gobang[y][x] = 0
                    cls.canvas.delete(cls.image[y][x])
                    cls.record.set(cls.record.value[:-19])

                    # 系统发出玩家悔棋消息
                    cls.chat.append('[系统]\n玩家悔棋！\n')
                    # 步数更新
                    cls.step -= 2

                if cls.record.value:
                    # 若悔棋后还有记录，则计算该下棋位置
                    x, y = map(int, cls.record.value[-14:-9].split(','))
                    # 将该位置打上红标
                    cls.mouse_red(x, y)
                else:
                    # 记录被清空，没有棋子存在了，红标恢复默认位置
                    cls.mouse_red(7, -3)

            else:
                tools.Tip(cls.canvas, '— 提示 —\n当前不可悔棋!', bg='#1F1F1F').fly(3)

    @classmethod
    def again(cls):
        """ 重新开始 """
        if cls.canvas.lock:

            if cls.mode == '网络对抗':
                if cls.over:
                    Client.send('Game', 'Again', 'Gobang', config['account'])

                    cls.chat.append('[系统]\n游戏重新开始！\n')
                    cls.chat.append('[系统]\n%s方先手！\n' %
                                    '黑' if cls.player == 'black' else '白')
                    cls.play = True
                    tools.Tip(cls.canvas, '— 提示 —\n游戏重新开始!\n您为%s方!' % '黑' if cls.player == 'black' else '白',
                              bg='#1F1F1F').fly(5)

                    # 初始化棋盘数据
                    cls.gobang = [[0] * 15 for _ in range(15)]
                    # 删除所有的棋盘图片数据
                    for line in cls.image:
                        for img in line:
                            cls.canvas.delete(img)

                    # 清空棋步记录
                    cls.record.set('')
                    # 红标恢复默认位置
                    cls.mouse_red(7, -3)
                    # 步数归零
                    cls.step = 0

                else:
                    tools.Tip(cls.canvas, '— 提示 —\n当前游戏还未结束!\n无法重新开始!',
                              bg='#1F1F1F').fly(5)

            if cls.mode == '双人对弈':

                # 初始化棋盘数据
                cls.gobang = [[0] * 15 for _ in range(15)]
                # 删除所有的棋盘图片数据
                for line in cls.image:
                    for img in line:
                        cls.canvas.delete(img)

                # 清空棋步记录
                cls.record.set('')
                # 清空聊天记录
                cls.chat.set('')
                # 红标恢复默认位置
                cls.mouse_red(7, -3)
                # 步数归零
                cls.step = 0

                # 系统宣布先手方
                cls.chat.append('[系统]\n%s方先手！\n' % '黑')
                # 打开走棋锁，允许玩家走棋
                cls.play = True
                # 设定当前走棋方为黑方
                cls.player = 'black'
            elif cls.mode == '人机对战':

                # 初始化棋盘数据
                cls.gobang = [[0] * 15 for _ in range(15)]
                # 删除所有的棋盘图片数据
                for line in cls.image:
                    for img in line:
                        cls.canvas.delete(img)

                # 清空棋步记录
                cls.record.set('')
                # 清空聊天记录
                cls.chat.set('')
                # 红标恢复默认位置
                cls.mouse_red(7, -3)
                # 步数归零
                cls.step = 0

                # 设定当前走棋方为黑方（玩家默认为黑方）
                cls.player = 'black'
                if not cls.computer_set_flag:
                    # 设定框下拉标识设为True
                    cls.computer_set_flag = True
                    # 锁定玩家锁，在确定系数前不允许玩家走棋
                    cls.play = False
                    # 激活电脑系数设定框按钮
                    for ind, widget in enumerate(cls.canvas_computer):
                        if ind >= 3:
                            widget.live = True
                    # 下拉电脑系数设定框
                    cls.computer_move(1)

            cls.over = False

    @classmethod
    def hint(cls):
        """ 提示 """
        if cls.canvas.lock:
            if cls.mode == '网络对抗':
                tools.Tip(cls.canvas, '— 提示 —\n当前模式下\n提示功能仍在开发!',
                          bg='#1F1F1F').fly(3)
            elif cls.mode == '闯关模式':
                tools.Tip(cls.canvas, '— 提示 —\n当前模式下\n提示功能仍在开发!',
                          bg='#1F1F1F').fly(3)
            else:
                tools.Tip(cls.canvas, '— 提示 —\n当前模式下\n提示功能已禁用!',
                          bg='#1F1F1F').fly(5)

    @classmethod
    def send(cls):
        """ 发送消息 """
        if cls.canvas.lock:
            if cls.mode == '网络对抗':
                if cls.entry.value:
                    Client.send('Game', 'Chat', cls.entry.value,
                                config['account'])
                    cls.entry.set('')
                else:
                    tools.Tip(cls.canvas, '— 提示 —\n请输入消息内容!',
                              bg='#1F1F1F').fly(3)
            else:
                tools.Tip(cls.canvas, '— 提示 —\n当前模式下\n聊天功能已禁用!',
                          bg='#1F1F1F').fly(5)

    @classmethod
    def back(cls):
        """ 返回 """
        if cls.canvas.lock:
            # 取消鼠标移动的绑定
            root.unbind('<Motion>')
            # 取消鼠标左键按下的绑定
            root.unbind('<Button-1>')
            # 显示游戏房间画布
            Room.canvas.place(x=0, y=0)
            # 五子棋画布上锁，防误点
            cls.canvas.set_lock(False)
            # 打开游戏房间锁
            Room.canvas.set_lock(True)
            # 隐藏五子棋画布
            cls.canvas.place_forget()

            # 清空棋盘数据
            cls.gobang = [[0] * 15 for _ in range(15)]
            # 删除所有的棋盘图片数据
            for line in cls.image:
                for img in line:
                    cls.canvas.delete(img)

            # 清空棋步记录
            cls.record.set('')
            # 清空聊天记录
            cls.chat.set('')
            # 红标恢复默认位置
            cls.mouse_red(7, -3)
            # 步数归零
            cls.step = 0

            if cls.mode == '网络对抗':
                # 发送离开房间信息
                Client.send('Game', 'Quit', 'Gobang', config['account'])

            elif cls.mode == '人机对战' and cls.computer_set_flag:
                # 设定系数下拉框标识为False
                cls.computer_set_flag = False
                # 收起系数设定下拉框
                cls.computer_move(-1)

    @classmethod
    def analysis(cls):
        """ 收集AI分析数据 """

        process = []

        for i in range(15):
            process.append([line[i] for line in cls.gobang])

        for lis in cls.gobang:
            process.append(lis)

        for i in [1, -1]:  # 右斜;左斜
            for x in range(15):
                y = 0
                temp_list1 = []
                temp_list2 = []
                try:
                    while x >= 0:
                        temp_list1.append(cls.gobang[x][y])
                        temp_list2.append(
                            cls.gobang[i * (y - 7) + 7][i * (x - 7) + 7])
                        x += i
                        y += 1
                except IndexError:
                    pass

                if len(temp_list1) > 4:
                    process.append(temp_list1)
                if len(temp_list2) > 4:
                    process.append(temp_list2)

        return process

    @classmethod
    def scissors(cls, x: int, y: int):
        """ 剪枝 """
        key_1 = [cls.gobang[y][x] for x in range(x - 2, x + 3) if 0 <= x <= 14]
        key_2 = [cls.gobang[y][x] for y in range(y - 2, y + 3) if 0 <= y <= 14]
        key_3 = [cls.gobang[y][x] for x, y in zip(range(x - 2, x + 3), range(y - 2, y + 3)) if
                 0 <= x <= 14 and 0 <= y <= 14]
        key_4 = [cls.gobang[y][x] for x, y in zip(range(x - 2, x + 3), range(y + 2, y - 3, -1)) if
                 0 <= x <= 14 and 0 <= y <= 14]

        return sum(key_1) + sum(key_2) + sum(key_3) + sum(key_4)

    @staticmethod
    def power(base, exponent):
        """ 快速幂 """
        res = 1
        while exponent:
            if exponent & 1:
                res *= base
            base *= base
            exponent = exponent >> 1
        return res

    @classmethod
    def artificial_intelligence(cls, attack: int, defense: int):
        """ AI算法 """
        result = []

        for x in range(15):
            for y in range(15):
                if not cls.gobang[y][x] and cls.scissors(x, y):
                    cls.gobang[y][x] = 1
                    score = 0

                    for line in cls.analysis():

                        for i in range(len(line) - 4):
                            key = line[i: i + 5]

                            if 2 not in key:
                                if key == [1, 1, 1, 1, 1]:
                                    return x, y
                                else:
                                    try:
                                        score += cls.power(
                                            constants.ATT_CASE.index(key), attack)
                                    except ValueError:
                                        score += cls.power(
                                            constants.ATT_CASE.index(key[::-1]), attack)

                            if 1 not in key:
                                try:
                                    ind = constants.DEF_CASE.index(key)
                                    if ind >= 17:
                                        score -= 100000000
                                    else:
                                        score -= cls.power(ind, defense)
                                except ValueError:
                                    ind = constants.DEF_CASE.index(key[::-1])
                                    if ind >= 17:
                                        score -= 100000000
                                    else:
                                        score -= cls.power(ind, defense)

                        for i in range(len(line) - 5):
                            key = line[i: i + 6]

                            if 2 not in key:
                                try:
                                    ind = constants.ATT_CASE_2.index(key)
                                    if ind >= 33:
                                        return x, y
                                    else:
                                        score += cls.power(ind, attack)
                                except ValueError:
                                    ind = constants.ATT_CASE_2.index(
                                        key[::-1])
                                    if ind >= 33:
                                        return x, y
                                    else:
                                        score += cls.power(ind, attack)

                            if 1 not in key:
                                try:
                                    ind = constants.DEF_CASE_2.index(key)
                                    if ind >= 25:
                                        score -= 100000000
                                    else:
                                        score -= cls.power(
                                            constants.DEF_CASE_2.index(key), defense)
                                except ValueError:
                                    ind = constants.DEF_CASE_2.index(
                                        key[::-1])
                                    if ind >= 25:
                                        score -= 100000000
                                    else:
                                        score -= cls.power(
                                            constants.DEF_CASE_2.index(key[::-1]), defense)

                    cls.gobang[y][x] = 0

                    result.append(((x, y), score))

        result.sort(key=lambda elem: elem[1], reverse=True)

        return result[0][0]


def close():
    """ 关闭程序 """
    if Client.flag:
        Client.send(cmd='Quit')
    Client.client.close()
    root.quit()


def main():
    """ 启动程序 """
    PageLoad()
    root.mainloop()


if __name__ == '__main__':
    main()
