from ratelimit import limits, sleep_and_retry
import time
import datetime

test = 1

@sleep_and_retry
@limits(calls=1, period=.21)
def ratelimit_APIxxx():
    """Empty function to check for calls to API"""
    return

def printdatetime(i):
    test + 1
    print(str(i) + ': ' + datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))

i=0
while i<100:
    try:
        ratelimit_APIxxx()
        printdatetime(i)
    except:
        print('error')
    i+=1




def func(i):
    if i == 0:
        break
    print(i)
    print(2 * i)
    return i+1




from deep_translator import (GoogleTranslator,
                              PonsTranslator,
                              LingueeTranslator,
                              MyMemoryTranslator,
                              YandexTranslator,
                              DeepL,
                              QCRI,
                              single_detection,
                              batch_detection)
# from deep_translator import GoogleTranslator
# from deep_translator import DeepL
# from deep_translator import LingueeTranslator
# translated = GoogleTranslator(source='nl', target='en').translate_batch(["hallo", "benzeen"])
# translated = GoogleTranslator(source='nl', target='en').translate_batch(["hallo benzeen"])
# translated = DeepL("your_api_key").translate('hallo')

LingueeTranslator(source='nl', target='en').translate("temperatuur")
LingueeTranslator(source='nl', target='en').translate("zuurgraad")

PonsTranslator(source='nl', target='en').translate("waterdiepte")
GoogleTranslator(source='nl', target='en').translate(text="waterdiepte")
PonsTranslator(source='en', target='fr').translate(word)
