from flask import Flask, render_template, Response, request,send_from_directory
import cv2
import numpy as np
import os
import face_recognition
import csv
from datetime import datetime
import time

app = Flask(__name__)

path = 'facial-recognition-outpass-management-system-main/images'

images = []
classNames = []
myList = os.listdir(path)
print(myList)
for idx, cl in enumerate(myList, start=1):
    curImg = cv2.imread(f'{path}/{cl}')
    images.append(curImg)
    classNames.append(os.path.splitext(cl)[0])


cap = cv2.VideoCapture(0)
print("Is the camera opened?", cap.isOpened())

encodeListKnown = []

threshold = 0.4

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(img)
        
        if face_locations:
            encode = face_recognition.face_encodings(img, face_locations)[0]
            encodeList.append(encode)
        else:
            print("No faces found in the image:", img)

    return encodeList



# Call findEncodings to populate encodeListKnown
encodeListKnown = findEncodings(images)

def recognize_face(img):
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    recognized_faces = []

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

        matchIndex = np.argmin(faceDis)

        if matches[matchIndex] and faceDis[matchIndex] < threshold:
            name = classNames[matchIndex].upper()
        else:
            name = 'Unknown'

        recognized_faces.append((name, faceLoc))
        print(recognized_faces)

    return recognized_faces

@app.route('/')
def home():
    return render_template('home.html') 
@app.route('/caretaker',methods=['POST','GET'])
def index():
    return render_template('index.html')
@app.route('/main-gate',methods=['POST','GET'])
def maingate():
    return render_template('security.html')


@app.route('/upload', methods=['POST'])
def upload():
    if request.method == 'POST':
        _, img = cap.read()
        recognized_faces = recognize_face(img) 
        print(recognized_faces)   
        students_path='facial-recognition-outpass-management-system-main/facial-recognition-outpass-management-system-main/static/student_details.csv'
        details=None
        for i,j in recognized_faces:
            idx=i
            j=j
            with open(students_path,'r') as file:
                reader=csv.DictReader(file)
                detected=False
                for i in reader:
                    print(i)
                    if(i['id']==idx):
                        details=i
                        detected=True
                        print(f'details{details}')
                if(detected != True):
                    return render_template('noface.html')
                   
        return render_template('issue.html', recognized_faces=recognized_faces,details=details)
@app.route('/idnumber',methods=['POST'])
def idnum():
    det=None
    idx=request.form.get('id')
    students_path='static/student_details.csv'
    with open(students_path,'r') as file1:
            reader1=csv.DictReader(file1)
            for i in reader1:
                if(i['id']==idx):
                    det=i
    return render_template('issue.html', details=det)
@app.route('/fetch',methods=['POST'])
def fetch():
    det=None
    idx=request.form.get('id')
    outpass_path='static/outpass.csv'
    flag=False
    out=False
    in_time=False
    with open(outpass_path, 'r') as file1:
        reader1 = csv.DictReader(file1)
        for i in reader1:
            if (i['outpassid'] == idx or i['id'] == idx):
                det = i
                flag=True
                if (det['outtime'] != 'Still in the Campus') and (det['intime'] != 'Still in a Leave'):
                    return render_template('failure.html', details=det)

                if det['outtime'] == 'Still in the Campus':
                    out = True

                if det['intime'] == 'Still in a Leave':
                    in_time = True
        if(not flag):
            return render_template('failure.html',idx=idx)
    return render_template('inandout.html', details=det,out=out,in_time=in_time)
def generate_unique_id(student_id):
    timestamp = int(time.time())
    unique_id = f"NUZOP{timestamp}"
    return unique_id
outpass_path='static/outpass.csv'
@app.route('/detail', methods=['POST'])
def detail():
    reason = request.form.get('reason')
    idx = request.form.get('id')
    name = request.form.get('name')
    branch = request.form.get('branch')
    year = request.form.get('year')
    issue_time = str(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
    date = str(datetime.now().date())
    outtime='Still in the Campus'
    intime='-'
    outpassid=generate_unique_id(idx)
    # msg=f'''Dear {name},
    # Your Outpass is Issued Succesfully and Your Outpass ID is {outpassid}
    # Note this ID you need to go tell this at Main Gate While you are Leaving
    # and Entering into the Campus
    # Thank You and Take Care
    # '''
    # SendEmail(idx,msg,outpassid)

    # Writing to the file

    with open(outpass_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([idx, name, branch, year, issue_time,outtime,date,reason,intime,outpassid])

    # Reading from the file
    with open(outpass_path, 'r', newline='') as file:
        reader = csv.reader(file)
        issued_outpasses = list(reader)  # Convert the reader to a list

    return render_template('success.html', issued_outpasses=issued_outpasses,outpassid=outpassid)

@app.route('/security', methods=['POST', 'GET'])
def security():
    intime = "Still in a Leave"
    idx = None
    idx = request.form.get('id')
    status = request.form.get('status')
    print(status)
    if status == '1':
        outpass_path='static/outpass.csv'
        outtime = str(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        with open(outpass_path, 'r', newline='') as file:
            reader = csv.reader(file)
            rows = []
            for row in reader:
                if row[0] == idx: 
                    print(row)
                    row[5] = outtime
                    row[8] ='Still in a Leave' 
                rows.append(row)
    elif status == '2':
        outpass_path='static/outpass.csv'
        intime = str(datetime.now().strftime('%d-%m-%Y %H:%M:%S'))
        with open(outpass_path, 'r', newline='') as file:
            reader = csv.reader(file)
            rows = []
            for row in reader:
                if row[0] == idx: 
                    print(row)
                    row[8] = intime  
                rows.append(row)
    else:
        print('Gadbad hai bhai idhar security ke paas')

    with open(outpass_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)
    return render_template('success.html', issued_outpasses=rows,status=status)
@app.route('/download_csv')
def download_csv():
    directory = 'static'
    filename = 'outpass.csv'
    return send_from_directory(directory, filename, as_attachment=True)


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            break

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')





if __name__ == '__main__':
    app.run(debug=True)
    