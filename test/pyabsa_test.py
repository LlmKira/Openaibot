# -*- coding: utf-8 -*-
# @Time    : 2/1/23 11:18 PM
# @FileName: pyabsa.py
# @Software: PyCharm
# @Github    ：sudoskys
"""
from pyabsa import ATEPCCheckpointManager
from pyabsa import available_checkpoints

aspect_extractor = ATEPCCheckpointManager.get_aspect_extractor(checkpoint='multilingual-256-2')

result = aspect_extractor.extract_aspect(inference_source=["我爱你"],
                                         pred_sentiment=True)
print(result)
"""
import aspect_based_sentiment_analysis as absa

nlp = absa.load()
text = ("We are great fans of Slack, but we wish the subscriptions "
        "were more accessible to small startups.")

slack, price = nlp(text, aspects=['slack', 'price'])
assert price.sentiment == absa.Sentiment.negative
assert slack.sentiment == absa.Sentiment.positive
