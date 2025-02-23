import RPi.GPIO as GPIO
import Adafruit_DHT
import spidev
import time
import requests
import uuid
import cv2
import datetime

#------------sensor control------------------

#set GPIO Pin
Sensor = Adafruit_DHT.DHT11

light_pin = 27
outdht_pin = 2
motor_pin = 4
humider_pin = 17

#spi setting (for soil stove sensor)
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz = 1000000

#GPIO mode setting
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

#PIN set
GPIO.setup(humider_pin, GPIO.OUT)
GPIO.setup(light_pin, GPIO.OUT)
GPIO.setup(motor_pin, GPIO.OUT)

#light control fuction

def turn_on_light():
    GPIO.output(light_pin, GPIO.LOW)
    print("조명이 켜졌습니다.")
    #light_flag = 1

def turn_off_light():
    GPIO.output(light_pin, GPIO.HIGH)
    print("조명이 꺼졌습니다.")
    #light_flag = 0
 
 
#humider control
def turn_on_humider():
    GPIO.output(humider_pin, GPIO.LOW)
    print("가습시가 켜졌습니다.")
    
def turn_off_humider():
    GPIO.output(humider_pin, GPIO.HIGH)
    print("가습기가 꺼졌습니다.")


#soil stove sensor control
def readChannel(channel):
        val = spi.xfer2([1,(8+channel<<4), 0])
        data = ((val[1]&3) << 8) +val[2]
        return data
def convertPercent(data):
        return 100.0 -round(((data*100)/float(1023)),1)


#water_pumb control

#standard_soil = 4 #remove

def motor_control(val , standard):
    if(val < standard):
        GPIO.output(motor_pin, GPIO.LOW)
        time.sleep(2)
        GPIO.output(motor_pin, GPIO.HIGH)

#turn_off_light()
turn_off_humider()
GPIO.output(motor_pin, GPIO.HIGH)

print('-----------------------------')


while True :
    
    #GPIO.output(motor_pin, GPIO.LOW)
#-----------------sever-----------------
#user booth setting value get
    
    #remove
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print("현재 시간:", formatted_time)
    
    url = 'http://3.38.62.245:8080/device/load/one?deviceId=1'
    r = requests.get(url)

# get user's setting data from server
    new_temp = r.json()["temperature"]
    new_humi = r.json()["humidity"]
    new_soil = r.json()["soilMoisture"]

#comprison setting data
    standard_temp = new_temp
    standard_humi = new_humi
    standard_soil = new_soil

    print(new_temp,new_humi,new_soil) #remove


#image capture and store
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    ret, frame = cap.read()
    if ret:
        cv2.imwrite("server3.jpg", frame)
        print("이미지를 저장했습니다.")#remove
    
    cap.release()



#image send server code
    deviceId = "1234"
    url = 'http://3.38.62.245:8080/datain/image?deviceId=' + deviceId
    boundary = uuid.uuid4().hex

    headers = {'Content-Type': 'multipart/form-data; boundary=' + boundary}

    image_path = '/home/pi/server3.jpg'
    files ={'file':open(image_path,'rb')}

    r = requests.post(url,files=files)
    print(r.text) #remove
    
    
    humi, temp = Adafruit_DHT.read_retry(Sensor, outdht_pin)

    if humi is not None and temp is not None:
        print('temp = {0:0.1f} humi = {1:0.1f}%'.format(temp,humi))
    

    
#soil sensor read and print code
    soilMoisture = readChannel(0) #spi 통신으로 읽어온 토양습도값 (0~1024)
    soilMoistrue_percent = convertPercent(soilMoisture) #토양습도값을 퍼센트로 변환
    print('soil humid =',soilMoistrue_percent,'%') #remove

    standard_soil1 = 60
#물주기 제어 코드
    motor_control(soilMoistrue_percent, standard_soil1) #현재 토양 습도가 설정값보다 낮으면 물주기

#사용자 설정 온도값에 따른 조명 제어   
    if temp > standard_temp:
        turn_off_light()
    else :
        turn_on_light()




#-------------server---------------
#send data to server

    data_url = 'http://3.38.62.245:8080/datain/hourlog'

    data = {
        "deviceId" : 1234,
        "temperature": temp,
        "humidity": humi ,
        "soilMoisture": soilMoistrue_percent
    }
    response = requests.post(data_url, json=data)
    print(response.text)

    
    #remove
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    print("현재 시간:", formatted_time)
    print('-----------------------------')
    
    time.sleep(600)
    



'''
#사용자 설정 습도값에 따른 가습기 제어
    if humi < standard_humi:
        turn_on_humider()
    else :
        turn_off_humider()
'''
