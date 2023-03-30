from threading import Lock


class ThreadingLock(object):
    __instance = None

    @staticmethod
    def get_instance():
        if ThreadingLock.__instance is None:
            ThreadingLock.__instance = Lock()
        return ThreadingLock.__instance
