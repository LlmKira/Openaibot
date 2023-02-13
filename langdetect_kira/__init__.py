from .langdetect import LangDetector

__langDetector = LangDetector()


def detect(text):
    return __langDetector.detect(text)


__all__ = ['detect']
