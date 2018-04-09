# -*- encoding: utf-8 -*-
import json
import requests
import sys
import pya3rt
from django.http import HttpResponse
from linebot import LineBotApi
from PIL import Image
from io import BytesIO

sys.path.append('./bot')

REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
ACCESS_TOKEN = '*****'
HEADER = {
    "Content-Type": "application/json",
    "Authorization": "Bearer " + ACCESS_TOKEN
}
lINE_BOT_API = LineBotApi(ACCESS_TOKEN)

# recuitAPI
recuitapikey = "******"
client = pya3rt.TalkClient(recuitapikey)

# docomoAPI
docomoapikey = '********'
# Get API_Path
def __build_url(name, version='v1'):
    return __api_path.format({'version': version, 'name': name})

__api_path = 'https://api.apigw.smt.docomo.ne.jp/imageRecognition/{0[version]}/{0[name]}'


def index(request):
    return HttpResponse("This is bot api.")

    # Reply text
def reply_text(reply_token, rep_meg):
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": rep_meg
            }
        ]
    }

    requests.post(REPLY_ENDPOINT, headers=HEADER, data=json.dumps(payload))  # to send data to LINE
    return rep_meg


    # Save image
def save_image(messegeid):
    message_content = lINE_BOT_API.get_message_content(messegeid)

    i = Image.open(BytesIO(message_content.content))
    filename = '/tmp/' + messegeid + '.jpg'
    i.save(filename)

    return filename

    # Get json
def get_json(filename):
    with open(filename, mode='rb') as f:
        result = requests.post(
            url=__build_url('recognize'),
            params={'APIKEY': docomoapikey, 'recog': 'product-all', 'numOfCandidates': 5},
            data=f,
            headers={'Content-Type': 'application/octet-stream'})
        result.raise_for_status()
        result = result.json()
    return result

    # Reply carousel
def post_carousel(reply_token,imageUrl,title,brand,releaseDate,maker,url,itemName):

    payload = {
          "replyToken":reply_token,
          "messages":[
              {
                "type": "template",
                "altText": "商品結果",
                "template": {
                    "type": "carousel",
                    "columns": [
                        {
                          "thumbnailImageUrl": imageUrl[i],
                          "title": itemName[i],
                          "text": "ブランド名：" + brand[i] + " メーカー名："+ maker[i] +" 発売日：" +releaseDate[i],
                          "actions": [

                              {
                                  "type": "uri",
                                  "label": "Amazonで見る",
                                  "uri": url[i]
                              }
                          ]
                        } for i in range(len(itemName))
                      ]
                }
              }
            ]
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER, data=json.dumps(payload))

    return title[len(title)-1]



def callback(request):
    reply = ""
    request_json = json.loads(request.body.decode('utf-8'))  # to get json

    for e in request_json['events']:
        reply_token = e['replyToken']  # to get reply_token
        message_type = e['message']['type']  # to get type

        # reply for test
        if message_type == 'text':
            text = e['message']['text']  # to get message
            rep_meg = client.talk(text)["results"][0]["reply"]  # to get reply message by recuitTalk
            reply += reply_text(reply_token,rep_meg)

            # reply for image
        if message_type == 'image':
            messegeid = e['message']['id']  # to get messageID
            filename = save_image(messegeid)
            result = get_json(filename)
            #print(result)
            if (result.get('candidates') != None):
              imageUrl,title,brand,releaseDate,maker,url,itemName =[],[],[],[],[],[],[]

              for i in range(len(result['candidates'])): # to get item info
                imageUrl.append(result['candidates'][i]['imageUrl'])
                title.append(result['candidates'][i]['sites'][0]['title'])
                brand.append(result['candidates'][i]['detail']['brand'])
                releaseDate.append(result['candidates'][i]['detail']['releaseDate'])
                maker.append(result['candidates'][i]['detail']['maker'])
                url.append(result['candidates'][i]['sites'][0]['url'])
                itemName.append(result['candidates'][i]['detail']['itemName'][0:29]) # to restrict length

              reply += post_carousel(reply_token,imageUrl,title,brand,releaseDate,maker,url,itemName)

            else:
                rep_meg = "認識できんかったわ。撮り直し！"
                reply += reply_text(reply_token, rep_meg)

    return HttpResponse(reply)  # for test
