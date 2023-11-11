import cv2

#print("Before URL")
cap = cv2.VideoCapture('rtsp://admin:A1234567@188.170.176.190:8030/Streaming/Channels/101?transportmode=unicast&profile=Profile_1')
#print("After URL")

while True:

    #print('About to start the Read command')
    ret, frame = cap.read()
    #print('About to show frame of Video.')
    cv2.imshow("Capturing",frame)
    #print('Running..')

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()