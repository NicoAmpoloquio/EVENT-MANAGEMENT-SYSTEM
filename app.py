import mysql.connector,sys
from mysql.connector import Error
from flask import Flask, request, jsonify, render_template,redirect, url_for
#from random import randint
#import matplotlib.pyplot as plt
#import datetime


app = Flask(__name__)


#checking is the participant is already registered or not/ for error handling about the requirements
@app.route('/',methods=['GET', 'POST'])
def renderLoginPage():
    events = runQuery("SELECT * FROM events")
    branch =  runQuery("SELECT * FROM branch")
    if request.method == 'POST':
        Name = request.form['FirstName'] + " " + request.form['LastName']
        Mobile = request.form['MobileNumber']
        Branch_id = request.form['Branch']
        Event = request.form['Event']
        Email = request.form['Email']

        if len(Mobile) != min(11, len(Mobile)):
            return render_template('loginfail.html',errors = ["Invalid Mobile Number!"])

        if Email[-4:] != '.com':
            return render_template('loginfail.html', errors = ["Invalid Email!"])

        if len(runQuery("SELECT * FROM participants WHERE event_id={} AND mobile={}".format(Event,Mobile))) > 0 :
            return render_template('loginfail.html', errors = ["Student already Registered for the Event!"])
        
        if len(runQuery("SELECT * FROM participants WHERE event_id={} AND mobile={}".format(Event, Mobile))) > 0:
            return redirect(url_for('renderLoginPage', errors=["Student already Registered for the Event!"]))

        runQuery("INSERT INTO participants(event_id,fullname,email,mobile,college,branch_id) VALUES({},\"{}\",\"{}\",\"{}\",\"COEP\",\"{}\");".format(Event,Name,Email,Mobile,Branch_id))

        return render_template('index.html',events = events,branchs = branch,errors=["Succesfully Registered!"])

    return render_template('index.html',events = events,branchs = branch)
    

#login fail message
@app.route('/loginfail',methods=['GET'])
def renderLoginFail():
    return render_template('loginfail.html')

#admin login
@app.route('/admin', methods=['GET', 'POST'])
def renderAdmin():
    if request.method == 'POST':
        UN = request.form['username']
        PS = request.form['password']

        cred = runQuery("SELECT * FROM admin")
        print(cred)
        for user in cred:
            if UN==user[0] and PS==user[1]:
                return redirect('/eventType')

        return render_template('admin.html',errors=["Wrong Username/Password"])

    return render_template('admin.html')    

#saving forms
@app.route('/eventType',methods=['GET','POST'])
def getEvents():
    eventTypes = runQuery("SELECT *,(SELECT COUNT(*) FROM participants AS P WHERE T.type_id IN (SELECT type_id FROM events AS E WHERE E.event_id = P.event_id ) ) AS COUNT FROM event_type AS T;") 
    events = runQuery("SELECT event_id,event_title,(SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id ) AS count FROM events AS E;")
    types = runQuery("SELECT * FROM event_type;")
    location = runQuery("SELECT * FROM location")

    if request.method == "POST":
        try:

            Name = request.form["newEvent"]
            fee=request.form["Fee"]
            participants = request.form["maxP"]
            Type=request.form["EventType"]
            Location = request.form["EventLocation"]
            Date = request.form['Date']
            runQuery("INSERT INTO events(event_title,event_price,participants,type_id,location_id,date) VALUES(\"{}\",{},{},{},{},\'{}\');".format(Name,fee,participants,Type, Location,Date))

        except:
            EventId=request.form["EventId"]
            runQuery("DELETE FROM events WHERE event_id={}".format(EventId))

    return render_template('events.html',events = events,eventTypes = eventTypes,types = types,locations = location) 

@app.route('/eventinfo')
def rendereventinfo():
    events=runQuery("SELECT *,(SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id ) AS count FROM events AS E LEFT JOIN event_type USING(type_id) LEFT JOIN location USING(location_id);")

    return render_template('events_info.html',events = events)

#selecting/viewing participant/s
@app.route('/participants', methods=['GET', 'POST'])
def renderParticipants():
    events = runQuery("SELECT * FROM events;")

    if request.method == "POST":
        Event = request.form.get('Event')

        if 'extract_all' in request.form:
            participants = runQuery("SELECT p.p_id, p.fullname, p.mobile, p.email, e.event_title FROM participants p INNER JOIN events e ON p.event_id = e.event_id;")
            event_counts = runQuery("SELECT event_id, COUNT(*) FROM participants GROUP BY event_id;")
            event_id_to_count = {event_id: count for event_id, count in event_counts}
            event_labels = [event[1] for event in events]
            event_data = [(event_id_to_count.get(event[0], 0) / len(participants)) * 100 for event in events]
            
            return render_template('participants.html', events=events, participants=participants, event_labels=event_labels, event_data=event_data)

        participants = runQuery("SELECT p_id, fullname, mobile, email FROM participants p INNER JOIN events e ON p.event_id = e.event_id WHERE p.event_id={};".format(Event))
        return render_template('participants.html', events=events, participants=participants)

    return render_template('participants.html', events=events)

#removing participants
@app.route('/removeParticipant', methods=['POST'])
def removeParticipant():
    if request.method == 'POST':
        participant_id = request.form['participant_id']

        runQuery("DELETE FROM participants WHERE p_id={}".format(participant_id))
        return redirect('/participants')


def runQuery(query):
    
    try:
        db = mysql.connector.connect( host='localhost',database='event_mgmt',user='root',password='Nico@2003')

        if db.is_connected():
            print("Connected to MySQL, running query: ", query)
            cursor = db.cursor(buffered = True)
            cursor.execute(query)
            db.commit()
            res = None
            try:
                res = cursor.fetchall()
            except Exception as e:
                print("Query returned nothing, ", e)
                return []
            return res

    except Exception as e:
        print(e)
        return []

    db.close()

    print("Couldn't connect to MySQL")
    return None


if __name__ == "__main__":
    app.run() 
