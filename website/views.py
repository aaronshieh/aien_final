from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import dialogflow, json, requests, base64
from google.protobuf.json_format import MessageToJson

import os
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="TaipeiBus-d9a21c23d606.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="test-6853bf0aa060.json"
# DIALOGFLOW_PROJECT_ID = 'taipeibus-3f5d4'
DIALOGFLOW_PROJECT_ID = 'test-7405b'

def index(request):
    title = 'main'
    return render(request, 'website/voicebot.html', locals())

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

def voicebot(request):
    title = 'voicebot'
    return render(request, 'website/voicebot.html', locals())

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

@csrf_exempt
def receive_audio(request):
    if request.method == 'POST':
        audio_file = request.FILES['audio_data']
        with open('command.wav', 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        response = detect_intent_audio(DIALOGFLOW_PROJECT_ID, "unique", 'command.wav', 'en')
        return JsonResponse(response)

def detect_intent_audio(project_id, session_id, audio_file_path,
                        language_code):
    """Returns the result of detect intent with an audio file as input.
    Using the same `session_id` between requests allows continuation
    of the conversaion."""
    # import dialogflow_v2 as dialogflow
    import dialogflow_v2beta1 as dialogflow

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
    # print(response)
    # with open('output.wav', 'wb') as out:
    #     out.write(response.output_audio)
    #     print('Audio content written to file "output.wav"')

    encoded_audio = base64.b64encode(response.output_audio)
    encoded_audio = encoded_audio.decode('ascii')

    response_ = {
        'result': 'error',
        'response_audio': encoded_audio,
        'fulfillment_text': response.query_result.fulfillment_text
    }

    if response.query_result.intent.display_name != '':
        response_['result'] = 'success'
 
    if response.query_result.intent.display_name == 'Open Account':
        response_['intent'] = 'open_account'
    elif response.query_result.intent.display_name == 'Money Transfer':
        response_['intent'] = 'money_transfer'
    elif response.query_result.intent.display_name == 'Security':
        response_['intent'] = 'security'
    elif response.query_result.intent.display_name == 'Predict':
        response_['intent'] = 'predict'
    else:
        response_['intent'] = 'unknown'

    return response_