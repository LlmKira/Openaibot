class FakeTGBotUser:    #人
    id: int
class FakeTGBotChat:    #群
    id: int
class FakeTGBotMessage: #信
    from_user = FakeTGBotUser()
    chat = FakeTGBotChat()