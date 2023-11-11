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
from dotenv import load_dotenv

load_dotenv()
MQ_POST_ARR = os.environ.get('RABBITMQ_QUEUE_NAME_POST').split("|")
MQ_GET_ARR = os.environ.get('RABBITMQ_QUEUE_NAME_GET').split("|")
MQ_LOGIN = os.environ.get('RABBITMQ_LOGIN')
MQ_PASSWORD = os.environ.get('RABBITMQ_PASSSWORD')
MQ_PORT = os.environ.get('RABBITMQ_PORT')
MQ_HOST = os.environ.get('RABBITMQ_HOST')

is_changed = False

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
        return HttpResponse(get_one(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'stream.html')

def frame_detected(request):
    try:
        cam = VideoCamera()
        return HttpResponse(get_one_detected(cam), content_type="multipart/x-mixed-replace;boundary=frame")
    except:
        pass
    return render(request, 'stream.html')

class VideoCamera(object):
    def __init__(self):
        self.video = None
        credentials = pika.PlainCredentials(MQ_LOGIN, MQ_PASSWORD)
        parameters = pika.ConnectionParameters(port=MQ_PORT, host=MQ_HOST, credentials=credentials)

        self.connection_get_arr = list()
        self.connection_post_arr = list()
        self.channel_post_arr = list()
        self.channel_get_arr = list()

        self.last_frame_number = 0

        global is_changed
        is_changed = False

        for i in MQ_GET_ARR:
            self.connection_get_arr.append(pika.BlockingConnection(parameters))
            self.channel_get_arr.append(self.connection_get_arr[-1].channel())
            self.channel_get_arr[-1].queue_declare(queue=i, durable=True)
        for i in MQ_POST_ARR:
            self.connection_post_arr.append(pika.BlockingConnection(parameters))
            self.channel_post_arr.append(self.connection_post_arr[-1].channel())
            self.channel_post_arr[-1].queue_declare(queue=i, durable=True)


        self.init_camera()
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
        
    def init_camera(self):
        cameras_arr = list(Stream.objects.filter(Q(is_active=True)))
        if len(cameras_arr):
            camera = list(Stream.objects.filter(Q(is_active=True)))[0]
        else:
            camera = list(Stream.objects.all())[0]
        login = camera.username
        password = camera.password
        url = camera.url

        self.video = cv2.VideoCapture(f'rtsp://{login}:{password}{url}', cv2.CAP_ANY)
        
    
    def callback(self, ch, method, properties, body):
        if int(ch) - 1 >= self.last_frame_number:
            nparr = np.frombuffer(body, np.uint8)
            self.ai_frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            self.last_frame_number = int(ch) - 1

    def get_queue(self, frame_num, queue_name, chanel):
        chanel.basic_consume(queue=queue_name, on_message_callback=self.callback, auto_ack=True, consumer_tag=frame_num)
        chanel.start_consuming()
    
    def post_queue(self, queue_name, chanel, img_str):
        chanel.basic_publish(exchange='', routing_key=queue_name, body=img_str)

    def update(self):
        i = 0
        j = 0
        while True:
            self.grabbed, self.frame = self.video.read()
            if self.grabbed:
                self.frame_2 = self.frame
                i += 1
                if i % (25//len(MQ_POST_ARR)) == 0:
                    if j == len(MQ_POST_ARR):
                        self.last_frame_number = 0
                        i = 0
                        j = 0
                        continue

                    img_str = cv2.imencode('.jpg', self.frame)[1].tobytes()
                    threading.Thread(target=self.post_queue, kwargs={'queue_name': MQ_POST_ARR[j], 'chanel': self.channel_post_arr[j], 'img_str': img_str}).start()
                    j += 1

                if self.frame.shape == self.ai_frame.shape:
                    self.frame = cv2.addWeighted(self.frame, 1, self.ai_frame, 1, 0.0)

def gen(camera):
    while True:
        frame = camera.get_frame()
        global is_changed
        if is_changed:
            camera.init_camera()
            is_changed = False

        if frame:
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            
def get_one(camera):
    frame = camera.get_frame_unmodified()
    if frame:
        return (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
    
def get_one_detected(camera):
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
            global is_changed
            is_changed = True
            streams[0].save()

            return Response(status.HTTP_200_OK)
        
        except:
            return Response({'error': 'smth bad happened'}, status.HTTP_405_METHOD_NOT_ALLOWED)