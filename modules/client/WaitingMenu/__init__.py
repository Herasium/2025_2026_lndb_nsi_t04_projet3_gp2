from modules.client.toolbox.entity import Entity
from modules.client.toolbox.text import Text
from typing import List
from modules.data import texture, data
from modules.client.mouse import mouse
from line_profiler import profile
import math
import arcade



class WaitingMenu(arcade.View):

    def __init__(self,data):

        super().__init__()
        self.background_color: arcade.color = arcade.color.BLACK
        self.name = "WaitingMenu"

        self.button_quit = Entity(1820, 990, 64, 64,texture.get("quit_default"))
        self.x = 0
        
        self.data: List[str] = data
        self.nb_perso = 0
        self.nb_perso_enligne: List[str] = []
        self.perso: List[str] = []

        for n in self.data:
            self.nb_perso += 1
            self.nb_perso_enligne.append(n["name"])

        a = 2*(math.pi) / self.nb_perso
        b = 0
        for i in self.nb_perso_enligne:
            b += a
            self.perso.append(
                Text(
                    x=290*(math.cos(b))+960,
                    y=290*(math.sin(b))+540,
                    text=f"{i}",
                    align=("center", "center"),
                    size=12,
                )
            )


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
        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_default")
            arcade.exit()

    def on_draw(self):
        self.clear()
        self.button_quit.draw()
        arcade.draw_circle_filled(960, 540, 260, [109, 155, 195, 255])

        for p in self.perso:
            p.draw()

    @profile
    def on_update(self,delta_time):
        self.x = (self.x + 1) % 150
