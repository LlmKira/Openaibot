def detect_lang(text):
    try:
        from fatlangdetect import detect
        return detect(text=text.replace("\n", "").replace("\r", ""), low_memory=True).get("lang").upper()
    except Exception as e:
        from langdetect import detect
        return detect(text=text.replace("\n", "").replace("\r", ""))[0][0].upper()