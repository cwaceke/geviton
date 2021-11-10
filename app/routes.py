from app import app, db, mail
from flask import request, render_template, jsonify, flash, url_for, redirect,session
from datetime import datetime
from pytz import timezone
import json
from app.models import Data, User, Project
from app.forms import  RegistrationDetails,ResetEmail, ResetPassword,  RegistrationDetails, LoginDetails, ProjectDetails, InviteUser
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message


def getDate():
    nai = timezone('Africa/Nairobi')
    now_date=datetime.now().astimezone(nai)
    d= now_date.strftime("%m/%d/%y, %H:%M")
    return d


def locationPin (testString):
    polarityHex=testString[2:4]
    polarityInt=int(polarityHex, base=16)
    if (polarityInt==0):
        latitudePosition='-'
        longitudePosition='-'
    elif(polarityInt==1):
        latitudePosition="-"
        longitudePosition="+"
    elif(polarityInt==10):
        latitudePosition="+"
        longitudePosition="-"
    elif(polarityInt==11):
        latitudePosition="+"
        longitudePosition="+"
    else:
        print("Polarity not defined")
  

    # getting the latitude

    latitudeHex=testString[4:12]
    latitudeInt=int(latitudeHex,base=16)
    latitudeOriginal=float(latitudeInt/1000000)
    lat=latitudePosition+str(latitudeOriginal)

    #getting the longitude
    longitudeHex=testString[12:20]
    longitudeInt=int(longitudeHex,base=16)
    longitudeOriginal=float(longitudeInt/1000000)
    long=longitudePosition+str(longitudeOriginal) 

    return lat, long

def battery (testString):

    N=2
    length= len(testString)

    batteryhex=testString[length - N: ]
    batteryInt=int(batteryhex, base=16)
    return batteryInt

def level (testString):
    levelhex=testString[2:6]
    levelInt=int(levelhex, base=16)
    return levelInt

