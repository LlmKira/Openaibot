# from loguru import logger

class FakeTGBotUser:  # 人
    id: int


class FakeTGBotChat:  # 群
    id: int


class FakeTGBotMessage:  # 信
    from_user = FakeTGBotUser()
    chat = FakeTGBotChat()
    text: str


class FakeTGBot:

    def __init__(self, reply_to_callback):
        self.callback = reply_to_callback  # breakpoint here
        # logger.info('fake tg bot class')

    # global resp
    async def reply_to(self, message, text):
        # logger.info('reply_to !')
        if not self.callback:
            return
        self.callback(message, text)
