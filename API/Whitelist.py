import os
from utils.Chat import UserManger, GroupManger

class Whitelist:
    def __init__(self, _message, csonfig):
        global message
        message = _message
        self._csonfig = csonfig
    def checkPerson(self):
        if UserManger(message.from_user.id).read('block'):
            return False
        if self._csonfig.get("whiteUserSwitch"):
            if UserManger(message.from_user.id).read("white"):
                return True
            else:
                return False
        else:
            return True
    def checkGroup(self):
        if GroupManger(message.chat.id).read('block'):
            return False
        if self._csonfig.get("whiteUserSwitch"):
            if GroupManger(message.chat.id).read("white"):
                return True
            else:
                return False
        else:
            return True
    def checkAll(self):
        if message.chat.id:
            if self.checkGroup():
                return True
            else:
                return False
        elif self.checkPerson():
            return True
        else:
            return False