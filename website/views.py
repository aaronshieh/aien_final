from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import dialogflow, json, requests
from google.protobuf.json_format import MessageToJson

import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="TaipeiBus-d9a21c23d606.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="test-6853bf0aa060.json"
# DIALOGFLOW_PROJECT_ID = 'taipeibus-3f5d4'
DIALOGFLOW_PROJECT_ID = 'test-7405b'

def index(request):
    title = 'main'
    return render(request, 'website/index.html', locals())

def camera(request):
    title = 'camera'
    return render(request, 'website/camera_test.html', locals())
    
@csrf_exempt
def uploadImage(request):
    if request.method == 'POST':
        print('uploadImage start...')
        imgString = request.POST['image']
        imgString = imgString.replace('data:image/png;base64,', '')

        import base64
        imgdata = base64.b64decode(imgString)
        filename = 'cameraCapture.png'  
        with open(filename, 'wb') as f:
            f.write(imgdata)
        print('uploadImage end...')
        return HttpResponse('uploadImage done')

def chatbot(request):
    title = 'chatbot'
    return render(request, 'website/chatbot.html', locals())

# 接Google Dialogflow 語意分析參數
@csrf_exempt
def webhook(request):
    if request.method == 'POST':
        # print(json.loads(request.body).keys())
        # 取得公車路線號碼
        bus_route = json.loads(request.body)['queryResult']['parameters']['bus_route_number']
        bus_route = str(int(bus_route))
        print(bus_route)
        # 設定公共運輸API需要的資料
        payload = {
            '$format': 'JSON'
        }
        # 僞裝request來自於瀏覽器，不需要申請API KEY
        header = {'user-agent':'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
        # 送出要求
        r = requests.get('https://ptx.transportdata.tw/MOTC/v2/Bus/RealTimeNearStop/City/Taipei/' + bus_route, params=payload, headers=header)
        print(r.url)
        # 要求成功
        if r.status_code == 200:
            # 讀出資料
            body = r.json()
            print(body)

            # 打包回給google dialogflow的fulfillmentMessage
            fulfillmentMessagesObj = []
            for bus in body:
                direction = ""
                if bus['Direction'] == 0:
                    direction = '去程'
                elif bus['Direction'] == 1:
                    direction = '返程'
                # 顯示該路線的公車車牌、方向（去程或返程）、站牌名稱
                fulfillment_text = {
                    "text":{
                        "text":[bus["PlateNumb"], "direction: " + direction, "stop: " + bus['StopName']['Zh_tw']]
                    }
                }
                fulfillmentMessagesObj.append(fulfillment_text)

            # 傳JSON回給google dialogflow
            response = JsonResponse({'fulfillmentMessages':fulfillmentMessagesObj})
            return response

def detect_intent_texts(project_id, session_id, text, language_code):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    if text:
        text_input = dialogflow.types.TextInput(text=text, language_code=language_code)
        query_input = dialogflow.types.QueryInput(text=text_input)
        response = session_client.detect_intent(session=session, query_input=query_input)
        # print(response.query_result)
        return response.query_result.fulfillment_messages

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        message = request.POST['message']
        project_id = DIALOGFLOW_PROJECT_ID
        # fulfillment_text = detect_intent_texts(project_id, "unique", message, 'en')
        fulfillment_text = detect_intent_audio(project_id, "unique", 'hello.wav', 'en')
        # print(type(fulfillment_text))
        print("audio test", fulfillment_text)
        fulfillment_obj = []
        for obj in fulfillment_text:
            fulfillment_obj.append(json.loads(MessageToJson(obj)))

        # fulfillment_text = json.loads(message_json)
        response_text = { "message":  fulfillment_obj }
        print(response_text)
        return JsonResponse(response_text)

def detect_intent_audio(project_id, session_id, audio_file_path,
                        language_code):
    """Returns the result of detect intent with an audio file as input.
    Using the same `session_id` between requests allows continuation
    of the conversaion."""
    # import dialogflow_v2 as dialogflow

    session_client = dialogflow.SessionsClient()

    # Note: hard coding audio_encoding and sample_rate_hertz for simplicity.
    audio_encoding = dialogflow.enums.AudioEncoding.AUDIO_ENCODING_LINEAR_16
    sample_rate_hertz = 16000

    session = session_client.session_path(project_id, session_id)
    print('Session path: {}\n'.format(session))

    with open(audio_file_path, 'rb') as audio_file:
        input_audio = audio_file.read()

    audio_config = dialogflow.types.InputAudioConfig(
        audio_encoding=audio_encoding, language_code=language_code)
    query_input = dialogflow.types.QueryInput(audio_config=audio_config)

    response = session_client.detect_intent(
        session=session, query_input=query_input,
        input_audio=input_audio)

    print('=' * 20)
    print('Query text: {}'.format(response.query_result.query_text))
    print('Detected intent: {} (confidence: {})\n'.format(
        response.query_result.intent.display_name,
        response.query_result.intent_detection_confidence))
    print('Fulfillment text: {}\n'.format(
        response.query_result.fulfillment_text))