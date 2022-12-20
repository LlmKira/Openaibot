# -*- coding: utf-8 -*-
# @Time    : 12/20/22 10:03 AM
# @FileName: azure_tts.py
# @Software: PyCharm
# @Github    ：sudoskys

def azure_tts(text: str = "", api_key: str = "", region: str = "", voice_name: str = "zh-CN-XiaoxiaoNeural"):
    if not all([text, api_key, region, voice_name]):
        return
    # pip install azure-cognitiveservices-speech
    import azure.cognitiveservices.speech as speechsdk
    from azure.cognitiveservices.speech import AudioDataStream
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    speech_config.speech_synthesis_voice_name = voice_name
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    result = synthesizer.speak_text_async(text).get()
    stream = AudioDataStream(result)
    speech_synthesis_result = result
    Error = None
    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        Error = ("Speech synthesized for text [{}]".format(text))
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        Error = ("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            if cancellation_details.error_details:
                Error = ("Error details: {}".format(cancellation_details.error_details))
    return stream, Error
