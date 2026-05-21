from modules.logger import Logger
from modules.server.opcodes import opcodes
import random
import json
import asyncio
import time

logger = Logger("Game")

class Game:

    def __init__(self):
        logger.info("Initialisation d'une nouvelle partie de Loup-Garou.")
        self.status = 0
        self.players = {}
        self.players_per_roles = {}
        self.min_player_count = 1
        self.waiting_room = []
        self.playing_room = []
        self.death_room = []
        
        # All required roles explicitly registered
        self.roles = [
            "villager", "werewolf", "black_wolf", "pyromane", "moon_fighter", 
            "mark_garyson", "fortune_teller", "witch", "death_eater"
        ]
        self.pending_responses = {}
        self.phase_name = "waiting"         
        self.phase_start_time = None
        self.phase_duration = 0
        self.to_kill = []
        self.current_day = 0
        self.finished = False

        opcodes["chat"] = self.chat

    async def chat(self,message,client):
        text = message["message"]
        room = message["room"]

        for i in self.players:
            await self.send_player(i,"chat",{"message":text,"room":room,"name":client.name})

    def set_game_flags(self):
        self.black_wolf_eaten = False
        self.moon_fighter_skiped = False
        self.pyromane_bombed = []
        self.crazy_dave_up = False
        self.witch_save_used = False
        self.witch_genocide_used = False
        self.death_eater_used = False

    async def send_all_players(self, opcode, data):
        for id in list(self.playing_room):
            await self.send_player(id, opcode, data)

    async def send_all_players_waiting(self, opcode, data):
        for id in list(self.waiting_room):
            await self.send_player(id, opcode, data)

    async def send_all_players_dead(self, opcode, data):
        for id in list(self.death_room):
            await self.send_player(id, opcode, data)

    async def send_list_players(self, players, opcode, data):
        for id in players:
            await self.send_player(id, opcode, data)

    async def send_player(self, player_id, opcode, data):
        player = self.players.get(player_id)
        if not player:
            logger.warning(f"Envoi annulé pour '{opcode}' : joueur {player_id} introuvable.")
            return
            
        if not getattr(player, 'conn', None):
            logger.warning(f"Envoi annulé pour '{opcode}' : connexion du joueur {player_id} perdue.")
            return

        payload = {"opcode": opcode, "data": data}
        try:
            await player.conn.send(json.dumps(payload))
        except Exception as e:
            logger.error(f"Erreur réseau lors de l'envoi au joueur {player_id} : {e}", exc_info=True)

    async def wait_for_players_responses(self, players_list, opcode, timeout):
        responses = {}
        
        async def wait_for_one(pid):
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            
            if pid not in self.pending_responses:
                self.pending_responses[pid] = {}
            self.pending_responses[pid][opcode] = fut
            
            try:
                result = await asyncio.wait_for(fut, timeout=timeout)
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Le joueur {pid} n'a pas répondu à '{opcode}' dans le délai de {timeout}s.")
                return None
            finally:
                if pid in self.pending_responses:
                    self.pending_responses[pid].pop(opcode, None)
                    if not self.pending_responses[pid]:
                        self.pending_responses.pop(pid, None)

        active_players = [pid for pid in players_list if pid in self.players]
        
        tasks = {pid: asyncio.create_task(wait_for_one(pid)) for pid in active_players}
        
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for pid, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Exception lors de l'attente de réponse du joueur {pid} : {result}")
                    responses[pid] = None
                else:
                    responses[pid] = result
        
        valid_count = len([r for r in responses.values() if r is not None])
        logger.success(f"Collecte terminée pour '{opcode}' : {valid_count}/{len(active_players)} réponses reçues.")
        return responses
    
    def transfer_to_player_room(self):
        self.playing_room = self.waiting_room.copy()
        self.waiting_room = []

    def transfer_to_waiting_room(self):
        old_play = len(self.playing_room)
        old_dead = len(self.death_room)
        self.waiting_room = self.playing_room.copy() + self.waiting_room + self.death_room.copy()
        self.playing_room = []
        self.death_room = []
        logger.success(f"Salle d'attente restaurée : {old_play} vivants et {old_dead} morts replacés.")

    def transfer_to_death_room(self, player):
        if player in self.playing_room:
            self.playing_room = [p for p in self.playing_room if p != player]
            if player not in self.death_room:
                self.death_room.append(player)
        else:
            logger.warning(f"Impossible de transférer le joueur {player} dans la tombe : absent de la liste des vivants.")
    
    def transfer_to_living_room(self, player):
        if player in self.death_room:
            self.death_room = [p for p in self.death_room if p != player]
            if player not in self.playing_room:
                self.playing_room.append(player)
        else:
            logger.warning(f"Impossible de ressusciter le joueur {player} : absent de la tombe.")

    async def new_player(self, player_id):
        logger.info(f"Nouveau joueur connecté : {player_id}")
        players = []
        for id in list(self.waiting_room):
            if id in self.players:
                players.append({"id": id, "name": self.players[id].name})
            else:
                logger.warning(f"Incohérence : le joueur {id} est dans la salle d'attente mais sans données.")

        await self.send_all_players_waiting("waiting_room_list_update", {"players": players, "status": self.status})

    def get_roles(self):
            player_ids = [pid for pid in self.playing_room if pid in self.players]
            num_players = len(player_ids)

            if num_players < 1:
                logger.warning("Not enough players to assign roles")
                return {}, {}

            # --- Werewolves: 1 minimum, then +1 per 3 players ---
            num_werewolves = 1 + max(0, num_players - 3) // 3

            # Everyone starts as a villager
            assigned = {pid: "villager" for pid in player_ids}

            # Choose werewolves randomly
            werewolves = random.sample(player_ids, num_werewolves)
            for w in werewolves:
                assigned[w] = "werewolf"

            # --- Black wolf: 5% chance to evolve one werewolf ---
            if random.random() < 0.05:
                ww_list = [pid for pid, role in assigned.items() if role == "werewolf"]
                if ww_list:                     # always true because min 1 werewolf
                    black_wolf = random.choice(ww_list)
                    assigned[black_wolf] = "black_wolf"

            # --- Special roles with individual probabilities ---
            # Adjust the probabilities to your liking
            special_probabilities = {
                "fortune_teller": 0.5,
                "witch":          0.4,
                "pyromane":       0.3,
                "moon_fighter":   0.2,
                "mark_garyson":   0.15,
                "death_eater":    0.1
            }

            # Keep only those roles that are actually in self.roles
            possible_specials = [r for r in self.roles if r in special_probabilities]
            random.shuffle(possible_specials)   # avoid fixed order bias

            for role in possible_specials:
                if random.random() < special_probabilities[role]:
                    villagers = [pid for pid, r in assigned.items() if r == "villager"]
                    if villagers:
                        target = random.choice(villagers)
                        assigned[target] = role
                    # if no villager left, simply skip the role

            # --- Build the per_roles mapping ---
            per_roles = {}
            for pid, role in assigned.items():
                per_roles.setdefault(role, []).append(pid)

            logger.success(
                f"Rôles distribués : { {role: len(p) for role, p in per_roles.items()} }"
            )
            print(assigned)
            return assigned, per_roles

    def get_players_by_role(self, role, exclude_to_kill=False):
        players = []
        tracked_candidates = self.players_per_roles.get(role, [])
        
        for id in tracked_candidates:
            if id in self.players and id in self.playing_room:
                if getattr(self.players[id], 'role', None) == role:
                    if not exclude_to_kill or id not in self.to_kill:
                        players.append(id)
        
        return players

    def get_vote_result(self, responses):
        results = {}
        current = None
        current_count = 0

        for i in responses:
            if responses[i] is not None:
                vote_target = responses[i].get("vote")
                if vote_target is not None:
                    results[vote_target] = results.get(vote_target, 0) + 1

                    if results[vote_target] > current_count:
                        current = vote_target
                        current_count = results[vote_target]

        return current, current_count

    async def run_black_wolf(self, id):
        black_wolfs = self.get_players_by_role("black_wolf")

        if len(black_wolfs) < 1:
            return    
        
        if self.black_wolf_eaten:
            return

        await self.send_list_players(black_wolfs, "night_black_wolfs_start", {})

        if id in self.players:
            info = {"id": id, "name": self.players[id].name}
            await self.send_list_players(black_wolfs, "night_black_wolf_vote", {"villager": info})

            responses = await self.wait_for_players_responses(black_wolfs, "night_black_wolf_vote_response", 45)
            current, _ = self.get_vote_result(responses)
            await self.send_list_players(black_wolfs, "night_black_wolf_end", {})

            if current == id:
                try:
                    self.to_kill.remove(id)
                except ValueError:
                    logger.warning(f"Le joueur {id} n'était pas dans la liste des cibles à éliminer.")
                
                if id in self.players:
                    old_role = self.players[id].role
                    if old_role in self.players_per_roles:
                        try:
                            self.players_per_roles[old_role].remove(id)
                        except ValueError:
                            pass
                    
                    self.players[id].role = "werewolf"
                    if "werewolf" not in self.players_per_roles:
                        self.players_per_roles["werewolf"] = []
                    self.players_per_roles["werewolf"].append(id)
                    
                    logger.success(f"Le Loup Noir a transformé {self.players[id].name} en loup-garou.")
                    await self.send_player(id, "role_change", {"role": "werewolf"})
                    self.black_wolf_eaten = True
        

    async def run_fortune_teller(self):
        fortune_tellers = self.get_players_by_role("fortune_teller")

        if len(fortune_tellers) < 1:
            return

        await self.send_list_players(fortune_tellers, "night_fortune_teller_start", {})
        villagers = []

        for id in list(self.playing_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(3)
        await self.send_list_players(fortune_tellers, "night_fortune_teller_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(fortune_tellers, "night_fortune_teller_vote_response", 45)
        current, _ = self.get_vote_result(responses)

        if current is not None and current in self.players:
            role = getattr(self.players[current], 'role', "unknown")
            name = getattr(self.players[current], 'name', "???")
            logger.success(f"La Voyante a révélé le rôle de {name} : {role}.")
            await self.send_list_players(fortune_tellers, "night_fortune_teller_result", {"name": name, "role": role}) 

        await asyncio.sleep(5)
        await self.send_list_players(fortune_tellers, "night_fortune_teller_end", {})

    async def run_werewolf(self):
        villagers = []
        werewolfs = self.get_players_by_role("werewolf") + self.get_players_by_role("black_wolf")

        if len(werewolfs) < 1:
            return

        await self.send_list_players(werewolfs, "night_werewolf_start", {})

        for id in list(self.playing_room):
            if id in self.players and getattr(self.players[id], 'role', None) not in ("werewolf", "black_wolf"):
                villagers.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(3)
        await self.send_list_players(werewolfs, "night_werewolf_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(werewolfs, "night_werewolf_vote_response", 45)
        current, _ = self.get_vote_result(responses)
        await self.send_list_players(werewolfs, "night_werewolf_end", {})

        if current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.success(f"Les loups-garous ont choisi de dévorer {name}.")
            self.to_kill.append(current)
            await self.run_black_wolf(current)
        else:
            logger.warning("Les loups-garous n'ont pas réussi à se mettre d'accord sur une cible.")

    async def kill_players(self, players):
        killed = []
        unique_players = list(set(players))

        for id in unique_players:
            if id in self.players:
                if getattr(self.players[id], 'role', 'unknown') == "mark_garyson":
                    logger.warning(f"Mark Garyson ({self.players[id].name}) est sur le point de mourir, activation de sa vengeance.")
                    await self.run_mark_garyson()

                killed.append({"id": id, "name": self.players[id].name, "role": getattr(self.players[id], 'role', 'inconnu')})
                await self.send_player(id, "killed", {})
                self.transfer_to_death_room(id)
                logger.info(f"Joueur éliminé : {self.players[id].name} (rôle : {self.players[id].role})")
            else:
                logger.warning(f"Tentative d'élimination d'un joueur inexistant : {id}")

        if killed:
            await self.send_all_players("day_death", {"death": killed})

    async def run_mark_garyson(self):
        mark_garyson = self.get_players_by_role("mark_garyson", exclude_to_kill=False)

        if len(mark_garyson) < 1:
            return
        
        await self.send_all_players("mark_garyon_died", {})
        villagers = []
        for id in list(self.playing_room):
            if id in self.players and id not in self.to_kill:
                villagers.append({"id": id, "name": self.players[id].name})

        await self.send_list_players(mark_garyson, "mark_garyon_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(mark_garyson, "mark_garyon_response", 45)
        current, _ = self.get_vote_result(responses)
        if current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.success(f"Mark Garyson a emporté {name} dans sa tombe.")
            await self.kill_players([current])

    async def run_pyromane(self):
        pyromanes = self.get_players_by_role("pyromane")

        if len(pyromanes) < 1:
            return    

        await self.send_list_players(pyromanes, "night_pyromane_start", {})
        villagers = []
        for id in list(self.playing_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(3)
        await self.send_list_players(pyromanes, "night_pyromane_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(pyromanes, "night_pyromane_response", 45)
        current, _ = self.get_vote_result(responses)

        if current == -1:
            logger.warning(f"Le Pyromane déclenche ses explosifs ! Cibles : {self.pyromane_bombed}")
            await self.send_all_players("pyromane_explosion", {})
            self.to_kill.extend(self.pyromane_bombed)
            self.to_kill = list(set(self.to_kill))
            self.pyromane_bombed = []
            await asyncio.sleep(3)
        elif current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.success(f"Le Pyromane a placé une bombe sur {name}.")
            self.pyromane_bombed.append(current)

        await self.send_list_players(pyromanes, "night_pyromane_end", {})

    async def moon_fighter(self):
        moon_fighters = self.get_players_by_role("moon_fighter")

        if len(moon_fighters) < 1 or self.moon_fighter_skiped:
            await asyncio.sleep(1)
            return 0
        
        await self.send_list_players(moon_fighters, "night_moon_fighter_vote", {})
        responses = await self.wait_for_players_responses(moon_fighters, "night_moon_fighter_response", 5)

        current, _ = self.get_vote_result(responses)
        if current == 1:
            logger.success("Le Moon Fighter a interrompu la phase en cours.")
            self.moon_fighter_skiped = True
        return current

    async def run_night(self):
        self.phase_name = "night"
        self.phase_start_time = time.time()
        self.phase_duration = 55
        logger.success(f"------------------ Nuit {self.current_day} ------------------")
        self.to_kill = []
        await self.send_all_players("switch_night", {"current_night": self.current_day})
        await asyncio.sleep(10)
        skip = await self.moon_fighter()
        if skip: return
        await self.run_fortune_teller()
        await self.send_all_players("back_to_sleep",{})
        
        skip = await self.moon_fighter()
        if skip: return
        await self.run_werewolf()
        await self.send_all_players("back_to_sleep",{})

        skip = await self.moon_fighter()
        if skip: return
        await self.run_witch()
        await self.send_all_players("back_to_sleep",{})
        
        skip = await self.moon_fighter()
        if skip: return
        await self.run_pyromane()
        await self.send_all_players("back_to_sleep",{})
        
        skip = await self.moon_fighter()
        if skip: return
        await self.run_death_eater()
        await self.send_all_players("back_to_sleep",{})

        await asyncio.sleep(5)

    async def run_day(self):
        self.phase_name = "day"
        self.phase_start_time = time.time()
        self.phase_duration = 65 
        self.current_day += 1
        logger.success(f"------------------ Jour {self.current_day} ------------------")
        await self.send_all_players("switch_day", {"current_day": self.current_day})
        await asyncio.sleep(7)
        if self.to_kill:
            await self.kill_players(self.to_kill)
            self.to_kill = []

        await self.check_win()
        if self.finished:
            return

        await asyncio.sleep(10)

        villagers = []
        for id in list(self.playing_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})

        await self.send_all_players("day_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(list(self.playing_room), "day_vote_response", 45)
        current, vote_count = self.get_vote_result(responses)
        if current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.info(f"Vote du jour : {name} éliminé avec {vote_count} votes.")
            await self.kill_players([current])
            
        await self.crazy_dave_vote()
        await asyncio.sleep(5)

    async def check_win(self):
        werewolfs = self.get_players_by_role("werewolf", exclude_to_kill=False) + self.get_players_by_role("black_wolf", exclude_to_kill=False)
        
        if len(werewolfs) < 1:
            logger.success("Victoire des villageois !")
            await self.send_all_players("game_end", {"winner": "villager"})
            self.finished = True
            return

        villagers = [pid for pid in self.playing_room if pid in self.players and self.players[pid].role not in ("werewolf", "black_wolf")]
        
        if len(villagers) < 1:
            logger.success("Victoire des loups-garous !")
            await self.send_all_players("game_end", {"winner": "werewolf"})
            self.finished = True

    async def run_witch(self):
        witches = self.get_players_by_role("witch")

        if len(witches) < 1:
            return

        await self.send_list_players(witches, "night_witch_start", {})
        await asyncio.sleep(3)

        victim = None
        name = None
        if len(self.to_kill) > 0:
            victim = random.choice(self.to_kill)
            name = getattr(self.players[victim], "name", None)

        await self.send_list_players(witches, "night_witches_vote", {"id": victim, "name": name, "save": self.witch_save_used, "genocide": self.witch_genocide_used})

        responses = await self.wait_for_players_responses(witches, "night_witches_vote_response", 45)
        current, _ = self.get_vote_result(responses)

        if current == 1 and not self.witch_save_used:
            if victim:
                self.to_kill.remove(victim)
                logger.success(f"La Sorcière a sauvé {name} de la mort.")
            self.witch_save_used = True

        if current == 2 and not self.witch_genocide_used:
            await self.run_witch_genocide()

        await asyncio.sleep(3)
        await self.send_list_players(witches, "night_witch_end", {})

    async def run_death_eater(self):
        death_eaters = self.get_players_by_role("death_eater")

        if len(death_eaters) < 1 or self.death_eater_used:
            return

        await self.send_list_players(death_eaters, "night_death_eater_start", {})
        villagers = []
        for id in list(self.death_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})
  
        await self.send_list_players(death_eaters, "night_death_eater_vote", {"deads": villagers})

        responses = await self.wait_for_players_responses(death_eaters, "night_death_eater_vote_response", 45)
        current, _ = self.get_vote_result(responses)  

        if current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.success(f"Le Croque-mort a ressuscité {name}.")
            self.transfer_to_living_room(current)
            await self.send_player(current, "alive", {})

        self.death_eater_used = True

    async def run_witch_genocide(self):
        witches = self.get_players_by_role("witch")

        if len(witches) < 1:
            return

        await self.send_list_players(witches, "night_witch_genocide_start", {})
        villagers = []
        for id in list(self.playing_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})
  
        await self.send_list_players(witches, "night_witch_genocide_vote", {"villagers": villagers})
        responses = await self.wait_for_players_responses(witches, "night_witch_genocide_vote_response", 45)
        current, _ = self.get_vote_result(responses)  

        if current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.success(f"La Sorcière a empoisonné {name}.")
            self.to_kill.append(current)   

        self.witch_genocide_used = True

    async def crazy_dave_does(self):
        logger.warning("Crazy Dave active une perturbation temporelle.")
        await self.send_all_players("crazy_dave_up", {})
        await asyncio.sleep(5)
        
        await self.send_all_players("switch_night", {"current_day": self.current_day})
        self.current_day += 1
        await asyncio.sleep(3)
        
        await self.send_all_players("switch_day", {"current_day": self.current_day})
        await asyncio.sleep(3)
        
        await self.send_all_players("switch_night", {"current_day": self.current_day})
        await asyncio.sleep(3)

        crazy_dave = self.get_players_by_role("crazy_dave", exclude_to_kill=False)
        if len(crazy_dave) < 1:
            logger.error("Crazy Dave a disparu pendant sa perturbation.")
            await asyncio.sleep(5)
            return

        await self.send_list_players(crazy_dave, "crazy_dave_does_vote", {})
        responses = await self.wait_for_players_responses(crazy_dave, "crazy_dave_does_response", 45)
        current, _ = self.get_vote_result(responses)
        
        if current is not None:
            name = self.players[current].name if current in self.players else "inconnu"
            logger.success(f"Crazy Dave a éliminé {name} dans sa folie temporelle.")
            await self.kill_players([current])

    async def crazy_dave_vote(self):
        crazy_dave = self.get_players_by_role("crazy_dave", exclude_to_kill=False)

        if len(crazy_dave) < 1 or self.crazy_dave_up:
            await asyncio.sleep(1)
            return

        await self.send_list_players(crazy_dave, "crazy_dave_vote", {})
        responses = await self.wait_for_players_responses(crazy_dave, "crazy_dave_response", 15)
        current, _ = self.get_vote_result(responses)
        
        if current == 1:
            logger.success("Crazy Dave active son pouvoir.")
            self.crazy_dave_up = True
            await self.crazy_dave_does()

    async def run_game(self):
        self.status = 0
        self.finished = False

        logger.success("==========================================================================")
        logger.success("                     DÉBUT DE LA PARTIE PRINCIPALE                        ")
        logger.success("==========================================================================")
        logger.info(f"En attente de {self.min_player_count} joueur(s)...")

        while len(self.players) < self.min_player_count:
            await asyncio.sleep(0.1)

        logger.success(f"Nombre de joueurs atteint ({len(self.players)}). Démarrage imminent.")
        await self.send_all_players_waiting("game_start_soon", {})
        self.status = 1

        await asyncio.sleep(10)

        self.transfer_to_player_room()
        self.current_day = 0
        
        self.current_roles, self.players_per_roles = self.get_roles()
        self.set_game_flags()
        self.to_kill = []

        for i in list(self.playing_room):
            if i in self.players:
                if i in self.players:
                    self.players[i].role = self.current_roles[i]
                    await self.send_player(i, "player_role", {"role": self.current_roles[i]})
            else:
                logger.warning(f"Le joueur {i} a disparu avant la distribution des rôles.")

        await asyncio.sleep(15)

        while not self.finished:
            if not self.finished:
                await self.run_night()
                await self.check_win()

            if not self.finished:
                await self.run_day()
                await self.check_win()   

        logger.success("Partie terminée. Nettoyage en cours.")
        await self.send_all_players("back_to_waiting", {})
        await self.send_all_players_dead("back_to_waiting", {})

        self.transfer_to_waiting_room()
        players = []
        for id in list(self.waiting_room):
            if id in self.players:
                players.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(7)
        
        self.status = 0
        await self.send_all_players_waiting("waiting_room_list_update", {"players": players, "status": self.status})
        
        self.phase_name = "waiting"
        self.phase_start_time = None
        self.phase_duration = 0
        logger.success("================== FIN DE LA PARTIE ==================")