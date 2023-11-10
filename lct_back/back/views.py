from django.shortcuts import render
from django.views.decorators import gzip
from django.views.generic import TemplateView
from django.http import StreamingHttpResponse, HttpResponse
from django.db.models import Q
from .models import *
from .serializers import *
import pika
import numpy as np
import cv2
import threading
import os
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# добавить поддержку нескольких камер одновременно
MQ_POST_ARR = [i+'_post' for i in os.environ.get('RABBITMQ_QUEUE_NAME').split("|")]
MQ_GET_ARR = [i+'_get' for i in os.environ.get('RABBITMQ_QUEUE_NAME').split("|")]
# MQ_POST_ARR = ['test_rtsp_get_1', 'test_rtsp_get_2']
# MQ_GET_ARR = ['test_rtsp_post_1', 'test_rtsp_post_2']

MQ_LOGIN = os.environ.get('RABBITMQ_LOGIN')
MQ_PASSWORD = os.environ.get('RABBITMQ_PASSSWORD')
MQ_IP = os.environ.get('RABBITMQ_IP')
MQ_PORT = os.environ.get('RABBITMQ_PORT')
MQ_HOST = os.environ.get('RABBITMQ_HOST')

@gzip.gzip_page
def transmition(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'stream.html')

def frame(request):
    try:
        cam = VideoCamera()
        return HttpResponse(gen_one(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'stream.html')

#to capture video class
class VideoCamera(object):
    def __init__(self):
        # credentials = pika.PlainCredentials('test_user', 'test')
        # parameters = pika.ConnectionParameters('localhost', 5672, 'test_host', credentials)
        credentials = pika.PlainCredentials(MQ_LOGIN, MQ_PASSWORD)
        parameters = pika.ConnectionParameters(MQ_IP, MQ_PORT, MQ_HOST, credentials)

        self.connection_get_arr = list()
        self.connection_post_arr = list()
        self.channel_post_arr = list()
        self.channel_get_arr = list()

        self.last_frame_number = 0

        for i in MQ_GET_ARR:
            self.connection_get_arr.append(pika.BlockingConnection(parameters))
            self.channel_get_arr.append(self.connection_get_arr[-1].channel())
            self.channel_get_arr[-1].queue_declare(queue=i, durable=True)
        for i in MQ_POST_ARR:
            self.connection_post_arr.append(pika.BlockingConnection(parameters))
            self.channel_post_arr.append(self.connection_post_arr[-1].channel())
            self.channel_post_arr[-1].queue_declare(queue=i, durable=True)

        # self.channel_post.queue_declare(queue='test_rtsp_frames', durable=True)
        # self.channel_get.queue_declare(queue='test_ai_detected_frames', durable=True)

        cameras_arr = list(Stream.objects.filter(Q(is_active=True)))
        if len(cameras_arr):
            camera = list(Stream.objects.filter(Q(is_active=True)))[0]
        else:
            camera = list(Stream.objects.all())[0]
        login = camera.username
        password = camera.password
        url = camera.url

        self.video = cv2.VideoCapture(f'rtsp://{login}:{password}{url}')
        # self.video = cv2.VideoCapture('rtsp://admin:A1234567@188.170.176.190:8027/Streaming/Channels/101?transportmode=unicast&profile=Profile_1')
        self.grabbed, self.frame = self.video.read()
        self.frame_2 = self.frame
        h, w ,ch = self.frame.shape
        self.ai_frame = np.zeros((h, w, ch), dtype=np.uint8)
        threading.Thread(target=self.update, args=()).start()

        for i in range(len(MQ_GET_ARR)):
            threading.Thread(target=self.get_queue, kwargs = {'frame_num': str(i), 'queue_name': MQ_GET_ARR[i], 'chanel': self.channel_get_arr[i]}).start()

    def __del__(self):
        for i in self.connection_get_arr:
            i.close()
        for i in self.connection_post_arr:
            i.close()
        if self.video:
            self.video.release()

    def get_frame(self):
        image = self.frame
        if self.grabbed:
            jpeg = cv2.imencode('.jpg', image)[1]
            return jpeg.tobytes()
        else:
            return 0
        
    def get_frame_unmodified(self):
        image = self.frame_2
        if self.grabbed:
            jpeg = cv2.imencode('.jpg', image)[1]
            return jpeg.tobytes()
        else:
            return 0
    
    def callback(self, ch, method, properties, body):
        if int(ch) - 1 >= self.last_frame_number:
            # for i in range(0,int(ch)-1):
            #     self.channel_get.queue_purge(MQ_GET_ARR[i])
            nparr = np.frombuffer(body, np.uint8)
            self.ai_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            self.last_frame_number = int(ch) - 1

    def get_queue(self, frame_num, queue_name, chanel):
        chanel.basic_consume(queue=queue_name, on_message_callback=self.callback, auto_ack=True, consumer_tag=frame_num)
        chanel.start_consuming()
    
    def post_queue(self, queue_name, chanel, img_str):
        chanel.basic_publish(exchange='', routing_key=queue_name, body=img_str)

    # def connect(self):
    #     credentials = pika.PlainCredentials('test_user', 'test')
    #     parameters = pika.ConnectionParameters('localhost', 5672, 'test_host', credentials)
    #     # credentials = pika.PlainCredentials(MQ_LOGIN, MQ_PASSWORD)
    #     # parameters = pika.ConnectionParameters(MQ_HOST, MQ_PORT, MQ_HOST, credentials)

    #     self.connection_get = pika.BlockingConnection(parameters)
    #     self.connection_post = pika.BlockingConnection(parameters)
    #     self.channel_post = self.connection_post.channel()
    #     self.channel_get = self.connection_get.channel()

    #     for i in MQ_GET_ARR:
    #         self.channel_get.queue_declare(queue=i, durable=True)
    #     for i in MQ_POST_ARR:
    #         self.channel_post.queue_declare(queue=i, durable=True)

    #     for i in range(len(MQ_GET_ARR)):
    #         threading.Thread(target=self.get_queue, kwargs = {'frame_num': str(i), 'queue_name': MQ_GET_ARR[i]}).start()
    #     # threading.Thread(target=self.get_queue, args=('test_ai_detected_frames')).start()

    def update(self):
        i = 0
        j = 0
        while True:
            self.grabbed, self.frame = self.video.read()
            self.frame_2 = self.frame
            i += 1
            if i % (25//len(MQ_POST_ARR)) == 0:
                if j == len(MQ_POST_ARR):
                    self.last_frame_number = 0
                    # for name in MQ_POST_ARR:
                    #     self.channel_post.queue_purge(name)
                    i = 0
                    j = 0
                    continue

                if self.grabbed:
                    img_str = cv2.imencode('.jpg', self.frame)[1].tobytes()
                    threading.Thread(target=self.post_queue, kwargs={'queue_name': MQ_POST_ARR[j], 'chanel': self.channel_post_arr[j], 'img_str': img_str}).start()
                    # self.channel_post.basic_publish(exchange='', routing_key='test_rtsp_frames', body=img_str)
                j += 1

            if self.grabbed:
                self.frame = cv2.addWeighted(self.frame, 1, self.ai_frame, 1, 0.0)

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            
def gen_one(camera):
    frame = camera.get_frame()
    if frame:
        return (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            
            
class StreamView(TemplateView):
    template_name = 'stream.html'


class StreamAPIGet(generics.ListAPIView):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [AllowAny]


class StreamAPICreate(generics.CreateAPIView):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [AllowAny]


class StreamAPIUpdate(generics.RetrieveUpdateDestroyAPIView):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [AllowAny]


class FrameCreateAPI(APIView):
    permission_classes = [AllowAny]
        
    def post(self, request):
        try:
            file = request.FILE['myfile']
            Frame.objects.create(frame=request.FILES[file])

            return Response(status.HTTP_200_OK)
        except:
            return Response({'error': 'smth bad happened'}, status.HTTP_405_METHOD_NOT_ALLOWED)
        

class StreamUpdateIsActiveAPI(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            uid = request.data['uid']

            active_streams = list(Stream.objects.filter(Q(is_active=True)))
            streams = list(Stream.objects.filter(Q(uid=uid)))
            if len(streams) == 0:
                return Response(status.HTTP_404_NOT_FOUND)
            for i in active_streams:
                i.is_active=False
                i.save()
            streams[0].is_active = True
            streams[0].save()

            return Response(status.HTTP_200_OK)
        
        except:
            return Response({'error': 'smth bad happened'}, status.HTTP_405_METHOD_NOT_ALLOWED)