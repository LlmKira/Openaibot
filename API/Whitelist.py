import os
from utils.Chat import UserManger, GroupManger

class FakeTGBotUser:
    id: int
class FakeTGBotChat:
    id: int
class FakeTGBotMessage:
    from_user = FakeTGBotUser()
    chat = FakeTGBotChat()

message = FakeTGBotMessage()

class Whitelist:
    def __init__(self, incomingObject, appe):
        message.chat.id = incomingObject.groupId
        message.from_user.id = incomingObject.chatId
        self._csonfig = appe.load_csonfig()
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