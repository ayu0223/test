# インポートするライブラリ
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, MessageTemplateAction, URITemplateAction
)
import os
import boto3

# 軽量なウェブアプリケーションフレームワーク:Flask
app = Flask(__name__)


#環境変数からLINE Access Tokenを設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
#環境変数からLINE Channel Secretを設定
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# MessageEvent
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
	line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='「' + event.message.text + '」って何？')
     )

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)

# 画像メッセージの場合
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    image_bin = BytesIO(message_content.content)
    image = image_bin.getvalue()

    # S3へ画像を保存
    s3 = boto3.client('s3')
    filename = message_id + '.jpg' # メッセージIDをファイル名とする
    s3.put_object(Bucket='backetを指定', Body=image,  Key=filename)

 # Rekognition呼び出し
    rekognition = boto3.client('rekognition')
    response = rekognition.detect_faces(
        Image={
            'S3Object': {
                'Bucket': 'backetを指定',
                'Name': filename
            }
        },
        Attributes=[
            'ALL'
        ]
    )

    # 結果から感情データを取得
    message = ''
    cnt = 0
    for face_detail in response['FaceDetails']:
        cnt += 1
        message += str(cnt) + '人目\n'
        for emotion in face_detail['Emotions']:
            message += translation(emotion['Type']) + ':' + \
                str(round(emotion['Confidence'], 6)) + '\n'


def translation(type):
    if type == 'HAPPY':
        return '幸せ'
    elif type == 'SAD':
        return '悲しみ'
    elif type == 'ANGRY':
        return '怒り'
    elif type == 'SURPRISED':
        return '驚き'
    elif type == 'DISGUSTED':
        return '嫌悪'
    elif type == 'CALM':
        return '穏やか'
    elif type == 'CONFUSED':
        return '困惑'
    elif type == 'FEAR':
        return '恐れ'