
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
    def on_mouse_release(self,x,y,buttons,modifier):
        if self.input_nickname.touched :
            self.is_typing = True
            self.input_nickname.sprite = texture.get("nickname_typing")

        if self.button_join.touched and self.done and self.nickname and len(self.nickname)!= 0 :
            self.button_join.sprite = texture.get("join_default")
            data.nickname = self.nickname
            data.client.display(GameMenu())
            
        if self.button_setting.touched :
            self.button_setting.sprite = texture.get("settings_default")

        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_default")
            arcade.exit()

    def on_text (self, text:str):
        if self.is_typing == True and len(self.nickname)<=10:
            self.nickname += text
            self.nickname_text.text = self.nickname

    def on_key_press(self, key, modifiers):
        if self.is_typing:
            if key == arcade.key.ENTER:
                self.is_typing = False
                self.done = True
                data.client.display(GameMenu())
                data.nickname = self.nickname
            elif key == arcade.key.BACKSPACE:
                self.nickname = self.nickname[:-1]
                self.nickname_text.text = self.nickname
                
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