#signup, login and logout
@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if current_user.is_authenticated:
        return redirect (url_for('index'))

    registration=RegistrationDetails()

    #if form is submitted,  collect data and add it to db
    if request.method=='POST' and registration.validate_on_submit():
        hashed_password=generate_password_hash(request.form['password'], method='sha256')
        new_user=User(
            username=request.form['username'],
            email=request.form['email_field'],
            password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered', 'info')
        return redirect(url_for('login'))

    return render_template('signup.html', registration=registration)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect (url_for('index'))

    login=LoginDetails()

    #check if form is submitted and collect data
    if request.method=='POST' and login.validate_on_submit():
        #check if user exists
        user = User.query.filter_by(email = request.form['email_field']).first()
        if user:
            # if user exist in database than we will compare our database hased password and password come from login form 
            if check_password_hash(user.password, request.form['password']):
                # if password is matched, allow user to access and save email and username inside the session
                login_user(user, remember=True)
                return redirect(url_for('index'))

            else:
                # if password is in correct , redirect to login page
                flash('Username or Password Incorrect','warning')

                return redirect(url_for('login'))
    return render_template('login.html', login=login)
    
@app.route('/logout')
def logout():
    # Removing data from session by setting logged_flag to False.
    logout_user()
    # redirecting to home page
    return redirect(url_for('login'))

def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message('Password Reset Request', sender='noreply@gondor.com',recipients=[user.email])

    msg.body=f'''To reset your password, visit the following link:
{ url_for('reset_token', token=token, _external=True)}  


If you did not make this request then simply ignore this email and no changes will be made      
'''
    mail.send(msg)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect (url_for('index'))
    resetRequest=ResetEmail()
    if resetRequest.validate_on_submit():
        user=User.query.filter_by(email=resetRequest.email_field.data).first()
        #send the email
        send_reset_email(user)
        flash('An email has been sent to you with a reset token.','info')
        return redirect(url_for('login'))
    return render_template('password_request.html', resetRequest=resetRequest)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect (url_for('index'))
    user=User.verify_reset_token(token)
    if user is None:
        flash('The token is invalid or expired', 'warning')
        return redirect(url_for('reset_request'))
    resetPassword=ResetPassword()  
    if resetPassword.validate_on_submit():
        hashed_password=generate_password_hash(request.form['password'], method='sha256')
        password=hashed_password
        db.session.commit()
        flash('Your password has been updated. You are now able to log in', 'success')
        return redirect(url_for('login'))  
    return render_template('password_reset.html', resetPassword=resetPassword)

#home page
@app.route('/')
@login_required
def index():
    #get logged in user
    userId=current_user.id
    #get the user projects
    dist_projects=[r.project_name for r in Project.query.filter(Project.ownerId==userId).all()]

    #dist_projects= [r.project_name for r in db.session.query(Data.project_name).distinct()]
    return render_template('index.html', dist_projects=dist_projects )



@app.route('/waterMeterWithGPS/<prjName>', methods=['POST','GET'])
@login_required
def waterGPS(prjName):
  
    #get all data with the project name we want in a list
    
    all_devices=db.session.query(Data.device_id).distinct()
    dist_devices= [r.device_id for r in all_devices.filter(Data.project_name==prjName).all()]
    return render_template('simtank.html', dist_devices=dist_devices)

def send_invite_email(user, project):
    msg=Message('Project Invite', sender='noreply@gondor.com',recipients=[user.email])

    msg.body=f'''You have been invited to view the project,{project}. Visit the following link to create your account:
{ url_for('signup', _external=True)}  


If you do not know anything about this project, then simply ignore this email and no changes will be made      
'''
    mail.send(msg)

@app.route('/customize', methods=['POST','GET'])
@login_required
def customize():
   
    project_details=ProjectDetails()
    
    invite_user=InviteUser()
    
    if request.method=='POST':
            
        if project_details.validate_on_submit():
                #getting value from the form 
            deviceType=request.form['device_type'] 
            projectName=request.form['project_name']
        
            if (deviceType=='waterLevelGPS'):
                base=request.url_root
                base=base[:-1]
               

                #generate a callback URL for the client to use and flash it
                message="The api callback URL is  " + base + url_for('confirmationWaterGPS', prjName=projectName)
                flash(message, 'success')

                #add the project to the db and its related 
                if current_user.is_authenticated:
                
                    new_project=Project(project_name=projectName,ownerId=current_user.id)
                    db.session.add(new_project)
                    db.session.commit()
                    
                else:
                    flash("User not authenticated", 'danger')
                
                return render_template('index.html')
                    #getting the base URL
        


    return render_template('customize.html', project_details=project_details, invite_user=invite_user)

app.route('/invite_user', methods=['GET', 'POST'])
def invite_user():
 
    #check the role of the sender
    #Get the project that the admin is adding them to from dropdown
    resetPassword=ResetPassword()  
    if resetPassword.validate_on_submit():
        hashed_password=generate_password_hash(request.form['password'], method='sha256')
        password=hashed_password
        db.session.commit()
        flash('Your password has been updated. You are now able to log in', 'success')
        return redirect(url_for('login'))  
    return render_template('password_reset.html', resetPassword=resetPassword)
   

@app.route('/update')
def update():
    dist_projects= [r.project_name for r in db.session.query(Data.project_name).distinct()]
    return render_template('update.html', dist_projects=dist_projects )

@app.route('/delete/<prjName>', methods=['POST','GET'])
def deleteProject(prjName):
    project=Data.query.filter_by(project_name=prjName).all()
    print (project)

    if project:
        for project_data in project:
            db.session.delete(project_data)
            db.session.commit()
        return redirect('/update')
        
    return redirect('/')



@app.route('/test', methods=['POST','GET'])
def test():
    dist_devices= [r.device_id for r in db.session.query(Data.device_id).distinct()]
    return render_template('test.html', dist_devices=dist_devices)

@app.route('/process', methods=['POST','GET'])
def process():
    if request.method== 'POST':
        device=request.form['device']
        
        if device:
            data=Data.query.filter_by(device_id=device).first()
            #get location data
            locData=Data.query.order_by(Data.time.desc()).filter(Data.device_id==device).filter (Data.latitude.isnot(None)).first()
            try:

                longCurrent=locData.longitude

                latCurrent=locData.latitude
            except:
                longCurrent=36.817223
                latCurrent=-1.286389

        #get most recent water level data
            levelData=Data.query.order_by(Data.time.desc()).filter(Data.device_id==device).filter(Data.level.isnot(None)).first()

            try:
                levelCurrent=levelData.level
              
            except:
                levelCurrent=1000


            dataDict={"device":data.device_id,"time":data.time,"data":data.payload,"latitude":latCurrent,"longitude":longCurrent,"level":levelCurrent,"battery":data.battery}

            dataJson=json.dumps(dataDict)
            

            return jsonify(dataDict)
    return jsonify({'error' : 'Missing data!'})

    
@app.route('/device/<device_id>')
def device(device_id):
    
    data=Data.query.order_by(Data.time.desc()).filter_by(device_id=device_id).limit(10)
    
    return render_template('device.html',data=data)



@app.route('/confirmation/waterLevelGPS/<prjName>', methods=['POST'])
def confirmationWaterGPS(prjName):

    #use the project name to get a user id
    userId=Project.query.filter_by(project_name=prjName).first()
    if not userId:
        flash ("Please check the callback address",'danger')
    
    
    content=request.json #grab the json data
    device_id=content['id']
    dataString=content['data']
    time = getDate()
    typeHex=dataString[:2]
    
    if (typeHex=="1f"):
        deviceLat, deviceLong=locationPin(dataString)
        deviceBat=battery(dataString)
        new_data=Data(project_name=prjName,device_id=device_id, time=time,payload=dataString, battery=deviceBat,latitude=deviceLat, longitude=deviceLong)

    elif (typeHex=="2f"):
        waterLevel=level(dataString)
        deviceBat=battery(dataString)
        new_data=Data(project_name=prjName,device_id=device_id, time=time,payload=dataString, battery=deviceBat,level=waterLevel)
    elif (typeHex=="4f"):
        waterLevel=level(dataString)
        deviceBat=battery(dataString)
        new_data=Data(project_name=prjName,device_id=device_id, time=time,payload=dataString, battery=deviceBat,level=waterLevel)
       
    else:
        deviceBat=battery(dataString)
        new_data=Data(project_name=prjName,device_id=device_id, time=time, payload=dataString, battery=deviceBat)



    db.session.add(new_data)
    db.session.commit()
    print (new_data)
    return ('', 200)

