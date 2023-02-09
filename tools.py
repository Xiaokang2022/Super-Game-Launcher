"""
辅助模块
"""


import tkintertools


class Tip:
    """ 提示框类 """

    def __init__(self,
                 canvas: tkintertools.Canvas,
                 text: str,
                 button: tuple[str, str] | None = None,
                 bg: str = ''):
        # 父画布控件
        self.canvas = canvas
        # 提示框模式
        self.button = button
        # 摧毁判断
        self._destroy = False
        # 当前窗口大小
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        # 提示框文本显示
        self.text = tkintertools.CanvasLabel(canvas,
                                             width - canvas.rate_x * 240,
                                             height + canvas.rate_y * 10,
                                             canvas.rate_x * 230,
                                             canvas.rate_y * 90,
                                             5, text, font=(
                                                 '楷体', int(15 * canvas.rate_x)),
                                             color_text=(
                                                 'grey', 'white', 'white'),
                                             color_fill=(bg, bg, 'grey'),
                                             color_outline=('grey', 'white', 'white'))
        if button:
            # 添加一个靠左下的按钮
            self.left = tkintertools.CanvasButton(canvas,
                                                  width - canvas.rate_x * 230,
                                                  height + canvas.rate_y * 60,
                                                  canvas.rate_x * 100,
                                                  canvas.rate_y * 30,
                                                  5,
                                                  button[0],
                                                  color_text=(
                                                      'grey', 'red', 'red'),
                                                  color_fill=('', '', 'grey'),
                                                  color_outline=('grey', 'red', 'red'))
            # 添加一个靠右下的按钮
            self.right = tkintertools.CanvasButton(canvas,
                                                   width - canvas.rate_x * 120,
                                                   height + canvas.rate_y * 60,
                                                   canvas.rate_x * 100,
                                                   canvas.rate_y * 30,
                                                   5,
                                                   button[1],
                                                   color_text=(
                                                       'grey', 'cyan', 'cyan'),
                                                   color_fill=(
                                                       '', '', 'grey'),
                                                   color_outline=('grey', 'cyan', 'cyan'))

    def fly(self, existence: int, first: bool = True, dy: int = -110):
        """ 提示框浮动弹出方法 """
        if first:
            # 启动自毁倒计时函数
            self.self_destruction(existence * 1000)

        tkintertools.move(
            self.canvas, self.text, 0, dy * self.canvas.rate_y, 300, 'rebound', 60)
        if self.button:
            tkintertools.move(
                self.canvas, self.left, 0, dy * self.canvas.rate_y, 300, 'rebound', 60)
            tkintertools.move(
                self.canvas, self.right, 0, dy * self.canvas.rate_y, 300, 'rebound', 60)

    def self_destruction(self, existence: int):
        """ 自毁设定方法 """
        # 提示框最后1秒内浮动收回
        self.canvas.after(existence - 1000, self.fly, existence, False, 110)
        # 提示框自毁
        self.canvas.after(existence, self.destroy)

    def destroy(self):
        """ 摧毁控件方法 """
        if not self._destroy:
            self._destroy = True
            self.text.destroy()
            if self.button:
                self.left.destroy()
                self.right.destroy()


class GameCard:
    """ 游戏卡类 """

    def __init__(self,
                 canvas: tkintertools.Canvas,
                 title: str,
                 color: str,
                 text: str,
                 x1: int,
                 y1: int,
                 x2: int,
                 y2: int):
        self.canvas = canvas
        self.title = canvas.create_text((x1 + x2) / 2, y1 + 30,
                                        text=title,
                                        fill=color,
                                        font=('华文新魏', 25),
                                        tags='25')
        self.text = tkintertools.CanvasLabel(canvas, x1, y1, x2 - x1, y2 - y1, 5, text,
                                             color_text=(
                                                 'grey', 'white', 'white'),
                                             color_fill=('', '', ''),
                                             color_outline=('grey', 'white', 'white'))
        self.rectangle = tkintertools.CanvasLabel(canvas,
                                                  x1 + 10, y2 - 160,
                                                  x2 - x1 - 20, 110,
                                                  5,
                                                  color_text=(
                                                      'grey', 'white', 'white'),
                                                  color_fill=('', '', ''),
                                                  color_outline=('grey', 'white', 'white'))
        # 显示图片
        self.image = canvas.create_image((x1 + x2) / 2, (y1 + y2) / 2 + 45)
        # 添加一个靠底居中的按钮
        self.start = tkintertools.CanvasButton(canvas, (x1 + x2) / 2 - 50, y2 - 40,
                                               100, 30, 5, '启动游戏',
                                               color_text=(
                                                   'grey', 'springgreen', 'springgreen'),
                                               color_fill=(
                                                   '', '', 'grey'),
                                               color_outline=('grey', 'springgreen', 'springgreen'))

    def move(self, dx: float):
        """ 改变横坐标方法 """
        self.text.move(dx, 0)
        self.rectangle.move(dx, 0)
        self.start.move(dx, 0)
        self.canvas.move(self.title, dx, 0)
        self.canvas.move(self.image, dx, 0)


class Popup:
    """ 虚拟弹窗 """

    def __init__(self, root: tkintertools.Tk, title: str, text: str, left, right):
        self.canvas = tkintertools.Canvas(root, 300, 200, bg='#1F1F1F')
        self.canvas.create_rectangle(0, 0, 300, 30, fill='black')
        self.canvas.create_rectangle(0, 150, 300, 200, fill='black')
        self.canvas.create_text(
            10, 15, text=title, fill='white', anchor='w', font=('楷体', 12))
        self.canvas.create_text(
            150, 90, text=text, fill='white', font=('楷体', 15), justify='center')

        if left[1]:
            tkintertools.CanvasButton(
                self.canvas, 10, 160, 135, 30, 0, left[0],
                command=lambda: (left[1](), self.canvas.destroy()),
                color_fill=('#1F1F1F', 'grey', '#111111'),
                color_text=('white', 'white', 'white'),
                color_outline=('grey', 'white', 'white'))
        if right[1]:
            tkintertools.CanvasButton(
                self.canvas, 155, 160, 135, 30, 0, right[0],
                command=lambda: (right[1](), self.canvas.destroy()),
                color_fill=('#1F1F1F', 'grey', '#111111'),
                color_text=('white', 'white', 'white'),
                color_outline=('springgreen', 'white', 'white'))
        self.canvas.place(x=350, y=150)
        self.canvas.bell()
        self.canvas.zoom()
