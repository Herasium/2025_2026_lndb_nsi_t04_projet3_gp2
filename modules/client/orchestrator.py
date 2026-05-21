# gaming bitches
import multiprocessing
import json
import pyglet
import asyncio
import queue

from modules.data import data
from modules.logger import Logger

from modules.client.Abstarct import WaitingMenu
from modules.client.Abstarct import RoleAttribution
from modules.client.Abstarct import NightMenu
from modules.client.Abstarct import DayMenu
from modules.client.Abstarct import KilledMenu
from modules.client.Abstarct import AliveMenu
from modules.client.Abstarct import DayDeath
from modules.client.Abstarct import GameEndMenu

from modules.client.Roles import MoonFighterMenu
from modules.client.Roles import FortuneTellerMenu
from modules.client.Roles import WerewolfMenu
from modules.client.Roles import BlackWolfMenu
from modules.client.Roles import MarkGaryonMenu
from modules.client.Roles import WitchMenu
from modules.client.Roles import PyromaneMenu
from modules.client.Roles import DeathEaterMenu
from modules.client.Roles import DayVote

logger = Logger("Orchestrator")

class Orchestrator:

    def __init__(self, ip):
        self.ip = ip
        self.rx = None
        self.tx = None
        self.loop = None

        self.chat_access = [0]
        self.chat_history = [[] for i in range(10)]
        self.current_chat = 0
        self.typing = ""
        self.is_typing = False
        self.chat_index = {
            "villager": [1],
            "werewolf": [1,3], 
            "black_wolf": [1,3],
            "pyromane": [1,4],
            "moon_fighter": [1,5], 
            "mark_garyson": [1,7],
            "fortune_teller": [1,8],
            "witch": [1,9],
            "death_eater": [1,6],
        }

        self.role = None
        
        # 0: All
        # 1: Alive
        # 2: Dead
        # 3: Werewolves + Black Wolves
        # 4: Pyromane
        # 5: Moon Fighter
        # 6: Death Eater
        # 7: Mark Garyson
        # 8: Fortune Teller
        # 9: Witch

        data.orch = self

        # State tracking parameters to optimize menu redrawing loops
        self.active_menu_name = None
        self.current_menu = None

    async def send(self, opcode, payload=None):
        if payload is None:
            payload = {}
        message = json.dumps({"opcode": opcode, "data": payload})
        self.tx.put_nowait(message)

    def _safe_send(self, opcode, payload):
        """Thread-safe pipeline to dispatch responses out from UI callback frames."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.send(opcode, payload), self.loop)

    def _navigate_or_update(self, menu_name, menu_class, state, data_payload=None):
        """
        Manages UI views. If target menu is already active, calls .run() on it.
        Otherwise, creates a new instance, mounts it, and stores the reference.
        """
        def process_ui_mutation(dt):
            if self.active_menu_name == menu_name and self.current_menu:
                self.current_menu.run(state, data_payload)
            else:
                instance = menu_class()
                self.active_menu_name = menu_name
                self.current_menu = instance
                
                data.client.display(instance)
                if menu_name != "MainMenu":
                    instance.run(state, data_payload)

        pyglet.clock.schedule_once(process_ui_mutation, 0)

    # --- Structural Layout State Handlers ---

    async def handle_waiting_room_list_update(self, payload):
        self.chat_access = [0]
        self._navigate_or_update("WaitingMenu", WaitingMenu, "update", payload)

    async def handle_role_change(self, payload):
        self.role = payload.get("role", None)
        self.chat_access = self.chat_index.get(self.role,[1])
        self._navigate_or_update("RoleAttribution", RoleAttribution, "change", payload)

    async def handle_player_role(self, payload):
        self.role = payload.get("role", None)
        self.chat_access = self.chat_index.get(self.role,[1])
        self._navigate_or_update("RoleAttribution", RoleAttribution, "change", payload)

    async def handle_switch_night(self, payload):
        self._navigate_or_update("NightMenu", NightMenu, "transition", payload)

    async def handle_switch_day(self, payload):
        self._navigate_or_update("DayMenu", DayMenu, "transition", payload)

    async def handle_killed(self, payload):
        self.chat_access = [2]
        self._navigate_or_update("KilledMenu", KilledMenu, "dead", payload)

    async def handle_alive(self, payload):
        self.chat_access = self.chat_index.get(self.role,[1])
        self._navigate_or_update("AliveMenu", AliveMenu, "resurrected", payload)

    async def handle_day_death(self, payload):
        self._navigate_or_update("DayDeath", DayDeath, "announcement", payload)

    async def handle_game_end(self, payload):
        self._navigate_or_update("GameEndMenu", GameEndMenu, "end", payload)

    # --- Interactive In-Game Mechanics Handlers ---

    async def handle_night_moon_fighter_vote(self, payload):
        ui_data = {"callback": lambda vote: self._safe_send("night_moon_fighter_response", {"vote": vote})}
        self._navigate_or_update("MoonFighterMenu", MoonFighterMenu, "vote", ui_data)

    async def handle_night_fortune_teller_start(self, payload):
        self._navigate_or_update("FortuneTellerMenu", FortuneTellerMenu, "start", payload)

    async def handle_night_fortune_teller_vote(self, payload):
        ui_data = {
            "villagers": payload["villagers"],
            "callback": lambda choice: self._safe_send("night_fortune_teller_vote_response", {"vote": choice["id"]})
        }
        self._navigate_or_update("FortuneTellerMenu", FortuneTellerMenu, "vote", ui_data)

    async def handle_night_fortune_teller_result(self, payload):
        self._navigate_or_update("FortuneTellerMenu", FortuneTellerMenu, "result", payload)

    async def handle_night_fortune_teller_end(self, payload):
        self._navigate_or_update("FortuneTellerMenu", FortuneTellerMenu, "end", payload)

    async def handle_night_werewolf_start(self, payload):
        self._navigate_or_update("WerewolfMenu", WerewolfMenu, "start", payload)

    async def handle_night_werewolf_vote(self, payload):
        ui_data = {
            "villagers": payload["villagers"],
            "callback": lambda choice: self._safe_send("night_werewolf_vote_response", {"vote": choice["id"]})
        }
        self._navigate_or_update("WerewolfMenu", WerewolfMenu, "vote", ui_data)

    async def handle_night_werewolf_end(self, payload):
        self._navigate_or_update("WerewolfMenu", WerewolfMenu, "end", payload)

    async def handle_night_black_wolfs_start(self, payload):
        self._navigate_or_update("BlackWolfMenu", BlackWolfMenu, "start", payload)

    async def handle_night_black_wolf_vote(self, payload):
        ui_data = {
            "villager": payload["villager"],
            "callback": lambda choice: self._safe_send("night_black_wolf_vote_response", {"vote": choice["id"] if choice else None})
        }
        self._navigate_or_update("BlackWolfMenu", BlackWolfMenu, "vote", ui_data)

    async def handle_night_black_wolf_end(self, payload):
        self._navigate_or_update("BlackWolfMenu", BlackWolfMenu, "end", payload)

    async def handle_mark_garyon_died(self, payload):
        self._navigate_or_update("MarkGaryonMenu", MarkGaryonMenu, "died_alert", payload)

    async def handle_mark_garyon_vote(self, payload):
        ui_data = {
            "villagers": payload["villagers"],
            "callback": lambda choice: self._safe_send("mark_garyon_response", {"vote": choice["id"]})
        }
        self._navigate_or_update("MarkGaryonMenu", MarkGaryonMenu, "revenge_vote", ui_data)

    async def handle_night_witch_start(self, payload):
        self._navigate_or_update("WitchMenu", WitchMenu, "start", payload)

    async def handle_night_witches_vote(self, payload):
        ui_data = {
            "server_payload": payload,
            "callback": lambda choice_code: self._safe_send("night_witches_vote_response", {"vote": choice_code})
        }
        self._navigate_or_update("WitchMenu", WitchMenu, "potion_choice", ui_data)

    async def handle_night_witch_genocide_start(self, payload):
        self._navigate_or_update("WitchMenu", WitchMenu, "genocide_start", payload)

    async def handle_night_witch_genocide_vote(self, payload):
        ui_data = {
            "villagers": payload["villagers"],
            "callback": lambda choice: self._safe_send("night_witch_genocide_vote_response", {"vote": choice["id"]})
        }
        self._navigate_or_update("WitchMenu", WitchMenu, "genocide_vote", ui_data)

    async def handle_night_witch_end(self, payload):
        self._navigate_or_update("WitchMenu", WitchMenu, "end", payload)

    async def handle_night_pyromane_start(self, payload):
        self._navigate_or_update("PyromaneMenu", PyromaneMenu, "start", payload)

    async def handle_night_pyromane_vote(self, payload):
        ui_data = {
            "villagers": payload["villagers"],
            "callback": lambda target_code: self._safe_send("night_pyromane_response", {"vote": target_code["id"]})
        }
        self._navigate_or_update("PyromaneMenu", PyromaneMenu, "vote", ui_data)

    async def handle_pyromane_explosion(self, payload):
        self._navigate_or_update("PyromaneMenu", PyromaneMenu, "explosion_alert", payload)

    async def handle_night_pyromane_end(self, payload):
        self._navigate_or_update("PyromaneMenu", PyromaneMenu, "end", payload)

    async def handle_night_death_eater_start(self, payload):
        self._navigate_or_update("DeathEaterMenu", DeathEaterMenu, "start", payload)

    async def handle_night_death_eater_vote(self, payload):
        ui_data = {
            "deads": payload["deads"],
            "callback": lambda choice: self._safe_send("night_death_eater_vote_response", {"vote": choice["id"]})
        }
        self._navigate_or_update("DeathEaterMenu", DeathEaterMenu, "vote", ui_data)

    async def handle_day_vote(self, payload):
        ui_data = {
            "villagers": payload["villagers"],
            "callback": lambda choice: self._safe_send("day_vote_response", {"vote": choice["id"]})
        }
        self._navigate_or_update("DayVote", DayVote, "vote", ui_data)

    async def handle_chat(self,payload):
        try:
            self.chat_history[payload["room"]].append({"message":payload["message"],"name":payload["name"]})
        except Exception as e:
            print(e)

    def send_chat(self):
        self._safe_send("chat",{"room":self.current_chat,"message":self.typing})
        self.typing = ""

    # --- Runtime Network Loop Operations ---

    async def read(self):

        try:
            raw: str = await self.loop.run_in_executor(
                None, self.rx.get, True, 1.0
            )

        except queue.Empty:
            raw = None
            return

        parsed = json.loads(raw)
        logger.debug(f"Received Packet: {parsed}")

        opcode = parsed.get("opcode")
        payload = parsed.get("data", {})

        handler_name = f"handle_{opcode}"
        handler = getattr(self, handler_name, None)

        if handler:
            await handler(payload)
        else:
            logger.warning(f"Unmapped incoming opcode detected: {opcode}")

    def quit(self):
        data.client.cut()
        self.running = False


    async def run(self):
        self.loop = asyncio.get_running_loop()
        data.client.connect(self.ip)

        self.running = True

        self.rx = data.client.rx_queue
        self.tx = data.client.tx_queue

        await self.send("player_join", {"name": data.nickname})

        while self.running:
            await self.read()
