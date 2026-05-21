from modules.logger import Logger
import random
import json
import asyncio
import time

logger = Logger("Game")

class Game:

    def __init__(self):
        logger.info("Initializing a new Werewolf Game instance.")
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
        logger.debug(f"Game core initialized. Target min players: {self.min_player_count}. Registered roles: {self.roles}")

    def set_game_flags(self):
        logger.info("Resetting/Configuring tactical game modification flags.")
        self.black_wolf_eaten = False
        self.moon_fighter_skiped = False
        self.pyromane_bombed = []
        self.crazy_dave_up = False
        self.witch_save_used = False
        self.witch_genocide_used = False
        self.death_eater_used = False
        logger.debug("All game state modifiers normalized to false/empty values.")

    async def send_all_players(self, opcode, data):
        logger.info(f"Broadcasting network payload '{opcode}' to all active players in the playing room.")
        current_room_snapshots = list(self.playing_room)
        logger.debug(f"Broadcasting targets ({len(current_room_snapshots)}): {current_room_snapshots}")
        for id in current_room_snapshots:
            await self.send_player(id, opcode, data)

    async def send_all_players_waiting(self, opcode, data):
        logger.info(f"Broadcasting network payload '{opcode}' to waiting room clients.")
        current_waiting_snapshots = list(self.waiting_room)
        logger.debug(f"Waiting targets ({len(current_waiting_snapshots)}): {current_waiting_snapshots}")
        for id in current_waiting_snapshots:
            await self.send_player(id, opcode, data)

    async def send_all_players_dead(self, opcode, data):
        logger.info(f"Broadcasting network payload '{opcode}' to the graveyard (death room).")
        current_dead_snapshots = list(self.death_room)
        logger.debug(f"Graveyard targets ({len(current_dead_snapshots)}): {current_dead_snapshots}")
        for id in current_dead_snapshots:
            await self.send_player(id, opcode, data)

    async def send_list_players(self, players, opcode, data):
        logger.info(f"Sending selective opcode '{opcode}' to explicit group of {len(players)} target ids.")
        for id in players:
            await self.send_player(id, opcode, data)

    async def send_player(self, player_id, opcode, data):
        player = self.players.get(player_id)
        if not player:
            logger.warning(f"Aborted sending opcode '{opcode}': Player structure for ID {player_id} is missing from active tracking map.")
            return
            
        if not getattr(player, 'conn', None):
            logger.warning(f"Aborted sending opcode '{opcode}': Player connection object for ID {player_id} is empty/dead.")
            return

        payload = {"opcode": opcode, "data": data}
        logger.debug(f"Dispatching WebSockets frame -> Player: {player_id} ({getattr(player, 'name', 'Unknown')}) | Payload: {payload}")
        try:
            await player.conn.send(json.dumps(payload))
        except Exception as e:
            logger.error(f"Network transport level collision sending data to client {player_id}: {e}", exc_info=True)

    async def wait_for_players_responses(self, players_list, opcode, timeout):
        responses = {}
        logger.info(f"Asynchronous response window opened for '{opcode}'. Listening to {len(players_list)} targets. Hard cutoff timeout: {timeout}s.")
        
        async def wait_for_one(pid):
            loop = asyncio.get_running_loop()
            fut = loop.create_future()
            
            if pid not in self.pending_responses:
                self.pending_responses[pid] = {}
            self.pending_responses[pid][opcode] = fut
            
            logger.debug(f"Hooked unique Future tracker for client {pid} on transaction query string '{opcode}'")
            try:
                result = await asyncio.wait_for(fut, timeout=timeout)
                logger.debug(f"Received valid runtime response payload back from client {pid} for request context '{opcode}': {result}")
                return result
            except asyncio.TimeoutError:
                logger.warning(f"Network processing constraint reached! Client {pid} did not respond to '{opcode}' within {timeout}s.")
                return None
            finally:
                if pid in self.pending_responses:
                    self.pending_responses[pid].pop(opcode, None)
                    if not self.pending_responses[pid]:
                        self.pending_responses.pop(pid, None)

        active_players = [pid for pid in players_list if pid in self.players]
        logger.debug(f"Filtered verification task loop down to real living nodes: {active_players}")
        
        tasks = {pid: asyncio.create_task(wait_for_one(pid)) for pid in active_players}
        
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            for pid, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Exception bubble intercepted on concurrent wait loop execution for player {pid}: {result}")
                    responses[pid] = None
                else:
                    responses[pid] = result
        
        valid_count = len([r for r in responses.values() if r is not None])
        logger.success(f"Response polling window closed for '{opcode}'. Collected {valid_count}/{len(active_players)} inputs.")
        return responses
    
    def transfer_to_player_room(self):
        logger.info(f"Transitioning room state configurations. Reallocating {len(self.waiting_room)} clients into processing arena.")
        self.playing_room = self.waiting_room.copy()
        self.waiting_room = []
        logger.debug(f"Migration completed. Sandbox players size: {len(self.playing_room)} | Buffer size: {len(self.waiting_room)}")

    def transfer_to_waiting_room(self):
        logger.info("De-escalating active sandbox structures. Pooling all players back into the staging waiting lobby.")
        old_play = len(self.playing_room)
        old_dead = len(self.death_room)
        self.waiting_room = self.playing_room.copy() + self.waiting_room + self.death_room.copy()
        self.playing_room = []
        self.death_room = []
        logger.success(f"Ecosystem reset applied. Merged {old_play} live and {old_dead} dead actors back into waiting pool.")

    def transfer_to_death_room(self, player):
        logger.info(f"Running entity execution mapping logic for entity ID: {player}")
        if player in self.playing_room:
            self.playing_room = [p for p in self.playing_room if p != player]
            if player not in self.death_room:
                self.death_room.append(player)
            logger.success(f"Entity identity validation: Player {player} moved successfully from living registry to graveyard array.")
        else:
            logger.warning(f"Anomalous lifecycle call intercepted! Attempted to move Player {player} to dead stack, but they are absent from living arrays.")
    
    def transfer_to_living_room(self, player):
        logger.info(f"Running resurrection/revival engine rules for entity ID: {player}")
        if player in self.death_room:
            self.death_room = [p for p in self.death_room if p != player]
            if player not in self.playing_room:
                self.playing_room.append(player)
            logger.success(f"Resurrection confirmed. Player {player} restored to active operational lists.")
        else:
            logger.warning(f"Anomalous lifecycle call intercepted! Attempted to extract Player {player} from graveyard, but tracking map says they are not dead.")

    async def new_player(self, player_id):
        logger.info(f"New runtime network connection mapping hooked for player_id: {player_id}")
        players = []
        for id in list(self.waiting_room):
            if id in self.players:
                players.append({"id": id, "name": self.players[id].name})
            else:
                logger.warning(f"Data mapping discrepancy checked. Player reference code {id} exists in waiting arrays but metadata model is unmapped.")

        logger.debug(f"Broadcasting current updated staging roster back to waiting lobby clients: {players}")
        await self.send_all_players_waiting("waiting_room_list_update", {"players": players, "status": self.status})

    def get_roles(self):
        logger.info("Executing procedural system role distributions using dynamic balancing algorithms.")
        player_ids = [pid for pid in self.playing_room if pid in self.players]
        num_players = len(player_ids)
        logger.debug(f"Calculating role footprints against {num_players} active game participants.")
        
        num_werewolves = max(1, num_players // 4)
        if num_players >= 6 and num_werewolves < 2:
            num_werewolves = 2
        logger.debug(f"Calculated base safe antagonist headcount matrix requirement: {num_werewolves}")
            
        special_roles = [role for role in self.roles if role not in ("villager", "werewolf")]
        max_specials = num_players - num_werewolves
        if max_specials < 0:
            max_specials = 0
            
        selected_specials = random.sample(special_roles, min(len(special_roles), max_specials))
        logger.debug(f"Selected special capability sub-matrix roles for distribution match: {selected_specials}")
        
        pool = (["werewolf"] * num_werewolves) + selected_specials + (["villager"] * (num_players - num_werewolves - len(selected_specials)))
        logger.debug(f"Unshuffled generation state role array pool built: {pool}")
        random.shuffle(pool)
        
        result = {}
        per_roles = {}

        for i, player_id in enumerate(player_ids):
            #assigned_role = pool[i]
            assigned_role = "witch"
            result[player_id] = assigned_role

            if assigned_role not in per_roles:
                per_roles[assigned_role] = []
            per_roles[assigned_role].append(player_id)

        logger.success(f"Final safe distribution complete. Summary: { {role: len(p) for role, p in per_roles.items()} }")
        return result, per_roles

    def get_players_by_role(self, role, exclude_to_kill=False):
        players = []
        tracked_candidates = self.players_per_roles.get(role, [])
        logger.debug(f"Scanning profile lists for type mapping matching role: '{role}' (Excluding scheduled executions: {exclude_to_kill})")
        
        for id in tracked_candidates:
            if id in self.players and id in self.playing_room:
                if getattr(self.players[id], 'role', None) == role:
                    if not exclude_to_kill or id not in self.to_kill:
                        players.append(id)
        
        logger.debug(f"Role query returned matching tracking array keys: {players}")
        return players

    def get_vote_result(self, responses):
        logger.info("Processing compilation and tally parsing routines for incoming vote responses.")
        results = {}
        current = None
        current_count = 0

        for i in responses:
            if responses[i] is not None:
                vote_target = responses[i].get("vote")
                if vote_target is not None:
                    print(vote_target)
                    results[vote_target] = results.get(vote_target, 0) + 1
                    logger.debug(f"Tally process tracking -> Player {i} registered target vote choice against ID {vote_target}")

                    if results[vote_target] > current_count:
                        current = vote_target
                        current_count = results[vote_target]

        logger.success(f"Vote algorithm finished compiling. Grid results: {results}. Resolution target selected: {current} with weight: {current_count}")
        return current, current_count

    async def run_black_wolf(self, id):
        logger.info(f"Evaluating conditional phase triggers for character archetype Black Wolf against target context ID: {id}")
        black_wolfs = self.get_players_by_role("black_wolf")

        if len(black_wolfs) < 1:
            logger.debug("No tracking models for role context Black Wolf found alive. Moving system frame forward.")
            return    
        
        if self.black_wolf_eaten:
            logger.info("Black Wolf active skill execution limit reached for this session profile (Already consumed).")
            return

        logger.info("Broadcasting selection sequence to Black Wolf role group matrix instances.")
        await self.send_list_players(black_wolfs, "night_black_wolfs_start", {})

        if id in self.players:
            info = {"id": id, "name": self.players[id].name}
            await self.send_list_players(black_wolfs, "night_black_wolf_vote", {"villager": info})

            responses = await self.wait_for_players_responses(black_wolfs, "night_black_wolf_vote_response", 45)
            current, _ = self.get_vote_result(responses)
            await self.send_list_players(black_wolfs, "night_black_wolf_end", {})

            if current == id:
                logger.success(f"Skill validation passed! Black Wolf converts target identity {id} instead of execution.")
                try:
                    self.to_kill.remove(id)
                    logger.debug(f"Extracted identity {id} safely out of standard execution tracking array.")
                except ValueError:
                    logger.warning(f"Attempted extraction of {id} from execution array failed: element not tracked.")
                
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
                    
                    logger.info(f"Dispatched asynchronous role restructuring frames to target {id}.")
                    await self.send_player(id, "role_change", {"role": "werewolf"})
                    self.black_wolf_eaten = True

    async def run_fortune_teller(self):
        logger.info("Starting Fortune Teller logic loop configuration thread.")
        fortune_tellers = self.get_players_by_role("fortune_teller")

        if len(fortune_tellers) < 1:
            logger.warning("No operational Fortune Teller instances discovered. Canceling step pipeline.")
            return

        await self.send_list_players(fortune_tellers, "night_fortune_teller_start", {})
        villagers = []

        for id in list(self.playing_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(3)
        logger.debug(f"Presenting projection map option arrays to active seers: {villagers}")
        await self.send_list_players(fortune_tellers, "night_fortune_teller_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(fortune_tellers, "night_fortune_teller_vote_response", 45)
        current, _ = self.get_vote_result(responses)

        if current is not None and current in self.players:
            role = getattr(self.players[current], 'role', "unknown")
            name = getattr(self.players[current], 'name', "???")
            logger.success(f"Fortune Teller target resolution complete. Target ID: {current} | Identity revealed: {role}")
            await self.send_list_players(fortune_tellers, "night_fortune_teller_result", {"name": name, "role": role}) 

        await asyncio.sleep(5)
        await self.send_list_players(fortune_tellers, "night_fortune_teller_end", {})

    async def run_werewolf(self):
        logger.info("Beginning execution context for antagonist group: Werewolf.")
        villagers = []
        werewolfs = self.get_players_by_role("werewolf") + self.get_players_by_role("black_wolf")

        if len(werewolfs) < 1:
            logger.warning("Critical baseline: No active items discovered in antagonist packs. Advancing sequence.")
            return

        logger.debug(f"Active pack entities tracking references: {werewolfs}")
        await self.send_list_players(werewolfs, "night_werewolf_start", {})

        for id in list(self.playing_room):
            if id in self.players and getattr(self.players[id], 'role', None) not in ("werewolf", "black_wolf"):
                villagers.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(3)
        logger.debug(f"Delivering target array grid vectors down to pack network frames: {villagers}")
        await self.send_list_players(werewolfs, "night_werewolf_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(werewolfs, "night_werewolf_vote_response", 45)
        current, _ = self.get_vote_result(responses)
        await self.send_list_players(werewolfs, "night_werewolf_end", {})

        if current is not None:
            logger.success(f"Consensus achieved by antagonist collective matrix. target execution profile target: {current}")
            self.to_kill.append(current)
            await self.run_black_wolf(current)
        else:
            logger.warning("Antagonist packet failed to arrive at an execution target decision agreement.")

    async def kill_players(self, players):
        killed = []
        unique_players = list(set(players))
        logger.info(f"Invoking core execution engine cycle for batch processing target list: {unique_players}")

        for id in unique_players:
            if id in self.players:
                if getattr(self.players[id], 'role', 'unknown') == "mark_garyson":
                    logger.warning(f"Critical Event Intersection! Mark Garyson role detected on dying target entity {id}. intercepting execution sequence to evaluate passives.")
                    await self.run_mark_garyson()

                logger.info(f"Applying terminal lifecycle transformation state directly onto player: {id} ({self.players[id].name}).")
                killed.append({"id": id, "name": self.players[id].name, "role": getattr(self.players[id], 'role', 'unknown')})
                await self.send_player(id, "killed", {})
                self.transfer_to_death_room(id)
            else:
                logger.warning(f"Processing error during death sequence execution: Target code identity {id} is no longer mapped inside active game profile maps.")

        if killed:
            logger.success(f"Batch execution complete. Broadcasting structural death events list down to room context clients: {killed}")
            await self.send_all_players("day_death", {"death": killed})

    async def run_mark_garyson(self):
        logger.info("Executing capability trace loop rules for role module: Mark Garyson")
        mark_garyson = self.get_players_by_role("mark_garyson", exclude_to_kill=False)

        if len(mark_garyson) < 1:
            logger.error("Skill logic error processing entity profile: Mark Garyson object structure is dead/absent.")
            return
        
        await self.send_all_players("mark_garyon_died", {})
        villagers = []
        for id in list(self.playing_room):
            if id in self.players and id not in self.to_kill:
                villagers.append({"id": id, "name": self.players[id].name})

        logger.debug(f"Offering direct instant-revenge choice vectors to entity: {villagers}")
        await self.send_list_players(mark_garyson, "mark_garyon_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(mark_garyson, "mark_garyon_response", 45)
        current, _ = self.get_vote_result(responses)
        if current is not None:
            logger.success(f"Passive execution confirmed. Mark Garyson choice dragged target entity down to death array: {current}")
            await self.kill_players([current])

    async def run_pyromane(self):
        logger.info("Beginning sequence logic tracing for character class tracking system: Pyromane.")
        pyromanes = self.get_players_by_role("pyromane")

        if len(pyromanes) < 1:
            logger.debug("No live characters detected matching Pyromane criteria flags. Skipping processing window.")
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
            logger.warning(f"Detonation signal confirmation captured (-1). Detonating all loaded targets tracking lists: {self.pyromane_bombed}")
            await self.send_all_players("pyromane_explosion", {})
            self.to_kill.extend(self.pyromane_bombed)
            self.to_kill = list(set(self.to_kill))
            self.pyromane_bombed = []
            await asyncio.sleep(3)
        elif current is not None:
            logger.success(f"Pyromane targeted fuel load marker confirmed added onto entity id target: {current}")
            self.pyromane_bombed.append(current)

        await self.send_list_players(pyromanes, "night_pyromane_end", {})

    async def moon_fighter(self):
        logger.info("Polling passive context validation vectors for class profile: Moon Fighter.")
        moon_fighters = self.get_players_by_role("moon_fighter")

        if len(moon_fighters) < 1 or self.moon_fighter_skiped:
            logger.debug("Moon Fighter skip activation preconditions met (Absent or previously spent tracking flags).")
            await asyncio.sleep(1)
            return 0
        
        await self.send_list_players(moon_fighters, "night_moon_fighter_vote", {})
        responses = await self.wait_for_players_responses(moon_fighters, "night_moon_fighter_response", 5)

        current, _ = self.get_vote_result(responses)
        if current == 1:
            logger.warning("Intercept verification true! Moon Fighter chose to disrupt and skip the current sub-phase sequence block.")
            self.moon_fighter_skiped = True
        return current

    async def run_night(self):
        self.phase_name = "night"
        self.phase_start_time = time.time()
        self.phase_duration = 55
        logger.success(f"------------------ Night {self.current_day} Starting ------------------")
        self.to_kill = []
        await self.send_all_players("switch_night", {"current_night": self.current_day})
        await asyncio.sleep(10)
        skip = await self.moon_fighter()
        if skip: logger.info("Night logic intercept phase verified. Halting step stack execution."); return
        await self.run_fortune_teller()
        
        skip = await self.moon_fighter()
        if skip: logger.info("Night logic intercept phase verified. Halting step stack execution."); return
        await self.run_werewolf()

        skip = await self.moon_fighter()
        if skip: logger.info("Night logic intercept phase verified. Halting step stack execution."); return
        await self.run_witch()
        
        skip = await self.moon_fighter()
        if skip: logger.info("Night logic intercept phase verified. Halting step stack execution."); return
        await self.run_pyromane()
        
        skip = await self.moon_fighter()
        if skip: logger.info("Night logic intercept phase verified. Halting step stack execution."); return
        await self.run_death_eater()

    async def run_day(self):
        self.phase_name = "day"
        self.phase_start_time = time.time()
        self.phase_duration = 65 
        self.current_day += 1
        logger.success(f"------------------ Day {self.current_day} Starting ------------------")
        await self.send_all_players("switch_day", {"current_day": self.current_day})

        if self.to_kill:
            logger.info(f"Evaluating night cycle resolution data. Target list scheduled for destruction: {self.to_kill}")
            await self.kill_players(self.to_kill)
            self.to_kill = []

        await self.check_win()
        if self.finished:
            return

        logger.debug("Entering standard daylight observation block pause (10s).")
        await asyncio.sleep(10)

        villagers = []
        for id in list(self.playing_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})

        logger.info("Opening active public day tribunal system mechanics.")
        await self.send_all_players("day_vote", {"villagers": villagers})

        responses = await self.wait_for_players_responses(list(self.playing_room), "day_vote_response", 45)
        current, vote_count = self.get_vote_result(responses)
        logger.info(f"Day tribunal processing matrix resolved. Selection Target: {current} with consolidated vote profile weight: {vote_count}")
        
        await asyncio.sleep(5)
        if current is not None:
            logger.info(f"Executing tribunal outcome for user selection reference: {current}")
            await self.kill_players([current])
            
        logger.debug(f"Current cycle status metrics -> Active Living Headcount: {self.playing_room} | Graveyard Headcount size: {self.death_room}")
        await self.crazy_dave_vote()
        await asyncio.sleep(5)

    async def check_win(self):
 
 
        logger.info("Executing win-condition evaluation matrix scans against active live rooms layers.")
        werewolfs = self.get_players_by_role("werewolf", exclude_to_kill=False) + self.get_players_by_role("black_wolf", exclude_to_kill=False)
        logger.debug(f"Win check parsing -> Live matching antagonists pack size remaining: {len(werewolfs)}")
        
        if len(werewolfs) < 1:
            logger.success("End of game state reached: All antagonists wiped out! Triggering Villager team victory sequence.")
            await self.send_all_players("game_end", {"winner": "villager"})
            self.finished = True
            return

        villagers = [pid for pid in self.playing_room if pid in self.players and self.players[pid].role not in ("werewolf", "black_wolf")]
        logger.debug(f"Win check parsing -> Live matching non-werewolf alignment size remaining: {len(villagers)}")
        
        if len(villagers) < 1:
            logger.success("End of game state reached: All human faction entities destroyed! Triggering Werewolf team victory sequence.")
            await self.send_all_players("game_end", {"winner": "werewolf"})
            self.finished = True

    async def run_witch(self):
        logger.info("Configuring functional execution loops for tracking class: Witch.")
        witches = self.get_players_by_role("witch")

        if len(witches) < 1:
            logger.debug("No valid matching live profiles for Witch discovered. Skipping step sequence context.")
            return

        await self.send_list_players(witches, "night_witch_start", {})
        await asyncio.sleep(3)

        victim = None
        name = None
        if len(self.to_kill) > 0:
            victim = random.choice(self.to_kill)
            name = getattr(self.players[victim], "name", None)
            logger.debug(f"Witch target preview chosen from raw execution heap tracker: Entity {victim} ({name})")

        logger.info("Delivering options map variables to individual Witch socket instances.")
        await self.send_list_players(witches, "night_witches_vote", {"id": victim, "name": name, "save": self.witch_save_used, "genocide": self.witch_genocide_used})

        responses = await self.wait_for_players_responses(witches, "night_witches_vote_response", 45)
        current, _ = self.get_vote_result(responses)

        if current == 1 and not self.witch_save_used:
            logger.success(f"Witch used life potion. Rescuing and protecting scheduled target reference: {victim}")
            if victim in self.to_kill:
                self.to_kill.remove(victim)
            self.witch_save_used = True

        if current == 2 and not self.witch_genocide_used:
            logger.warning("Witch activated single target damage execution (Genocide choice triggered).")
            await self.run_witch_genocide()

        await asyncio.sleep(3)
        await self.send_list_players(witches, "night_witch_end", {})

    async def run_death_eater(self):
        logger.info("Configuring functional loop execution profiles for subclass item: Death Eater.")
        death_eaters = self.get_players_by_role("death_eater")

        if len(death_eaters) < 1 or self.death_eater_used:
            logger.debug("Preconditions for Death Eater execution not met (No entity found or ability spent).")
            return

        await self.send_list_players(death_eaters, "night_death_eater_start", {})
        villagers = []
        for id in list(self.death_room):
            if id in self.players:
                villagers.append({"id": id, "name": self.players[id].name})
  
        logger.debug(f"Presenting dead player target options down to active Death Eaters: {villagers}")
        await self.send_list_players(death_eaters, "night_death_eater_vote", {"deads": villagers})

        responses = await self.wait_for_players_responses(death_eaters, "night_death_eater_vote_response", 45)
        current, _ = self.get_vote_result(responses)  

        if current is not None:
            logger.success(f"Death Eater resurrect contract successfully resolved. Pulling client back to life pool arrays: {current}")
            self.transfer_to_living_room(current)
            await self.send_player(current, "alive", {})

        self.death_eater_used = True

    async def run_witch_genocide(self):
        logger.info("Executing precise targeted instant damage logic sequence context: Witch Genocide Subroutine.")
        witches = self.get_players_by_role("witch")

        if len(witches) < 1:
            logger.warning("Subroutine validation mismatch error: Subroutine reached without an active Witch asset.")
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
            logger.success(f"Witch target damage spell execution marker registered onto client ID target: {current}")
            self.to_kill.append(current)   

        self.witch_genocide_used = True

    async def crazy_dave_does(self):
        logger.warning("CRAZY DAVE TIME DISTORTION SKILL DEPLOYED. Simulating rapid temporal environment shifts.")
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
            logger.error("Anomalous error executing distortion step: Crazy Dave disappeared/died during performance loop.")
            await asyncio.sleep(5)
            return

        await self.send_list_players(crazy_dave, "crazy_dave_does_vote", {})
        responses = await self.wait_for_players_responses(crazy_dave, "crazy_dave_does_response", 45)
        current, _ = self.get_vote_result(responses)
        
        if current is not None:
            logger.success(f"Crazy Dave tracking execution consequence deployed against targeted target: {current}")
            await self.kill_players([current])

    async def crazy_dave_vote(self):
        logger.info("Checking availability flags for capability window activation: Crazy Dave.")
        crazy_dave = self.get_players_by_role("crazy_dave", exclude_to_kill=False)

        if len(crazy_dave) < 1 or self.crazy_dave_up:
            logger.debug("Preconditions for Crazy Dave system query not valid (Role absent or skill already flagged).")
            await asyncio.sleep(1)
            return

        await self.send_list_players(crazy_dave, "crazy_dave_vote", {})
        responses = await self.wait_for_players_responses(crazy_dave, "crazy_dave_response", 15)
        current, _ = self.get_vote_result(responses)
        
        if current == 1:
            logger.success("Crazy Dave user input confirmed trigger request! Spawning sub-phase engine threads.")
            self.crazy_dave_up = True
            await self.crazy_dave_does()

    async def run_game(self):
        self.status = 0
        self.finished = False

        logger.success("==========================================================================")
        logger.success("                     CORE GAME MAIN LOOP STARTED                          ")
        logger.success("==========================================================================")
        logger.info(f"Awaiting player count checkpoint minimum validation bounds ({self.min_player_count} clients)...")

        while len(self.players) < self.min_player_count:
            await asyncio.sleep(0.1)

        logger.success(f"Operational system parameter verification true! Player limit verified: {len(self.players)} active models.")
        await self.send_all_players_waiting("game_start_soon", {})
        self.status = 1

        logger.info("Pausing operations for standard match initiation interval delays (10s).")
        await asyncio.sleep(10)

        self.transfer_to_player_room()
        self.current_day = 0
        
        # Balance and map role parameters
        self.current_roles, self.players_per_roles = self.get_roles()
        self.set_game_flags()
        self.to_kill = []

        logger.info("Injecting assigned profile data down to individual active tracking instances.")
        for i in list(self.playing_room):
            if i in self.players:
                self.players[i].role = self.current_roles[i]
                logger.debug(f"Assigned Profile Identity Key mapping: User ID {i} -> Role Model: {self.current_roles[i]}")
                await self.send_player(i, "player_role", {"role": self.current_roles[i]})
            else:
                logger.warning(f"Data mapping collision: Client connection {i} went offline before delivery frames could be sent.")

        logger.info("Allowing 15s window loop pause for client interface render processing sync.")
        await asyncio.sleep(15)

        # Enter processing loops
        while not self.finished:
            if not self.finished:
                await self.run_night()
                await self.check_win()

            if not self.finished:
                await self.run_day()
                await self.check_win()   

        logger.success("Processing cycle flag complete. Running structural cleanup configurations.")
        await self.send_all_players("back_to_waiting", {})
        await self.send_all_players_dead("back_to_waiting", {})

        self.transfer_to_waiting_room()
        players = []
        for id in list(self.waiting_room):
            if id in self.players:
                players.append({"id": id, "name": self.players[id].name})

        await asyncio.sleep(1)
        
        self.status = 0
        await self.send_all_players_waiting("waiting_room_list_update", {"players": players, "status": self.status})
        
        self.phase_name = "waiting"
        self.phase_start_time = None
        self.phase_duration = 0
        logger.success("================== SYSTEM CLEANUP SETTLED: MAIN ROUTE LOOP ENDED CLEANLY ==================")