import asyncio


class GolfState:
    def __init__(self, text, mapping):
        self.text = text
        self.mapping = mapping
        

states = [
    GolfState("You place your ball down and get ready to take your first shot. (Par 3, vote on shot with ?<number>): ?1 Full send 4 bars. ?2 3 bars bounce off the angled block. ?3 2 bars straight forward",
    [1, -1, 2]),
    GolfState("The ball bounces over the course wall and you start back at the beginning. (Par 3, vote on shot with ?<number>): ?1 Full send 4 bars. ?2 3 bars bounce off the angled block. ?3 2 bars straight forward",
    [1, -1, 2]),
    GolfState("The ball stops with a straight line of sight to the hole. (Par 3, vote on shot with ?<number>): ?1 1.5 bars straight to the hole. ?2 2 bars fancy shot off the back wall. ?3 4 bars full send",
    [-1, 3, 5]),
    GolfState("The fancy shot stops just short of the hole. (Par 3, vote on shot with ?<number>): ?1 0.5 bars tap it into the hole. ?2 4 bars full send",
    [-1, 4]),
    GolfState("The ball bounces over the course wall and you return to the previous position next to the hole. (Par 3, vote on shot with ?<number>): ?1 0.5 bars tap it into the hole. ?2 4 bars full send",
    [-1, 4]),
    GolfState("The ball bounces over the course wall and you return to the previous position in line with the hole. (Par 3, vote on shot with ?<number>): ?1 1.5 bars straight to the hole. ?2 2 bars fancy shot off the back wall. ?3 4 bars full send",
    [-1, 3, 5])
]


class GolfGame:
    winning_message = {
        1:"Hole in one! POGGIES ",
        2:"Birdie! peepoClap ",
        3:"Par! Okayge ",
        4:"Bogey Smoge ",
        5:"Double-Bogey Smoge ",
        6:"Triple-Bogey Smoge ",
        7:"Seven Strokes",
        8:"Eight Strokes",
        9:"Nine Strokes",
        10:"10 Strokes"
    }
    def __init__(self):
        self.playing = False
        self.states = states
        

    async def play(self, ctx):
        if self.playing == False:
            self.playing = True
            self.votes = [0, 0, 0, 0]
            self.strokes = 0
            self.ctx = ctx
            await self.process_state(self.states[0])
            self.playing = False
    

    def vote(self, vote):
        self.votes[vote] += 1


    def get_winning_vote(self, options):
        considered_votes = self.votes[:options]
        max_votes = max(considered_votes)
        if max_votes > 0:
            winner = considered_votes.index(max_votes)
        else: 
            winner = -1
        self.votes = [0,0,0,0]
        return winner


    async def process_state(self, state):
        await self.ctx.send(state.text)
        await asyncio.sleep(20)
        self.strokes += 1
        winner = self.get_winning_vote(len(state.mapping))
        option_selected = f'Option {winner + 1} chosen. '
        if winner == -1:
            return # no one voted, so end the game
        elif state.mapping[winner] == -1:
            await self.ctx.send(option_selected)
            await asyncio.sleep(1.5)
            await self.ctx.send("The ball goes in the hole. " + GolfGame.winning_message[self.strokes])
        elif self.strokes >= 10:
            await self.ctx.send(option_selected)
            await asyncio.sleep(1.5)
            await self.ctx.send("Out of Strokes Sadge")
        else:
            await self.ctx.send(option_selected)
            await asyncio.sleep(1.5)
            await self.process_state(self.states[state.mapping[winner]])
