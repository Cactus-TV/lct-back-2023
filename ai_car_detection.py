import cv2
import pika
import numpy as np
import threading
 
credentials = pika.PlainCredentials('test_user', 'test')
parameters = pika.ConnectionParameters('localhost', 5672, 'test_host', credentials)
connection_get = pika.BlockingConnection(parameters)
connection_post = pika.BlockingConnection(parameters)
channel_get = connection_get.channel()
channel_get.queue_declare(queue='test_rtsp_frames', durable=True)
channel_post = connection_post.channel()
channel_post.queue_declare(queue='test_ai_detected_frames', durable=True)
car_cascade = cv2.CascadeClassifier('haarcascade_cars.xml')
 
def callback(ch, method, properties, body):
    nparr = np.frombuffer(body, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    #convert video into gray scale of each frames
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w, channels = frame.shape
    frame = np.zeros((h, w, channels), dtype=np.uint8)
    #detect cars in the video
    cars = car_cascade.detectMultiScale(gray, 1.1, 3)

    #to draw a rectangle in each cars 
    for (x,y,w,h) in cars:
        try:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            #frame = frame[y:y+h,x:x+w]
            img_str = cv2.imencode('.jpg', frame)[1].tobytes()
            channel_post.basic_publish(exchange='', routing_key='test_ai_detected_frames', body=img_str)
        except:
            continue
 
channel_get.basic_consume(queue='test_rtsp_frames', auto_ack=True, on_message_callback=callback)
threading.Thread(target=channel_get.start_consuming, args=()).start()
# channel_get.start_consuming()

# #read until video is completed
while True:
    # if img_str:
    #     channel_post.basic_publish(exchange='', routing_key='test_ai_detected_frames', body=img_str)
     #press Q on keyboard to exit
    if cv2.waitKey(25) & 0xFF == ord('q'):
        connection_post.close()
        connection_get.close()
        break