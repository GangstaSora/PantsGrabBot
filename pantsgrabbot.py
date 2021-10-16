import asyncio
from twitchio.ext import commands
import pyramid_db
import logging_setup
import pyramid_tracker
import configparser
import golf

        
class PantsGrabBot(commands.Bot):
    is_live = False
    pyramid_record = []
    pepege_trackers = {}
    timeout_time = 60
    grabbed_users = set()
    is_mitosis = True
    command_ready = True


    def __init__(self, channel, oath, client_id, client_secret, debug_user):
        super().__init__(irc_token=oath, nick='PantsGrabBot', prefix='?',
                         initial_channels=[channel], client_id=client_id, client_secret=client_secret)

        if channel == debug_user:
            self.DEBUG = True
        else:
            self.DEBUG = False

        self.pyramid_tracker = pyramid_tracker.PyramidTracker()
        self.db = pyramid_db.PyramidDb()
        self.logger = logging_setup.setup(channel)

        self.golf = golf.GolfGame()	


    # Events don't need decorators when subclassed
    async def event_ready(self):
        self.logger.info(f'Ready | {self.nick}')
        asyncio.create_task(self.check_live(self.initial_channels[0]))

    async def check_live(self, channel):
        while True:
            stream_info = await self.get_stream(channel)
            if stream_info is not None:
                self.is_live = True
            else:
                self.is_live = False
            self.logger.info(f'{channel} is_live: {self.is_live}')
            await asyncio.sleep(30)


    async def event_message(self, message):
        # pre-processing 
        message.content = message.content.replace('\U000e0000', '') #??? why twitch
        message.content = " ".join(message.content.split())
        message.content = message.content.strip()
        self.pyramid_record.append(message)

        # PantsGrab functionality
        if message.content.lower().count("pantsgrabbot") > 0:
            await self.grab(message)

        # log all messages for debuging purposes
        self.logger.info(f'(Chat) {message.author.name}: {message.content}')

        # only process pyramids when the streamer is live (or running on testing channel)
        if self.is_live or self.DEBUG:

            # process this message in the main pyramid processor
            main_pyramiding, main_size, main_completed = self.pyramid_tracker.process_message(message)

            # process this message for pepegeClap pyramids
            pepege = self.pepege_trackers.setdefault(message.author.name, pyramid_tracker.PyramidTracker())
            _, _, pepege_completed = pepege.process_message(message)

            # if a pyramid is not active, check if there is a pyramid to process and reset the message record 
            if not main_pyramiding:
                # if not pyramiding, but there are at least 4 messages, process completed or griefed pyramid
                if len(self.pyramid_record) >= 4: 
                    self.logger.info("Processing pyramid...")
                    asyncio.create_task(self.db.process_pyramid(list(self.pyramid_record), main_size, self))
                # either way if not pyramiding, reset the message record
                self.pyramid_record = [message]
            # send pepegeClap message if pepege pyramid was completed
            if pepege_completed and not main_completed:
                await self.send_wrapper(message.channel.send, f'pepegeClap {message.author.name} kept going')
        else:
            # prevents pyramid record being filled up while streamer is offline
            self.pyramid_record = [message]
                
        # process any commands
        await self.handle_commands(message)
                

    ############ Commands ###################################################################################
    @commands.command(name='points')
    async def my_command(self, ctx, name=None):
        if name is None:
            chatter = await self.db.get_chatter_points(ctx.author.name.lower(), ctx.channel.name)
        else:
            chatter = await self.db.get_chatter_points(name.lower(), ctx.channel.name)
        await self.send_wrapper(ctx.send, f'@{chatter[1].name} has {chatter[0].points} points!')


    @commands.command(name='leaderboard')
    async def leader_command(self, ctx):
        leaders = await self.db.get_leaderboard(ctx.channel.name, False)
        
        output = 'Your top pyramiders are... \n'
        for i, leader in enumerate(leaders[:5]):
            output += f'{i+1}. {leader.chatter.name}: ({leader.points} points) \n'

        await self.send_wrapper(ctx.send, output)


    @commands.command(name='grieferboard')
    async def griefer_command(self, ctx, name=None):
        griefers = await self.db.get_leaderboard(ctx.channel.name, True)
        
        output = 'Your top griefers are... \n'
        for i, griefer in enumerate(griefers[:5]):
            output += f'{i+1}. {griefer.chatter.name}: ({griefer.points} points) \n'

        await self.send_wrapper(ctx.send, output)


    @commands.command(name='candy')
    async def candy_command(self, ctx):
        await self.send_wrapper(ctx.send, 'Night gathers, and now my watch begins. NOPERS It shall not end until my death. NOPERS I shall take no wife, hold no lands, father no children. NOPERS I shall wear no crowns and win no glory. NOPERS I shall live and die at my post. NOPERS I am the sword in the darkness. NOPERS I will grief all of candy\'s pyramids for this night and all the nights to come')


    @commands.command(name='marbles')
    async def marbles_command(self, ctx):
        await self.send_wrapper(ctx.send, '!play')

    
    @commands.command(name='announcement')
    async def announcement(self, ctx):
        with open("announcement.txt", mode='r', encoding='utf-8') as f:
            message = f.readline()
            await self.send_wrapper(ctx.send, message)


    @commands.command(name='tft')
    async def tft_command(self, ctx):
        tft_comment = '''Teamfight Tactics (TFT) is an auto battler game developed and published by Riot Games. While it was received very positively at launch, many players are un-happy with a new mechanic called "getting Mortdogged". Players who have been "Mortdogged" receive a lower placement solely due to Mortdog's inability to balance his game, rather than an actual gap in their skill levels. Many players are leaving tft for "Golf With Your Friends" where placements are determined purely by player skill.'''
        await self.send_wrapper(ctx.send, tft_comment)

    
    @commands.command(name='timeouttime')
    async def timeouttime(self, ctx, time=5):
        if ctx.author.is_mod:
            self.timeout_time = time
            await self.send_wrapper(ctx.send, f'Now timing out griefers for {time} seconds Okayge ')


    @commands.command(name="tourney")
    async def golf_tourney(self, ctx):
        await self.send_wrapper(ctx.send, f'The Kurum\'s Hole Golf Invitational is starting soon! Type "@iCandyyyy  dinkDonk " to sign up! ')


    @commands.command(name='golf')
    async def golf_command(self, ctx):
        await self.golf.play(ctx)

    @commands.command(name='1')
    async def golf_vote_1(self, ctx):
        self.golf.vote(0)


    @commands.command(name='2')
    async def golf_vote_2(self, ctx):
        self.golf.vote(1)


    @commands.command(name='3')
    async def golf_vote_3(self, ctx):
        self.golf.vote(2)


    @commands.command(name='4')
    async def golf_vote_4(self, ctx):
        self.golf.vote(3)


    @commands.command(name='creator')
    async def creator_command(self, ctx):
        await self.send_wrapper(ctx.send, f'I was created by iCandyyyy :) ')


    @commands.command(name='mitosis')
    async def mitosis(self, ctx):
        if self.is_mitosis:
            self.is_mitosis = False
            sequence = [
                'YEP ',
                'YEEP ',
                'YP YP ',
                'YEP YEP ',
            ]
            for msg in sequence:
                await self.send_wrapper(ctx.send, msg)
                await asyncio.sleep(1.5)
            await asyncio.sleep(54)
            self.is_mitosis = True
        

    @commands.command(name='greifer')
    async def griefers(self, ctx):
        await self.send_wrapper(ctx.send, "I swear to god when I get mod I'm going to ban all you pyramid greifers Prayge ")


    @commands.command(name="wintrade")
    async def wintrade(self, ctx):
        await self.send_wrapper(ctx.send, "注意公民。 这是国家安全部。您的互联网活动引起了我们的注意。由于您的网络犯罪，您的社会 用评分将降至 -70。 (-70) 不要再这样做了。中国共产党的光荣。ATTENTION PLAYER. THIS IS THE TFT DEV TEAM. YOUR MATCH HISTORY HAS ATTRACTED OUR ATTENTION. DUE TO YOUR GAMEPLAY CRIMES YOU WILL BE BROUGHT DOWN TO -70 LADDER POINTS. (-70) DO NOT DO THIS AGAIN. GLORY TO THE GAME DESIGNER MORTDOG")

    @commands.command(name='subtember')
    async def subs(self, ctx):
        if ctx.channel.name == 'kurumx' or ctx.channel.name == 'gangstasora':
            await self.send_wrapper(ctx.send, '''Hello everyone subs are 20% off so please sub to this bum he needs to feed iCandyyyy's maplestory gacha addiction OkaygeBusiness ''')

    
######## Helpers ######################################################################################

    async def send_wrapper(self, send, message):
        await send(message)
        self.logger.info(f'Msg Sent: {message}')


    async def grab(self, message):
        if message.author.name not in self.grabbed_users:
            await self.send_wrapper(message.channel.send, f'@{message.author.name} PantsGrab')

            self.grabbed_users.add(message.author.name)
            await asyncio.sleep(30)
            self.grabbed_users.remove(message.author.name)




if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    bot = PantsGrabBot(config['Debug']['debug_user'], config['TwitchCredentials']['oath'], 
                       config['TwitchCredentials']['client_id'], config['TwitchCredentials']['client_secret'], 
                       config['Debug']['debug_user'])
    bot.run()   