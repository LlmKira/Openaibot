import os
os.chdir("..")
from utils.Chat import UserManger, GroupManger
import App.Event as appe

class FakeTGBotUser:
    id: int
class FakeTGBotChat:
    id: int
class FakeTGBotMessage:
    from_user = FakeTGBotUser()
    chat = FakeTGBotChat()

message = FakeTGBotMessage()
_csonfig = appe.load_csonfig()

class Whitelist:
    def __init__(self, incomingObject):
        message.chat.id = incomingObject.groupId
        message.from_user.id = incomingObject.userId
    def checkPerson(self):
        if UserManger(message.from_user.id).read('block'):
            return False
        if _csonfig.get("whiteUserSwitch"):
            if UserManger(message.from_user.id).read("white"):
                return True
            else:
                return False
        else:
            return True
    def checkGroup(self):
        if GroupManger(message.chat.id).read('block'):
            return False
        if _csonfig.get("whiteUserSwitch"):
            if GroupManger(message.chat.id).read("white"):
                return True
            else:
                return False
        else:
            return True
    def checkAll(self):
        if message.chat.id:
            if self.checkPerson() and self.checkGroup():
                return True
            else:
                return False
        elif self.checkPerson():
            return True
        else:
            return False