class FakeTGBotUser:    #人
    id: int
class FakeTGBotChat:    #群
    id: int
class FakeTGBotMessage: #信
    from_user = FakeTGBotUser()
    chat = FakeTGBotChat()
    text: str

class FakeTGBot:
    '''
    def __init__(self, reply_to_callback):
        self.callback = reply_to_callback
    '''
    global resp
    def reply_to(self, message, text):
        resp = text