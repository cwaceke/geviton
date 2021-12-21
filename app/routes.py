
from app import app, db
from flask import request, g, current_app, render_template, jsonify, flash, url_for, redirect,session
import json
from app.models import Data, User, Project, SurveyData
from app.forms import  RegistrationDetails,ResetEmail, ResetPassword,  RegistrationDetails, ProjectRegistrationDetails, LoginDetails, ProjectDetails, InviteUser
from werkzeug.security import generate_password_hash, check_password_hash
from flask_breadcrumbs import register_breadcrumb
from app.email import send_invite_email, send_reset_email
from app.payloadDecode import getDate, locationPin, battery, level, surveyDecode
from flask_login import login_user, current_user, logout_user, login_required
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from functools import wraps
from flask_googlemaps import Map
def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.admin != True:
            flash ("You don't have permission to access this resource.", "warning")
            return redirect(url_for('index'))
        return func(*args,**kwargs)
    return decorated_view

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
            admin=True,
            password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered', 'info')
        return redirect(url_for('login'))

    return render_template('signup.html', registration=registration)

@app.route('/signup/project/<token>', methods=['POST', 'GET'])
def signup_project(token):
    #get project name
    user_project=confirm_invite_token(token)
    #Get the project
    target_project=Project.query.filter(Project.project_name==user_project).first()

    registration=ProjectRegistrationDetails()
    #if form is submitted,  collect data and add it to db
    if request.method=='POST' and registration.validate_on_submit():
        hashed_password=generate_password_hash(request.form['password'], method='sha256')
        new_user=User(
            username=request.form['username'],
            email=request.form['email_field'],
            admin=False,
            password=hashed_password)
        new_user.projects.append(target_project)
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered', 'info')
        return redirect(url_for('login'))

    return render_template('signup_project.html', registration=registration)

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
            
            # if user exist in database than we will compare our database hased password and password coming from login form 
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


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect (url_for('index'))
    resetRequest=ResetEmail()
    if resetRequest.validate_on_submit():
        user=User.query.filter_by(email=resetRequest.email_field.data).first()
        #send the email
        if user:
            send_reset_email(user)
        flash('An email has been sent to you with a reset token.','info')
        return redirect(url_for('login'))
    return render_template('password_request.html', resetRequest=resetRequest)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect (url_for('index'))
    user=User.verify_reset_token(token)
    if user is None:
        flash('The token is invalid or expired', 'warning')
        return redirect(url_for('reset_request'))
    resetPassword=ResetPassword()  
    if resetPassword.validate_on_submit():
        hashed_password=generate_password_hash(request.form['password'], method='sha256')
        user.password=hashed_password
        db.session.commit()
        flash('Your password has been updated. You are now able to log in', 'success')
        return redirect(url_for('login'))  
    return render_template('password_reset.html', resetPassword=resetPassword)

#home page
@app.route('/')
@register_breadcrumb(app, '.', 'Home')
@login_required
def index():
    #get logged in user
    userId=current_user.id
   
    dist_projects=[r.project_name for r in Project.query.join(User.projects).filter(User.id==userId).all()]

    return render_template('index.html', dist_projects=dist_projects )

def view_prj_dlc(*args, **kwargs):
    prj_name = request.view_args['prjName']
    return [{'text': prj_name, 'url': prj_name}]

@app.route('/waterMeterWithGPS/<prjName>', methods=['POST','GET'])
@register_breadcrumb(app, '.waterMeterWithGPS', '',dynamic_list_constructor=view_prj_dlc)
@login_required
def waterGPS(prjName):
  
    #get all data with the project name we want in a list
    
    all_devices=db.session.query(Data.device_id).distinct()
    dist_devices= [r.device_id for r in all_devices.filter(Data.project_name==prjName).all()]
    return render_template('simtank.html', dist_devices=dist_devices)



