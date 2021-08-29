import logging
from multiprocessing import Process
import asyncio
import os
from pantsgrabbot import PantsGrabBot
from twitchio.ext import commands
import configparser

import nest_asyncio
nest_asyncio.apply()

class FollowingBot(commands.Bot):
    follow_set = set()
    processes = []


    def __init__(self, channel, oath, client_id, client_secret, debug_user):
        super().__init__(irc_token=oath, nick='PantsGrabBot', prefix='?',
                         initial_channels=[channel], client_id=client_id, client_secret=client_secret)

                         
    async def event_ready(self):
        pantsgrabbot = await self.get_users('pantsgrabbot')
        self.id = pantsgrabbot[0].id
        await self.get_following_daemon()


    async def get_following_daemon(self):
        while True:
            follow_set = await self.get_following(self.id)
            follow_set = {i['to_login'] for i in follow_set}
            if follow_set - self.follow_set != set():
                for channel in follow_set - self.follow_set:
                    os.makedirs(f'logs/{channel}', exist_ok=True)
                    new_bot = Process(target=start_bot, args=(channel,), daemon=True)
                    new_bot.start()
                    self.processes.append(new_bot)
                    logging.getLogger('pantsgrabbot').info(f'Started new bot for {channel}')
                self.follow_set = follow_set
            await asyncio.sleep(30)


def start_bot(username):
    bot = PantsGrabBot(username, config['TwitchCredentials']['oath'], config['TwitchCredentials']['client_id'], 
                        config['TwitchCredentials']['client_secret'],config['Debug']['debug_user'])
    bot.run()

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    followbot = FollowingBot(config['TwitchCredentials']['oath'], config['TwitchCredentials']['client_id'], 
                        config['TwitchCredentials']['client_secret'],config['Debug']['debug_user'])
    followbot.run()