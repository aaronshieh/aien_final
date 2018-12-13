from keras.preprocessing.image import img_to_array
from keras.models import load_model
import numpy as np
import argparse
import imutils
import pickle
import cv2
import os
import time
from linebot import LineBotApi
from linebot.models import TextSendMessage,ImageSendMessage,LocationSendMessage
from linebot.exceptions import LineBotApiError
from imgurpython import ImgurClient
from opencvkeras.config import client_id, client_secret, album_id, access_token, refresh_token



def chatbot(image_url, label):
	CHANNEL_ACCESS_TOKEN = "AfBiSgayqOrt3H2XWjmscj32vnPtPB5yN4IOAN/fLmeE6kIP2gM5OOH91zwNmNCBugn0Ti5RQVuRDSnD0qbwzaLGCKen7/pQ56/cRhmetnR4GRVMKOilhOXQV5rMB6Gb0s4pw0FIyQq6a5seJ2j36AdB04t89/1O/w1cDnyilFU="
	to = "U097c09aa32416c7eadedf6c395449c53"
	line_bot_api=LineBotApi(CHANNEL_ACCESS_TOKEN)
	title = "資策會無人銀行"+"("+label+")"
	address = "10658台北市大安區信義路三段153號"
	latitude = 25.033788
	longitude = 121.542579
	try:
    	 	line_bot_api.push_message(to, LocationSendMessage(title=title,address=address,latitude=latitude,longitude=longitude))
	except LineBotApiError as e:
    		# error handle
    		raise e
	line_bot_api=LineBotApi(CHANNEL_ACCESS_TOKEN)
	try:
    		line_bot_api.push_message(to, ImageSendMessage(original_content_url=image_url, preview_image_url=image_url))
	except LineBotApiError as e:
    		# error handle
    		raise e

def run():
	check=[]
	startTime =time.time()
	timeElapsed = 0
	secElapsed = 0
	name=1
	danger=0
	safety=0
	
	path = 'opencvkeras'
	
	cap = cv2.VideoCapture(0)
	# Define the codec and create VideoWriter object
	fourcc = cv2.VideoWriter_fourcc(*'XVID')
	out = cv2.VideoWriter('output.mp4',fourcc, 20.0, (640,480))

	while(cap.isOpened()):
		ret, frame = cap.read()
		timeElapsed =time.time()-startTime
		secElapsed = int(timeElapsed)
		if ret==True:
			frame = cv2.flip(frame,90)
			# write the flipped frame
			out.write(frame)
			cv2.imshow('frame',frame)
			cv2.imwrite(path+'/examples/'+str(name)+'.jpg',frame)
			name=name+1
			if cv2.waitKey(3) & secElapsed>2:
				break
		else:
			break
	# Release everything if job is finished
	cap.release()
	out.release()
	cv2.destroyAllWindows()

	# load the image
	files = os.listdir(path+"/examples")
	for i in range(2,6,1):
		print(i)
		image = cv2.imread(path+"/examples/"+files[i])
		output = image.copy()
		print(files)
		# pre-process the image for classification
		image = cv2.resize(image, (96, 96))
		image = image.astype("float") / 255.0
		image = img_to_array(image)
		image = np.expand_dims(image, axis=0)

		# load the trained convolutional neural network and the label
		# binarizer
		print("[INFO] loading network...")
		model = load_model(path+"/pokedex.model")
		lb = pickle.loads(open(path+"/lb.pickle", "rb").read())

		# classify the input image
		print("[INFO] classifying image...")
		proba = model.predict(image)[0]
		idx = np.argmax(proba)
		label = lb.classes_[idx]
		imagepath="./examples/"+files[i]
		# we'll mark our prediction as "correct" of the input image filename
		# contains the predicted label text (obviously this makes the
		# assumption that you have named your testing image files this way)
		filename = imagepath[imagepath.rfind(os.path.sep) + 1:]
		correct = "Bank"
		check.append(label)
		# build the label and draw the label on the image
		label2 = "{}: {:.2f}% ({})".format(label, proba[idx] * 100, correct)
		output = imutils.resize(output, width=400)
		cv2.putText(output, label2, (10, 25),  cv2.FONT_HERSHEY_SIMPLEX,
		0.7, (0, 255, 0), 2)

		# show the output image
		print("[INFO] {}".format(label))
		# cv2.imshow("Output", output)
		# cv2.waitKey(1)
		if(label =="Gun" or label=="Thief" or label=="ThiefGun"):
			danger=danger+1
		else:
			safety=safety+1
		if(danger==3):
			print("Danger")
			cv2.imwrite(path+'/output/1.jpg',output)
			client = ImgurClient(client_id, client_secret, access_token, refresh_token)
			config = {
						'album': album_id,
						'name': 'test-name!',
						'title': 'test-title',
						'description': 'test-description'
					}
			print("Uploading image... ")
			image = client.upload_from_path(path+'/output/1.jpg', config=config, anon=False)
			print("Done")
			print("You can find the image here:{0}".format(image['link']))
			image_url=image['link']
			chatbot(image_url, label)
			break
		if(safety==3 or safety>3):
			print("Safety")
			cv2.imwrite(path+'/output/1.jpg',output)
			break
		cv2.destroyAllWindows()
	print(check)