@app.route('/customize', methods=['POST','GET'])
@register_breadcrumb(app, '.customize', 'Customize')
@login_required
@admin_required
def customize():
   
    project_details=ProjectDetails()
    
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
                    new_project=Project(project_name=projectName)
                    project_owner=User.query.filter_by(id=current_user.id).first()
    
                    new_project.users.append(project_owner)
                    db.session.add(new_project)
                    db.session.commit()
                    
                else:
                    flash("User not authenticated", 'danger')
                
                return render_template('index.html')

            elif (deviceType=='landSurvey'):
                base=request.url_root
                base=base[:-1]
            
                #generate a callback URL for the client to use and flash it
                message="The api callback URL is  " + base + url_for('confirmationLandSurvery', prjName=projectName)
                flash(message, 'success')

                if current_user.is_authenticated:
                    new_project=Project(project_name=projectName)
                    project_owner=User.query.filter_by(id=current_user.id).first()
                    new_project.users.append(project_owner)
                    db.session.add(new_project)
                    db.session.commit()
                    
                else:
                    flash("User not authenticated", 'danger')

                return render_template('index.html')
    return render_template('customize.html', project_details=project_details)

    
    
@app.errorhandler(401)
def unauthorized(error):
    flash('You need to be an administrator to log in to this page', 'warning')
    return redirect(url_for('login', next=request.path))


def confirm_invite_token(token, expiration=7200):
    serializer=Serializer(app.config['SECRET_KEY'])
    try:
        project=serializer.loads(token, salt=app.config['SECURITY_PASSWORD_SALT'])
    except:
        return None
    return project

@app.route('/invite_user', methods=['GET', 'POST'])
@register_breadcrumb(app, '.invite', 'invite user')
@login_required
@admin_required
def invite_user():
  
    invite_user=InviteUser()

    if request.method=='POST' and invite_user.validate_on_submit():
        #get the email of a new user
        prj=int(request.form['projects'])
        new_user_email=request.form['email']
        first_project=Project.query.filter(Project.id==prj).first()
        
        # check if email exists and then append the project name
        user=User.query.filter_by(email=new_user_email).first()
        if user:
            #add the project to their list
            user.projects.append(first_project)
            db.session.commit()
        # if not user, send invite
        else:
            send_invite_email(new_user_email, first_project.project_name)
        flash('The invite has been sent.', 'success')
        return redirect(url_for('index'))  
    return render_template('invite.html', invite_user=invite_user)
   

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
@app.route('/survey', methods=['POST','GET'])
def survey():
    addresses = SurveyData.query.all()
    add_2=db.session.query(SurveyData.device_id).distinct()
    location_dict=[]
    for add in addresses:
        icon='http://maps.google.com/mapfiles/ms/icons/green-dot.png'
        if (add.tampered==True):
            icon='http://maps.google.com/mapfiles/ms/icons/blue-dot.png'
        else:
            icon='http://maps.google.com/mapfiles/ms/icons/green-dot.png'
    
        location_data = {
            "icon": icon,
            "lat": add.latitude, 
            "lng": add.longitude,
            "infobox": add.device_id,
        }
        location_dict.append(location_data)

    mymap=Map(
        identifier="view-side",
        style="height:700px;width:100%;margin:0;",
        lat=-1.2528,
        lng=37.0724,
        fullscreenControl=False,
        markers=location_dict
    )
    
    return render_template('survey.html',mymap=mymap)
    




@app.route('/survey/confirmation/<prjName>', methods=['POST'])
def confirmationLandSurvery(prjName):
    
    content=request.json
    device_id=content['id']
    dataString=content['data']
    time=getDate()
    #get the parameters and push them to a db

    tamperPar, latPar, longPar=surveyDecode(dataString)

    newSurveyData=SurveyData(project_name=prjName,device_id=device_id, time=time,payload=dataString, tampered=tamperPar, latitude=latPar, longitude=longPar)

    db.session.add(newSurveyData)
    db.session.commit()
    
    return ('', 200)



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
    
    return ('', 200)

