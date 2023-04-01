import base64
import hmac


class APISignature(object):
    def __init__(self, api_cfg):
        self.secret = api_cfg['secret']
        self.text = api_cfg['text']
        self.timestamp = api_cfg['timestamp']

    def sign(self):
        raw = self.text + "\n" + self.timestamp
        sign = base64.b64encode(hmac.new(self.secret.encode(), raw.encode(), digestmod='SHA256').digest())
        return sign.decode()

    def verify(self, sign):
        _true_sign = self.sign()
        if sign == _true_sign:
            return True
        else:
            return False
