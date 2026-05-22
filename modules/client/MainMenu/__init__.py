
from modules.client.toolbox.entity import Entity
from modules.data import texture, data
from modules.client.mouse import mouse
from line_profiler import profile
import arcade
from modules.client.GameMenu.__init__ import GameMenu


class MainMenu(arcade.View):

    def __init__(self):
        super().__init__()
        self.background_color: arcade.color = arcade.color.BLACK
        self.name = "MainMenu"
        self.bg = Entity(0,0,1920,1080,texture.get("main_background"))
        self.button_join = Entity(100,200,400,100,texture.get("join_default"))
        self.button_setting = Entity(1730,990,64,64,texture.get("settings_default"))
        self.button_quit = Entity(1820, 990, 64, 64,texture.get("quit_default"))
        self.input_nickname = Entity(100,300,400,100, texture.get("nickname"))
        self.done = True
        self.nickname = ""
        self.is_typing = False
        self.x = 0
        self.nickname_text = arcade.Text(
            text="",
            x=125,
            y=335,
            color=arcade.color.WHITE,
            font_size=18,
            font_name="Press Start 2P"
        )

        data.main_menu = MainMenu
    @profile
    def on_mouse_motion(
        self, x: float, y: float, delta_x: float, delta_y: float
    ) -> None:
        mouse.position = (x, y)
        if self.button_join.touched and self.nickname:
            self.button_join.sprite = texture.get("join_hover")
        else:
            self.button_join.sprite = texture.get("join_default")


    @profile
    def on_mouse_press(self,x,y,buttons,modifier):
        if self.button_join.touched :
            self.button_join.sprite = texture.get("join_click")

        if self.button_setting.touched :
            self.button_setting.sprite = texture.get("settings_click")

        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_click")


    @profile
    def on_mouse_release(self, x, y, buttons, modifier):
        if self.button_join.touched and self.done_ip and self.ip and self.done_name and self.name:
            self.button_join.sprite = texture.get("add_default")
            data.ip = self.ip
            data.name = self.name
            data.client.display(self.game_menu)

        if self.button_quit.touched:
            self.button_quit.sprite = texture.get("quit_default")
            data.client.display(self.game_menu)

        if self.input_name.touched:
            self.is_typing_name = True
            self.is_typing_ip = False
            self.input_name.sprite = texture.get("name_typing")
            self.input_ip.sprite = texture.get("ip") if len(self.ip) == 0 else texture.get("ip_full")

        elif self.input_ip.touched:
            self.is_typing_ip = True
            self.is_typing_name = False
            self.input_ip.sprite = texture.get("ip_typing")
            self.input_name.sprite = texture.get("name") if len(self.name) == 0 else texture.get("name_full")

    def on_text(self, text: str):
        if self.is_typing_name and len(self.name) <= 10:
            self.name += text
            self.name_text.text = self.name
            if len(self.name) >= 10:
                self.input_name.sprite = texture.get("name_full")
        elif self.is_typing_ip and len(self.ip) <= 16:
            self.ip += text
            self.ip_text.text = self.ip
            if len(self.ip) >= 16:
                self.input_ip.sprite = texture.get("ip_full")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            if self.is_typing_name:
                self.is_typing_name = False
                self.done_name = True
                self.input_name.sprite = texture.get("name") if len(self.name) == 0 else texture.get("name_full")
            if self.is_typing_ip:
                self.is_typing_ip = False
                self.done_ip = True
                self.input_ip.sprite = texture.get("ip") if len(self.ip) == 0 else texture.get("ip_full")

        elif key == arcade.key.BACKSPACE:
            if self.is_typing_name:
                self.name = self.name[:-1]
                self.name_text.text = self.name
                self.input_name.sprite = texture.get("name_typing")
            elif self.is_typing_ip:
                self.ip = self.ip[:-1]
                self.ip_text.text = self.ip
                self.input_ip.sprite = texture.get("ip_typing")
                
    def on_draw(self):
        self.clear()
        self.bg.draw()
        self.button_join.draw()
        self.button_setting.draw()
        self.button_quit.draw()
        self.input_nickname.draw()
        self.nickname_text.draw()

    @profile
    def on_update(self,delta_time):
        self.x = (self.x + 1) % 150
