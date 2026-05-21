import asyncio
from websockets.asyncio.server import serve
from modules.server.opcodes import opcodes
from modules.server.client import Client
from modules.data import random_id
from modules.logger import Logger
from modules.server.game import Game

import json

logger: Logger = Logger("ServerCore")

class Server():

    def __init__(self):
        self.clients = {}
        self.game = Game()
        opcodes["player_join"] = self.new_player_join

    async def new_player_join(self,message,client):

        player_id = client.id  
        client.name = message["name"]
        
        if not player_id in self.game.players:
            self.game.players[player_id] = client
            self.game.waiting_room.append(player_id)
            await self.game.new_player(player_id)
            logger.success(f"New player {client.name}")

    async def receive(self, websocket):

        player_id = str(id(websocket)) 
        new_client = Client(websocket, player_id) 
        
        self.clients[player_id] = new_client
        logger.debug(f"New client connected {player_id}")
        try:
            async for message in websocket:
                await self.handle_message(message, player_id)
        finally:
            logger.warning(f"Client quitted: {player_id}")
            self.game.waiting_room = [p for p in self.game.waiting_room if p != player_id]
            self.game.playing_room = [p for p in self.game.playing_room if p != player_id]
            self.game.death_room = [p for p in self.game.death_room if p != player_id]
            self.game.players.pop(player_id, None)
            self.clients.pop(player_id, None)

    async def handle_message(self, message, player_id):
            try:
                parsed = json.loads(message)
                opcode = parsed.get("opcode")
                data = parsed.get("data")

                if player_id in self.game.pending_responses:
                    if opcode in self.game.pending_responses[player_id]:
                        fut = self.game.pending_responses[player_id][opcode]
                        if not fut.done():
                            fut.set_result(data)
                            return 

                if opcode in opcodes:
                    await opcodes[opcode](data, self.clients[player_id])
                else:
                    logger.debug(f"Dropped message {opcode}")
                    
            except Exception as e:
                print(f"Error handling message: {e}")

    async def serve(self):
        async with serve(self.receive, "0.0.0.0", 8765) as server:
            while True:
                try:
                    await self.game.run_game()
                except Exception as e:
                    logger.error(f"Game crashed! {e}. Kicking everyone.")
                    try:
                        for i in self.game.players:
                            await self.game.players[i].conn.close()
                    except:
                        logger.error("Failed to kick everyone :(")
                        

    def run(self):
        asyncio.run(self.serve())
