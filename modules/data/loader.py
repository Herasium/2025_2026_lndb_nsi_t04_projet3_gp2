import arcade

from modules.data import data,texture

class Loader:

    def __init__(self):
        pass

    def load_images(self):
        
        # Font
        texture.add("main_background",arcade.Sprite("assets/homescreen/homescreen_v1.png"))
        texture.add("join_background",arcade.Sprite("assets/join_background/server_screen.png"))
        texture.add("houses_background",arcade.Sprite("assets/join_background/houses_night.png"))
        texture.add("night_sky",arcade.Sprite("assets/join_background/sky_night.png"))
        texture.add("big_moon",arcade.Sprite("assets/join_background/moon.png"))
        texture.add("houses_background_day",arcade.Sprite("assets/join_background/houses_day.png"))
        texture.add("day_sky",arcade.Sprite("assets/join_background/sky_day.png"))
        texture.add("sun",arcade.Sprite("assets/join_background/sun.png"))




        # MainMenu
        texture.add("join_default",arcade.Sprite("assets/buttons/join_default.png"))
        texture.add("join_click",arcade.Sprite("assets/buttons/join_click.png"))
        texture.add("join_hover",arcade.Sprite("assets/buttons/join_hover.png"))

        texture.add("ip",arcade.Sprite("assets/buttons/add_adresse.png"))
        texture.add("name",arcade.Sprite("assets/buttons/add_nom.png"))
        texture.add("name_typing",arcade.Sprite("assets/buttons/add_typing.png"))
        texture.add("ip_typing",arcade.Sprite("assets/buttons/add_typing.png"))


        texture.add("nickname",arcade.Sprite("assets/buttons/Nickname_Button.png"))
        texture.add("nickname_typing",arcade.Sprite("assets/buttons/Nickname_Button_Typing.png"))

        texture.add("settings_click",arcade.Sprite("assets/icons/settings_click.png"))
        texture.add("settings_default",arcade.Sprite("assets/icons/settings_default.png"))

        texture.add("quit_click",arcade.Sprite("assets/icons/quit_click.png"))
        texture.add("quit_default",arcade.Sprite("assets/icons/quit_default.png"))

        texture.add("server_bg",arcade.Sprite("assets/server_join/server_bg.png"))
        texture.add("server_case_default",arcade.Sprite("assets/server_join/server_case_default.png"))
        texture.add("server_case_hover",arcade.Sprite("assets/server_join/server_case_hover.png"))

        texture.add("server_online",arcade.Sprite("assets/status/status_0.png"))
        texture.add("server_waiting",arcade.Sprite("assets/status/status_1.png"))
        texture.add("server_offline",arcade.Sprite("assets/status/status_2.png"))

        texture.add("add_default",arcade.Sprite("assets/buttons/add_default.png"))
        texture.add("add_click",arcade.Sprite("assets/buttons/add_click.png"))
        texture.add("add_hover",arcade.Sprite("assets/buttons/add_hover.png"))


        texture.add("box",arcade.Sprite("assets/server_join/server_bg.png"))

        # Load bars
        texture.add("load_bar00",arcade.Sprite("assets/load_bars/load_bar00.png"))
        texture.add("load_bar01",arcade.Sprite("assets/load_bars/load_bar01.png"))
        texture.add("load_bar02",arcade.Sprite("assets/load_bars/load_bar02.png"))
        texture.add("load_bar03",arcade.Sprite("assets/load_bars/load_bar03.png"))
        texture.add("load_bar04",arcade.Sprite("assets/load_bars/load_bar04.png"))
        texture.add("load_bar05",arcade.Sprite("assets/load_bars/load_bar05.png"))
        texture.add("load_bar06",arcade.Sprite("assets/load_bars/load_bar06.png"))
        texture.add("load_bar07",arcade.Sprite("assets/load_bars/load_bar07.png"))
        texture.add("load_bar08",arcade.Sprite("assets/load_bars/load_bar08.png"))
        texture.add("load_bar09",arcade.Sprite("assets/load_bars/load_bar09.png"))
        texture.add("load_bar10",arcade.Sprite("assets/load_bars/load_bar10.png"))
        texture.add("load_bar11",arcade.Sprite("assets/load_bars/load_bar11.png"))
        texture.add("load_bar12",arcade.Sprite("assets/load_bars/load_bar12.png"))
        texture.add("load_bar13",arcade.Sprite("assets/load_bars/load_bar13.png"))
        texture.add("load_bar14",arcade.Sprite("assets/load_bars/load_bar14.png"))
        texture.add("load_bar15",arcade.Sprite("assets/load_bars/load_bar15.png"))
        texture.add("load_bar16",arcade.Sprite("assets/load_bars/load_bar16.png"))
        texture.add("load_bar17",arcade.Sprite("assets/load_bars/load_bar17.png"))
        texture.add("load_bar18",arcade.Sprite("assets/load_bars/load_bar18.png"))
        texture.add("load_bar19",arcade.Sprite("assets/load_bars/load_bar19.png"))

        texture.add("table",arcade.Sprite("assets/homescreen/table.png"))

    def load(self):
        self.load_images()
        self.load_font()


    def load_font(self):
        arcade.load_font("assets/fonts/press_start.ttf")