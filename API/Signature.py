import hmac, base64

class APISignature(object):
    def __init__(self, apicfg):
        self.secret = apicfg['secret']
        self.text = apicfg['text']
        self.timestamp = apicfg['timestamp']
    def sign(self):
        raw = self.text + "\n" + self.timestamp
        sign = base64.b64encode(hmac.new(self.secret.encode(), raw.encode(), digestmod='SHA256').digest())
        return sign.decode()
    def verify(self, sign):
        truesign = self.sign()
        if sign == truesign:
            return True
        else:
            return False