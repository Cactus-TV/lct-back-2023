from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import EmailMessage
from django.views.decorators import gzip
from django.views.generic import TemplateView
from django.http import StreamingHttpResponse

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
        self.video = cv2.VideoCapture('rtsp://admin:A1234567@188.170.176.190:8027/Streaming/Channels/101?transportmode=unicast&profile=Profile_1')
        self.grabbed, self.frame = self.video.read()
        threading.Thread(target=self.update, args=()).start()

    def __del__(self):
        self.video.release()

    def get_frame(self):
        image = self.frame
        _, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

    def update(self):
        while True:
            (self.grabbed, self.frame) = self.video.read()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

class StreamView(TemplateView):
    template_name = 'stream.html'