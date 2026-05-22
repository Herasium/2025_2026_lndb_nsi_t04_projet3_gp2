from modules.client.toolbox.entity import Entity
from modules.client.toolbox.text import Text
from typing import List
from modules.data import texture, data
from modules.client.mouse import mouse
from line_profiler import profile
import math
import arcade


class NewserverMenu(arcade.View):

    def __init__(self, game_menu):
        super().__init__()
        self.background_color: arcade.color = arcade.color.BLACK
        self.game_menu = game_menu

        BOX_W, BOX_H = 1000, 600
        BOX_X = (1920 - BOX_W) // 2
        BOX_Y = (1080 - BOX_H) // 2

        INPUT_W, INPUT_H = 400, 100
        PADDING = (BOX_W - INPUT_W * 2) // 3

        NAME_X = BOX_X + PADDING
        IP_X   = BOX_X + PADDING * 2 + INPUT_W
        INPUT_Y = BOX_Y + (BOX_H - INPUT_H) // 2

        JOIN_X = (1920 - INPUT_W) // 2
        JOIN_Y = BOX_Y - 20 - INPUT_H

        self.box         = Entity(BOX_X,  BOX_Y,  BOX_W,   BOX_H,   texture.get("box"))
        self.input_name  = Entity(NAME_X, INPUT_Y, INPUT_W, INPUT_H, texture.get("name"))
        self.input_ip    = Entity(IP_X,   INPUT_Y, INPUT_W, INPUT_H, texture.get("ip"))
        self.button_join = Entity(JOIN_X, JOIN_Y,  INPUT_W, INPUT_H, texture.get("add_default"))
        self.button_quit = Entity(1820, 990, 64, 64, texture.get("quit_default"))

        self.name = ""
        self.ip   = ""
        self.is_typing_name = False
        self.is_typing_ip   = False
        self.done_name = True
        self.done_ip   = True

        self.name_text = arcade.Text(
            text="",
            x=NAME_X + 25,
            y=INPUT_Y + 35,
            color=arcade.color.WHITE,
            font_size=18,
            font_name="Press Start 2P"
        )
        self.ip_text = arcade.Text(
            text="",
            x=IP_X + 25,
            y=INPUT_Y + 35,
            color=arcade.color.WHITE,
            font_size=18,
            font_name="Press Start 2P"
        )

        self.x = 0

    @profile
    def on_mouse_motion(
        self, x: float, y: float, delta_x: float, delta_y: float
    ) -> None:
        mouse.position = (x, y)
        pass

    @profile
    def on_mouse_press(self,x,y,buttons,modifier):
        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_click")

    @profile
    def on_mouse_release(self,x,y,buttons,modifier):
        if self.input_name.touched :
            self.is_typing_name = True
            self.input_name.sprite = texture.get("name_typing")

        if self.input_ip.touched :
            self.is_typing_ip = True
            self.input_ip.sprite = texture.get("ip_typing")

        if self.button_join.touched and self.done_ip and self.ip and len(self.ip)!= 0 and self.done_name and self.name and len(self.name)!= 0:
            self.button_join.sprite = texture.get("add_default")
            data.ip = self.ip
            data.name = self.name
            data.client.display(self.game_menu)

        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_default")
            data.client.display(self.game_menu)

        if self.input_name.touched:
            self.is_typing_name = True
            self.is_typing_ip = False  # désactive l'autre
            self.input_name.sprite = texture.get("name_typing")
            self.input_ip.sprite = texture.get("ip")

        elif self.input_ip.touched:
            self.is_typing_ip = True
            self.is_typing_name = False
            self.input_ip.sprite = texture.get("ip_typing")
            self.input_name.sprite = texture.get("name")


    def on_text(self, text: str):
        if self.is_typing_name and len(self.name) <= 10:
            self.name += text
            self.name_text.text = self.name
        elif self.is_typing_ip and len(self.ip) <= 16:  
            self.ip += text
            self.ip_text.text = self.ip



    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            if self.is_typing_name:
                self.is_typing_name = False
                self.done_name = True
                self.input_name.sprite = texture.get("name")
            if self.is_typing_ip:
                self.is_typing_ip = False
                self.done_ip = True
                self.input_ip.sprite = texture.get("ip")

        elif key == arcade.key.BACKSPACE:
            if self.is_typing_name:
                self.name = self.name[:-1]
                self.name_text.text = self.name
            elif self.is_typing_ip:
                self.ip = self.ip[:-1]
                self.ip_text.text = self.ip

    def on_draw(self):
        self.clear()
        self.box.draw()
        self.button_quit.draw()
        self.button_join.draw()
        self.input_name.draw()
        self.name_text.draw()
        self.input_ip.draw()
        self.ip_text.draw()

    @profile
    def on_update(self,delta_time):
        self.x = (self.x + 1) % 150
