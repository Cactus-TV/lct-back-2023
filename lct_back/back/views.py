from django.shortcuts import render, redirect
from django.views.decorators import gzip
from django.views.generic import TemplateView
from django.http import StreamingHttpResponse
from .models import Stream
from django.db.models import Q
import pika
import numpy as np

import cv2
import threading

@gzip.gzip_page
def transmition(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'stream.html')

#to capture video class
class VideoCamera(object):
    def __init__(self):
        credentials = pika.PlainCredentials('test_user', 'test')
        parameters = pika.ConnectionParameters('localhost', 5672, 'test_host', credentials)
        self.connection_get = pika.BlockingConnection(parameters)
        self.connection_post = pika.BlockingConnection(parameters)
        self.channel_post = self.connection_post.channel()
        self.channel_get = self.connection_get.channel()
        self.channel_post.queue_declare(queue='test_rtsp_frames', durable=True)
        self.channel_get.queue_declare(queue='test_ai_detected_frames', durable=True)
        # camera = list(Stream.objects.filter(Q(uid=id)))[0]
        # login = camera.username
        # password = camera.password
        # url = camera.url
        # self.channel_get.basic_consume(queue='test_ai_detected_frames', auto_ack=True, on_message_callback=self.callback)
        # threading.Thread(target=self.channel_get.start_consuming, args=()).start()
        # self.video = cv2.VideoCapture(f'rtsp://{login}:{password}@{url}')
        self.video = cv2.VideoCapture('rtsp://admin:A1234567@188.170.176.190:8027/Streaming/Channels/101?transportmode=unicast&profile=Profile_1')
        self.grabbed, self.frame = self.video.read()
        h, w ,ch = self.frame.shape
        self.ai_frame = np.zeros((h, w, ch), dtype=np.uint8)
        threading.Thread(target=self.update, args=()).start()
        threading.Thread(target=self.consume_queue, args=()).start()

    def __del__(self):
        self.connection_post.close()
        self.connection_get.close()
        self.video.release()

    def get_frame(self):
        image = self.frame
        if self.grabbed:
            jpeg = cv2.imencode('.jpg', image)[1]
            return jpeg.tobytes()
    
    def callback(self, ch, method, properties, body):
        nparr = np.frombuffer(body, np.uint8)
        self.ai_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    def consume_queue(self):
        self.channel_get.basic_consume(queue='test_ai_detected_frames', on_message_callback=self.callback, auto_ack=True)
        self.channel_get.start_consuming()

    def update(self):
        i = 0
        while True:
            self.grabbed, self.frame = self.video.read()
            i += 1
            if i >= 5:
                    if self.grabbed:
                        img_str = cv2.imencode('.jpg', self.frame)[1].tobytes()
                        # threading.Thread(target=self.channel_post.basic_publish(exchange='', routing_key='test_rtsp_frames', body=img_str), args=()).start()
                        self.channel_post.basic_publish(exchange='', routing_key='test_rtsp_frames', body=img_str)
                        i = 0
            self.frame = cv2.addWeighted(self.frame, 1, self.ai_frame, 1, 0.0)

def gen(camera):
    while True:
        frame = camera.get_frame()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

class StreamView(TemplateView):
    template_name = 'stream.html'