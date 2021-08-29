import asyncio
import logging


class PyramidTracker():
    pyramid_size = 1
    pyramid_follow = 2
    decending = False
    previous_message = 'Placeholder'

    def __init__(self) -> None:
        self.logger = logging.getLogger('pantsgrabbot')

    def process_message(self, message):
        
        self.pyramiding = self.pyramid_state_update(message)
        
        completed = self.pyramiding and self.pyramid_follow == 0 and self.pyramid_size >= 3
        size = max(self.pyramid_size, self.pyramid_follow)

        if completed:
            self.reset(message)

        self.logger.debug(self.to_string())
        return self.pyramiding, size, completed

    def pyramid_state_update(self, message):
        # Get the number of emote in pyramid row 
        check_count = message.content.count(self.previous_message.content)

        # check if pyramid started decending
        if self.pyramiding and check_count == self.pyramid_follow - 2 and not self.decending:
            self.decending = True
            self.pyramid_follow -= 2
            self.pyramid_size = self.pyramid_follow + 1

        # Check if number of emotes in new row is expected, reset if not
        elif check_count != self.pyramid_follow:
            self.reset(message)
            return False

        # If number of emotes is valid, verify formatting and increment/decrement
        if len(message.content) == (len(self.previous_message.content)*self.pyramid_follow + self.pyramid_follow-1):
            if self.decending:
                self.pyramid_follow -= 1
            else:
                self.pyramid_follow += 1
            return True
        # reset if formatting is invalid
        else:
            self.reset(message)
            return False


    def reset(self, message):
        if max(self.pyramid_size, self.pyramid_follow) >= 3:
            self.pyramid_record[0] = self.previous_message
            asyncio.create_task(self.db.process_pyramid(self.pyramid_record, max(self.pyramid_size, self.pyramid_follow), self))
        self.previous_message = message
        self.pyramid_size = 1
        self.pyramid_follow = 2
        self.decending = False
        self.pyramiding = False
    
    def to_string(self):
        return f'pyramid_size: {self.pyramid_size}, pyramid_follow: {self.pyramid_follow}, decending: {self.decending}, previous_message: {self.previous_message}'
        