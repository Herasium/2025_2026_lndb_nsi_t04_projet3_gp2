import arcade
import math

from modules.client.toolbox.entity import Entity
from modules.client.toolbox.text import Text
from modules.data import texture, data
from modules.client.mouse import mouse

class BaseGameMenu(arcade.View):
    """Classe de base fournissant l'arrière-plan et le bouton de fermeture sécurisé."""
    def __init__(self, menu_name):
        super().__init__()
        self.name = menu_name
        self.background_color = arcade.color.BLACK
        self.bg = Entity(0, 0, 1920, 1080, texture.get("join_background"))
        self.button_quit = Entity(1820, 990, 64, 64, texture.get("quit_default"))
        self.title_text = Text(x=1920/2, y=900, width=1000, height=80, text="")
        self.subtitle_text = Text(x=1920/2, y=820, width=1000, height=50, text="")
        self.typing_button = Entity(x=1700,y=600,width=300,height=100)

    def on_mouse_motion(self, x: float, y: float, delta_x: float, delta_y: float):
        mouse.position = (x, y)

    def on_mouse_press(self, x: float, y: float, buttons: int, modifier: int):
        if self.button_quit.touched:
            self.button_quit.sprite = texture.get("quit_click")
            try:
                data.orch.quit()
            except Exception as e:
                print("failed to quit lol",e)
                arcade.exit()

        if self.typing_button.touched:
            data.orch.is_typing = True

    def on_mouse_release(self, x: float, y: float, buttons: int, modifier: int):
        if self.button_quit.touched:
            self.button_quit.sprite = texture.get("quit_default")

    def on_text (self, text:str):
        if data.orch.is_typing:
            data.orch.typing += text

    def render_chat(self):
        orch = data.orch

        if not orch.current_chat in orch.chat_access:
            orch.current_chat = orch.chat_access[0]

        current = orch.current_chat
        messages = orch.chat_history[current][-10:] + [{"name":"","message":""} for i in range(10 - len(orch.chat_history[current][-10:]))]

        y = 900

        for i in messages:
            arcade.draw_text(f"{i["name"]}: {i["message"]}",1700,y)
            y -= 25
        y -=50
        self.typing_button.hitbox.draw()
        arcade.draw_text(f"{data.orch.typing}",1700,y)

    def on_key_press(self, key, modifiers):
        if data.orch.is_typing:
            if key == arcade.key.ENTER:
                data.orch.is_typing = False
                data.orch.send_chat()
            elif key == arcade.key.BACKSPACE:
                data.orch.typing = data.orch.typing[:-1]

    def on_draw(self):
        self.clear()
        if self.bg: self.bg.draw()
        self.title_text.draw()
        self.subtitle_text.draw()
        self.button_quit.draw()
        self.render_chat()


class WaitingMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("WaitingMenu")
        self.players_text = Text(x=1920/2, y=500, width=800, height=400, text="")

    def run(self, state, payload):
        self.title_text.text = "SALON D'ATTENTE"
        status = payload.get("status", 0)
        self.subtitle_text.text = "En attente du lancement par l'hôte..." if status == 0 else "La partie va commencer !"
        
        players = payload.get("players", [])
        names = [p["name"] for p in players]
        self.players_text.text = "Joueurs présents :\n" + ", ".join(names)

        self.table = Entity(1920/2,1080/2,550,550,texture.get("table"),arcade.Vec2(0.5,0.5))

        self.nb_perso = 0
        self.nb_perso_enligne = []
        self.perso = []

        for n in players:
            self.nb_perso += 1
            self.nb_perso_enligne.append(n["name"])

        a = 2*(math.pi) / self.nb_perso
        b = 0
        for i in self.nb_perso_enligne:
            b += a
            self.perso.append(
                Text(
                    x=320*(math.cos(b))+960,
                    y=320*(math.sin(b))+540,
                    text=f"{i}",
                    align=("center", "center"),
                    size=12,
                )
            )



    def on_draw(self):
        super().on_draw()
        self.clear()
        self.table.draw()
        self.title_text.draw()
        self.button_quit.draw()
        for p in self.perso:
            p.draw()
        self.render_chat()


class RoleAttribution(BaseGameMenu):
    def __init__(self):
        super().__init__("RoleAttribution")
        self.role_display = Text(x=1920/2, y=540, width=800, height=100, text="")

    def run(self, state, payload):
        self.title_text.text = "ATTRIBUTION DES RÔLES"
        self.subtitle_text.text = "Découvrez votre identité secrète pour cette partie."
        new_role = payload.get("role", "Inconnu").upper()
        self.role_display.text = f"VOTRE RÔLE : {new_role}"

    def on_draw(self):
        super().on_draw()
        self.role_display.draw()


class NightMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("NightMenu")
        self.moon_rise_speed = 170
        self.font_size = 18
        self.text_y = 740 - 1000
        self.max_font_size = 18
        self.growth_speed = 0.55
        self.button_quit = Entity(1820, 990, 64, 64,texture.get("quit_default"))
        self.bg = Entity(0,0,1920,1080,texture.get("join_background"))
        self.houses_bg = Entity(0,0,1920,1080,texture.get("houses_background"))
        self.sky_bg = Entity(0,0,1920,1080,texture.get("night_sky"))
        self.moon_bg = Entity(0,-1000,1920,1080,texture.get("big_moon"))

    def run(self, state, payload):
        num = payload.get("current_night", 1)
        self.title_text.text = f""
        self.subtitle_text.text = f"NUIT N°{num} Le village s'endort... Fermez les yeux."

    def on_draw(self):
        self.clear()
        # self.bg.draw()
        self.sky_bg.draw()
        self.moon_bg.draw()
        self.subtitle_text.draw()
        self.title_text.draw()
        self.houses_bg.draw()

        self.button_quit.draw()
        self.render_chat()

        

    def on_update(self, delta_time: float):
        if self.moon_bg.y < 0:
            self.moon_bg.y += self.moon_rise_speed * delta_time
            self.moon_bg.y = min(self.moon_bg.y, 0)
            self.text_y += self.moon_rise_speed * delta_time
            self.text_y = min(self.text_y, 740)
            self.subtitle_text.y = self.text_y

class DayMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("DayMenu")
        self.text_y = 740 - 1000
        self.sun_rise_speed = 170
        self.houses_bg_day = Entity(0,0,1920,1080,texture.get("houses_background_day"))
        self.sky_bg_day = Entity(0,0,1920,1080,texture.get("day_sky"))
        self.sun_bg = Entity(0,-700,1920,1080,texture.get("sun"))

    def run(self, state, payload):
        num = payload.get("current_day", 1)
        self.title_text.text = f"JOUR N°{num}"
        self.subtitle_text.text = "Le village se réveille... Qui a survécu ?"

    def on_draw(self):
        self.clear()
        # self.bg.draw()
        self.sky_bg_day.draw()
        self.sun_bg.draw()
        self.subtitle_text.draw()
        self.title_text.draw()
        self.houses_bg_day.draw()

        self.button_quit.draw()
        self.render_chat()

    def on_update(self, delta_time: float):
        if self.sun_bg.y < 0:
            self.sun_bg.y += self.sun_rise_speed * delta_time
            self.sun_bg.y = min(self.sun_bg.y, 0)
            self.text_y += self.sun_rise_speed * delta_time
            self.text_y = min(self.text_y, 740)
            self.subtitle_text.y = self.text_y


class KilledMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("KilledMenu")

    def run(self, state, payload):
        self.title_text.text = "VOUS AVEZ ÉTÉ TUÉ"
        self.subtitle_text.text = "Vous rejoignez le cimetière. Les morts ne parlent pas."


class AliveMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("AliveMenu")

    def run(self, state, payload):
        self.title_text.text = "RÉSURRECTION !"
        self.subtitle_text.text = "Les forces mystiques vous ramènent à la vie parmi les vivants."


class DayDeath(BaseGameMenu):
    def __init__(self):
        super().__init__("DayDeath")
        self.deaths_text = Text(x=1920/2, y=500, width=800, height=400, text="")
        self.houses_bg_day = Entity(0,0,1920,1080,texture.get("houses_background_day"))
        self.sky_bg_day = Entity(0,0,1920,1080,texture.get("day_sky"))
        self.sun_bg = Entity(0,0,1920,1080,texture.get("sun"))


    def run(self, state, payload):
        self.title_text.text = "RAPPORT DES MORTS"
        deaths = payload.get("death", [])
        if not deaths:
            self.subtitle_text.text = "Bonne nouvelle : Personne n'est mort cette nuit !"
            self.deaths_text.text = ""
        else:
            self.subtitle_text.text = "Le réveil est brutal..."
            lines = [f"• {d['name']} (Rôle: {d['role']})" for d in deaths]
            self.deaths_text.text = "\n".join(lines)

    def on_draw(self):
        super().on_draw()
        self.sky_bg_day.draw()
        self.houses_bg_day.draw()
        self.sun_bg.draw()
        self.title_text.draw()
        self.subtitle_text.draw()
        self.deaths_text.draw()
        self.render_chat()


class GameEndMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("GameEndMenu")        
        self.houses_bg_day = Entity(0,0,1920,1080,texture.get("houses_background_day"))
        self.sky_bg_day = Entity(0,0,1920,1080,texture.get("day_sky"))
        self.sun_bg = Entity(0,0,1920,1080,texture.get("sun"))

    def run(self, state, payload):
        winner = payload.get("winner", "Personne").upper()
        self.title_text.text = "FIN DE LA PARTIE"
        self.subtitle_text.text = f"VICTOIRE DE LA FACTION : {winner} !"

    def on_draw(self):
        super().on_draw()
        self.sky_bg_day.draw()
        self.houses_bg_day.draw()
        self.sun_bg.draw()
        self.title_text.draw()
        self.subtitle_text.draw()
        self.render_chat()

class AbstractVotingMenu(BaseGameMenu):
    """Moteur générique de rendu pour les choix ciblés sur des listes de joueurs."""
    def __init__(self, menu_name):
        super().__init__(menu_name)
        self.choices = []
        self.buttons = []
        self.callback = None

    def _build_grid(self, villagers):
        self.choices = villagers
        self.buttons.clear()
        
        w, h, gap_y = 220, 80, 20  
        total = len(villagers)
        if total == 0: return
        
        total_height = (total * h) + ((total - 1) * gap_y)

        start_y = 550 + (total_height / 2) - (h / 2)
        
        x = 1920 / 2
        
        for idx, item in enumerate(villagers):
            y = start_y - (idx * (h + gap_y))
            
            btn = Text(x=x, y=y, width=w, height=h, text=f"{item['name']}")
            self.buttons.append(btn)

    def on_mouse_motion(self, x: float, y: float, delta_x: float, delta_y: float):
        super().on_mouse_motion(x, y, delta_x, delta_y)

    def on_mouse_press(self, x: float, y: float, buttons: int, modifier: int):
        super().on_mouse_press(x, y, buttons, modifier)
        if self.callback:
            for idx, btn in enumerate(self.buttons):
                if btn.touched:
                    self.callback(self.choices[idx])
                    break

    def on_draw(self):
        super().on_draw()
        for btn in self.buttons:
            btn.draw()