from threading import Lock

class pLock(object):
    __instance = None
    @staticmethod
    def getInstance():
        if pLock.__instance is None:
            pLock.__instance = Lock()
        return pLock.__instance