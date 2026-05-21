import arcade
from modules.client.toolbox.entity import Entity
from modules.client.toolbox.text import Text
from modules.data import texture, data
from modules.client.Abstarct import AbstractVotingMenu, BaseGameMenu


class MoonFighterMenu(BaseGameMenu):
    def __init__(self):
        super().__init__("MoonFighterMenu")
        self.btn_yes = Text(x=1920/2 - 150, y=500, width=200, height=80, text="PASSER LA NUIT")
        self.btn_no = Text(x=1920/2 + 150, y=500, width=200, height=80, text="NE RIEN FAIRE")
        self.callback = None

    def run(self, state, payload):
        self.title_text.text = "GUERRIER DE LA LUNE"
        self.subtitle_text.text = "Voulez-vous intercepter les actions nocturnes et forcer le passage au jour ?"
        if payload:
            self.callback = payload.get("callback")

    def on_mouse_motion(self, x, y, dx, dy):
        super().on_mouse_motion(x, y, dx, dy)


    def on_mouse_press(self, x, y, buttons, modifier):
        super().on_mouse_press(x, y, buttons, modifier)
        if self.callback:
            if self.btn_yes.touched: self.callback(1)
            elif self.btn_no.touched: self.callback(0)

    def on_draw(self):
        super().on_draw()
        for btn, color in [(self.btn_yes, (0, 100, 0)), (self.btn_no, (100, 0, 0))]:
            c = (color[0]+30, color[1]+30, color[2]+30) if getattr(btn, "touched", False) else color
            btn.draw()


class FortuneTellerMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("FortuneTellerMenu")

    def run(self, state, payload):
        if state == "start":
            self.title_text.text = "VOYANTE"
            self.subtitle_text.text = "Concentration... Vos visions s'éveillent."
            self.buttons.clear()
        elif state == "vote" and payload:
            self.title_text.text = "CLAIRVOYANCE"
            self.subtitle_text.text = "Sélectionnez l'identité d'un joueur pour inspecter son rôle secret."
            self.callback = payload.get("callback")
            self._build_grid(payload.get("villagers", []))
        elif state == "result" and payload:
            self.title_text.text = "RÉVÉLATION MENTALE"
            self.subtitle_text.text = f"Le joueur {payload.get('name')} possède le rôle de : {payload.get('role').upper()}"
            self.buttons.clear()
        elif state == "end":
            self.title_text.text = "FIN DES VISIONS"
            self.subtitle_text.text = "Vos yeux se ferment, les esprits s'éloignent."
            self.buttons.clear()


class BlackWolfMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("BlackWolfMenu")
        self.btn_infect = None
        self.btn_kill = None

    def run(self, state, payload):
        if state == "start":
            self.title_text.text = "LOUP NOIR"
            self.subtitle_text.text = "Le pouvoir de mutation de la meute est disponible."
            self.btn_infect = self.btn_kill = None
        elif state == "vote" and payload:
            self.title_text.text = "INFECTION DU PACTE"
            victim = payload.get("villager", {})
            self.subtitle_text.text = f"Souhaitez-vous infecter {victim.get('name')} pour le convertir ou le laisser mourir ?"
            self.callback = payload.get("callback")
            self.btn_infect = Text(x=1920/2 - 150, y=500, width=200, height=80, text="INFECTER")
            self.btn_kill = Text(x=1920/2 + 150, y=500, width=200, height=80, text="LAISSER MOURIR")
            self.choices = [victim, None]
        elif state == "end":
            self.title_text.text = "MUTATION TERMINÉE"
            self.subtitle_text.text = "La bête se retire."
            self.btn_infect = self.btn_kill = None

    def on_mouse_motion(self, x, y, dx, dy):
        super().on_mouse_motion(x, y, dx, dy)


    def on_mouse_press(self, x, y, buttons, modifier):
        super().on_mouse_press(x, y, buttons, modifier)
        if self.callback:
            if self.btn_infect and self.btn_infect.touched: self.callback(self.choices[0])
            elif self.btn_kill and self.btn_kill.touched: self.callback(self.choices[1])

    def on_draw(self):
        if self.btn_infect:
            BaseGameMenu.on_draw(self)
            for btn, col in [(self.btn_infect, (148, 0, 211)), (self.btn_kill, (50, 50, 50))]:
                c = (col[0]+30, col[1]+30, col[2]+30) if getattr(btn, "touched", False) else col
                btn.draw()
        else:
            super().on_draw()


class MarkGaryonMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("MarkGaryonMenu")

    def run(self, state, payload):
        if state == "died_alert":
            self.title_text.text = "ALERTE VENGEANCE"
            self.subtitle_text.text = "Mark Garyson est mort ! Son exécution déclenche un tir de riposte."
            self.buttons.clear()
        elif state == "revenge_vote" and payload:
            self.title_text.text = "DERNIER SOUFFLE"
            self.subtitle_text.text = "Vous succombez... Choisissez immédiatement quel joueur vous emportez dans votre tombe."
            self.callback = payload.get("callback")
            self._build_grid(payload.get("villagers", []))


class WitchMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("WitchMenu")
        self.ui_buttons = []
        self.action_codes = []

    def run(self, state, payload):
        self.ui_buttons.clear()
        self.action_codes.clear()
        self.buttons.clear()

        if state == "start":
            self.title_text.text = "SORCIÈRE"
            self.subtitle_text.text = "Préparation des chaudrons et des essences magiques..."
        elif state == "potion_choice" and payload:
            self.title_text.text = "POTIONS DISPONIBLES"
            server_data = payload.get("server_payload", {})
            victim_name = server_data.get("name", "Personne")
            self.subtitle_text.text = f"La cible des loups est : {victim_name}."
            self.callback = payload.get("callback")
            
            y_pos = 500
            if not server_data.get("save", False) and server_data.get("id") is not None:
                self.ui_buttons.append(Text(x=1920/2 , y=y_pos+ 75, width=220, height=80, text="POTION DE VIE"))
                self.action_codes.append(1)
            if not server_data.get("genocide", False):
                self.ui_buttons.append(Text(x=1920/2, y=y_pos, width=220, height=80, text="POTION DE MORT"))
                self.action_codes.append(2)
            
            self.ui_buttons.append(Text(x=1920/2 , y=y_pos- 75, width=220, height=80, text="PASSER LE TOUR"))
            self.action_codes.append(0)
        elif state == "genocide_start":
            self.title_text.text = "SÉLECTION DU POISON"
            self.subtitle_text.text = "Ouverture du grimoire d'élimination."
        elif state == "genocide_vote" and payload:
            self.title_text.text = "VERSER LE VENIN"
            self.subtitle_text.text = "Sélectionnez la cible qui subira votre potion d'empoisonnement."
            self.callback = payload.get("callback")
            self._build_grid(payload.get("villagers", []))
        elif state == "end":
            self.title_text.text = "FIN DE L'ALCHIMIE"
            self.subtitle_text.text = "Vos flacons sont rangés."

    def on_mouse_motion(self, x, y, dx, dy):
        super().on_mouse_motion(x, y, dx, dy)


    def on_mouse_press(self, x, y, buttons, modifier):
        if self.ui_buttons:
            super().on_mouse_press(x, y, buttons, modifier)
            if self.callback:
                for idx, btn in enumerate(self.ui_buttons):
                    if btn.touched:
                        self.callback(self.action_codes[idx])
                        break
        else:
            super().on_mouse_press(x, y, buttons, modifier)

    def on_draw(self):
        if self.ui_buttons:
            BaseGameMenu.on_draw(self)
            for btn in self.ui_buttons:
                btn.draw()
        else:
            super().on_draw()


class PyromaneMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("PyromaneMenu")
        self.btn_detonate = None

    def run(self, state, payload):
        self.btn_detonate = None
        if state == "start":
            self.title_text.text = "PYROMANE"
            self.subtitle_text.text = "L'odeur du carburant se propage."
            self.buttons.clear()
        elif state == "vote" and payload:
            self.title_text.text = "STATION DE COUVERTURE"
            self.subtitle_text.text = "Aspergez un joueur d'essence OU enclenchez la mise à feu globale."
            self.callback = payload.get("callback")
            self._build_grid(payload.get("villagers", []))
            self.btn_detonate = Text(x=1920/2, y=200, width=300, height=70, text="TOUT FAIRE SAUTER")
        elif state == "explosion_alert":
            self.title_text.text = "DÉTONATION SOUDAINE"
            self.subtitle_text.text = "Une explosion majeure retentit ! Les cibles imbibées s'enflamment."
            self.buttons.clear()
        elif state == "end":
            self.title_text.text = "FIN DU BRASIER"
            self.subtitle_text.text = "Les étincelles s'estompent."
            self.buttons.clear()

    def on_mouse_motion(self, x, y, dx, dy):
        super().on_mouse_motion(x, y, dx, dy)


    def on_mouse_press(self, x, y, buttons, modifier):
        super().on_mouse_press(x, y, buttons, modifier)
        if self.callback and self.btn_detonate and self.btn_detonate.touched:
            self.callback({"id":-1})

    def on_draw(self):
        super().on_draw()
        if self.btn_detonate:
            c = (255, 69, 0) if getattr(self.btn_detonate, "touched", False) else (180, 40, 0)
            self.btn_detonate.draw()

class WerewolfMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("WerewolfMenu")
        self.action_info_text = Text(x=1920/2, y=680, width=1200, height=50, text="")

    def run(self, state, payload):
        self.title_text.text = "PHASE DES LOUPS-GAROUS"
        
        if state == "start":
            self.subtitle_text.text = "La nuit tombe... La meute se rassemble."
            self.action_info_text.text = "Préparez-vous à désigner votre prochaine victime avec vos frères..."
            self.buttons.clear()
            self.choices.clear()
            self.callback = None

        elif state == "vote":
            self.subtitle_text.text = "Le sang va couler."
            self.action_info_text.text = "Sélectionnez un villageois à dévorer :"
            
            villagers = payload.get("villagers", [])
            self.callback = payload.get("callback")
            
            self._build_grid(villagers)

        elif state == "end":
            self.subtitle_text.text = "La chasse est terminée."
            self.action_info_text.text = "Votre choix est scellé. Les loups se rendorment..."
            self.buttons.clear()
            self.choices.clear()
            self.callback = None

    def on_mouse_press(self, x: float, y: float, buttons: int, modifier: int):
        active_callback = self.callback
        
        super().on_mouse_press(x, y, buttons, modifier)
        
        if active_callback and not self.callback:
            self.action_info_text.text = "Vote enregistré ! En attente des autres membres de la meute..."
            self.buttons.clear()
            self.choices.clear()

    def on_draw(self):
        super().on_draw()
        self.action_info_text.draw()

class DeathEaterMenu(AbstractVotingMenu):
    def __init__(self):
        super().__init__("DeathEaterMenu")

    def run(self, state, payload):
        if state == "start":
            self.title_text.text = "MANGEUR DE MORT"
            self.subtitle_text.text = "Rapprochement avec le plan spectral..."
            self.buttons.clear()
        elif state == "vote" and payload:
            self.title_text.text = "INTRUSION AU CIMETIÈRE"
            self.subtitle_text.text = "Choisissez l'âme d'un joueur décedé afin de le ressusciter en jeu."
            self.callback = payload.get("callback")
            self._build_grid(payload.get("deads", []))


class DayVote(AbstractVotingMenu):
    def __init__(self):
        super().__init__("DayVote")
        self.houses_bg_day = Entity(0,0,1920,1080,texture.get("houses_background_day"))
        self.sky_bg_day = Entity(0,0,1920,1080,texture.get("day_sky"))
        self.sun_bg = Entity(0,0,1920,1080,texture.get("sun"))

    def run(self, state, payload):
        self.title_text.text = "TRIBUNAL DU VILLAGE"
        self.subtitle_text.text = "Délibération publique. Votez pour le suspect à éliminer sur le bûcher."
        if payload:
            self.callback = payload.get("callback")
            self._build_grid(payload.get("villagers", []))

    def on_draw(self):
        super().on_draw()
        self.sky_bg_day.draw()
        self.houses_bg_day.draw()
        self.sun_bg.draw()
        self.title_text.draw()
        self.subtitle_text.draw()

        for btn in self.buttons:
            btn.draw()

        self.render_chat()
    