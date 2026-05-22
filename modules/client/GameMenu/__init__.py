from modules.client.toolbox.entity import Entity
from typing import List
from modules.client.toolbox.text import Text
import asyncio
from modules.data import texture
from modules.client.mouse import mouse
from line_profiler import profile
from modules.data import data
import arcade
import traceback
from modules.client.WaitingMenu import WaitingMenu
from modules.client.NewserverMenu import NewserverMenu
from modules.client.orchestrator import Orchestrator



class GameMenu(arcade.View):

    def __init__(self):
        super().__init__()

        self.camera = 0

        self.background_color: arcade.color = arcade.color.BLACK
        self.name = "GameMenu"

        self.data: List[str] = []
        # self.servers = [
        #     {"ip":"localhost","name":"localhost"},
        #     {"ip":"192.168.3.97","name":"server"},
        # ]

        # self.servers.append({"ip": data.ip, "name": data.name},)

        #1: En Cours
        #0: Hors Ligne
        #2: En Ligne

        self.setup_texts()

        

        self.bg = Entity(0,0,1920,1080,texture.get("join_background"))
        self.cadre = Entity(320,220,256*5,128*5,texture.get("server_bg"))
        self.x = 0
        self._fetch_task = asyncio.run_coroutine_threadsafe(
            self._fetch_and_update(),
            data.loop,
        )
        
        self.button_quit = Entity(1820, 990, 64, 64,texture.get("quit_default"))

        self.add_server = Entity(520,70,80*5,20*5,texture.get("add_default"))

    async def _fetch_and_update(self) -> None:
        try:
            for i in data.servers:     
                self.data.append({"nom": i["name"], "nombre": 0, "max": 0, "status": 1})

            for index, i in enumerate(data.servers):     
                try:
                    new_data = await data.client.get_server_informations(i["ip"], i["name"])
                except Exception as exc:
                    pass
                self.data[index] = new_data
        except Exception as exc:
            pass

    def setup_texts(self) -> None:

        self.server: List[Text] = []
        self.case_server: List[Entity] = []

        a = (256*3.5) + 5
        for i in self.data :
            a = a - 36*5
            if i["status"] == 0 :
                self.status = texture.get("server_offline")
            elif i["status"] == 1 :
                self.status = texture.get("server_waiting")
            elif i["status"] == 2 :
                self.status = texture.get("server_online")

            self.server.append(
                [Text(
                    x=960,
                    y=a + self.camera,
                    text=f"{i["nom"]}  {i["nombre"]}/{i["max"]}",
                    align=("center", "center"),
                    size=18,
                ),
                Entity(
                    x=500,
                    y=a-25+self.camera,
                    width=32*1.5,
                    height=32*1.5,
                    sprite=self.status
                )]
            )
            
        b = (256*3) + 42
        for i in self.data:
            b = b - 36*5
            self.case_server.append(
                Entity(
                    x=320,
                    y=b + self.camera,
                    width=256*5,
                    height=36*5,
                    sprite=texture.get("server_case_default"),
                )
            )
        for i in self.case_server :
            if i.touched:
                i.sprite = texture.get("server_case_hover")
            else:
                i.sprite = texture.get("server_case_default")

    @profile
    def on_mouse_motion(
        self, x: float, y: float, delta_x: float, delta_y: float
    ) -> None:
        mouse.position = (x, y)

        if self.add_server.touched :
            self.add_server.sprite = texture.get("add_hover")
        else :
            self.add_server.sprite = texture.get("add_default")


    @profile
    def on_mouse_press(self,x,y,buttons,modifier):
        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_click")

        if self.add_server.touched :
            self.add_server.sprite = texture.get("add_click")


    @profile
    def on_mouse_release(self,x,y,buttons,modifier):
        if self.button_quit.touched :
            self.button_quit.sprite = texture.get("quit_default")
            arcade.exit()

        if self.add_server.touched :
            data.client.display(NewserverMenu(self))

        for i in range(len(self.case_server)):
            server = self.data[i]
            button = self.case_server[i]
            s = data.servers[i]
            ip = s["ip"]
            name = s["name"]
            if button.touched and server["status"] == 2:
                button.sprite = texture.get("server_case_default")
                #Server Connection
                orc = Orchestrator(ip)
                future = asyncio.run_coroutine_threadsafe(orc.run(), data.loop)

                def on_coroutine_exit(fut):
                    def switch_view_main_thread(delta_time):
                        data.client.display(GameMenu())
                        arcade.unschedule(switch_view_main_thread)
                    arcade.schedule(switch_view_main_thread, 1 / 60)
                future.add_done_callback(on_coroutine_exit)


    def on_draw(self):
        self.clear()
        self.bg.draw()
        self.cadre.draw()
        self.button_quit.draw()
        self.add_server.draw()

        for n in self.case_server:
            n.draw()

        for i in self.server:
            i[0].draw()
            i[1].draw()
        
    @profile
    def on_update(self,delta_time):
        self.setup_texts()

    def on_mouse_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None:
        """Met à jour le décalage vertical de la caméra et reconstruit la mise en page."""
        
        self.camera += scroll_y * -data.MOUSE_SENSI
        self.camera = max(self.camera, 0)
        self.camera = min(self.camera, data.MAX_SCROLL)
