from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
from flask_session import Session
from otp import genotp
from cmail import send_mail
from stoken import entoken,detoken
import mysql.connector
from io import BytesIO
import flask_excel as excel
import re

app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
app.secret_key='kishore@07#'
Session(app)
excel.init_excel(app)
#database connection
mydb=mysql.connector.connect(user='root',host='localhost',password='admin',db='snmp')

@app.route("/")
def home():
    return render_template("welcome.html")

@app.route("/register",methods=['GET','POST'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(email) from users where email=%s',[email])
        emailcount=cursor.fetchone()
        print(type(emailcount))
        if emailcount[0]==0:
            otp=genotp() #original otp
            print(otp)
            userdata={'user_name':username,'user_email':email,'user_password':password,'otp':otp}
            subject=f'Verification mail for SNM project'
            body=f'OTP for SNM Register verify {otp}'
            send_mail(to=email,subject=subject,body=body)
            flash('The OTP has  been sent to given Email')
            return redirect(url_for('otpverify',user_data=entoken(data=userdata)))
        elif emailcount[0]==1:
            flash('Email already existed')
        else:
            return f'something went wrong'

    return render_template('register.html')

@app.route('/otpverify/<user_data>',methods=['GET','POST'])
def otpverify(user_data):
    if request.method=='POST':
        userotp=request.form['userotp']#user given otp
        # check weather the given otp is right or wrong
        duser_data=detoken(data=user_data) #decrypted
        if duser_data['otp']==userotp:
            cursor=mydb.cursor()
            cursor.execute('insert into users(username,email,password) values(%s,%s,%s)',[duser_data['user_name'],duser_data['user_email'],duser_data['user_password']])
            mydb.commit()
            cursor.close()
            flash('Details registered successfully')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP')
    return render_template('otpverify.html')

@app.route("/login",methods=['GET','POST']) 
def login():
    if request.method=='POST':
        useremail=request.form['email']
        userpassword=request.form['pwd']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(email) from users where email=%s',[useremail])
        count_email=cursor.fetchone()
        if count_email[0]==1:
            cursor.execute('select password from users where email=%s',[useremail])
            stored_password=cursor.fetchone()
            if stored_password[0]==userpassword:
                session['user']=useremail
                print(session)
                return redirect(url_for('dashboard'))
            else:
                flash('password wrong')
                return redirect(url_for('login'))
        elif count_email[0]==0:
            flash('Email not found')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if request.method=='POST':
        title=request.form['title']
        description=request.form['description']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into notes(title,description,added_by) values(%s,%s,%s)',[title,description,session.get('user')])
        mydb.commit()
        cursor.close()
        flash(f'notes {title} added successfully')
        return redirect(url_for('viewallnotes'))
    return render_template('addnotes.html')

@app.route('/viewallnotes')
def viewallnotes():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select nid,title,created_at from notes where added_by=%s',[session.get('user')])
    allnotesdata=cursor.fetchall()
    print(allnotesdata)

    return render_template('viewallnotes.html',allnotesdata=allnotesdata) 

@app.route('/viewnotes<nid>')
def viewnotes(nid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from notes where nid=%s and added_by=%s',[nid,session.get('user')])
    notesdata=cursor.fetchone()
    print(notesdata)
    return render_template('viewnotes.html',notesdata=notesdata)

@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from notes where nid=%s and added_by=%s',[nid,session.get('user')])
    notesdata=cursor.fetchone()
    if request.method=='POST':
        u_title=request.form['title']
        u_description=request.form['description']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('update notes set title=%s,description=%s where nid=%s and added_by=%s',[u_title,u_description,nid,session.get('user')])
        mydb.commit()
        flash(f'notes{u_title} updated successfully')
        return redirect(url_for('viewnotes',nid=nid))
    return render_template('updatenotes.html',notesdata=notesdata)

@app.route('/deletenotes/<nid>')
def deletenotes(nid):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where nid=%s',[nid])
        #notesdata=cursor.fetchone()
        mydb.commit()
        return redirect(url_for('viewallnotes'))

@app.route('/uploadfiles',methods=['GET','POST'])
def uploadfiles():
    if request.method=='POST':
        file_data=request.files['file']
        f_name=file_data.filename
        fdata=file_data.read()
        cursor=mydb.cursor(buffered=True)
        cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[f_name,fdata,session.get('user')])
        mydb.commit()
        flash(f'{f_name} added successfully')

    return render_template('uploadfiles.html')


@app.route('/viewallfiles')
def viewallfiles():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[session.get('user')])
    allfilesdata=cursor.fetchall()
    return render_template('viewallfiles.html',allfilesdata=allfilesdata) 

@app.route('/viewfile/<fid>')
def viewfile(fid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select fdata,filename from filedata where fid=%s and added_by=%s',[fid,session.get('user')])
    filedata=cursor.fetchone()
    f_data=BytesIO(filedata[0]) #In-memory mysql stores binary stream data,
    #available as BytesIO objects
    return send_file(f_data,as_attachment=False,download_name=filedata[1])

@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select fdata,filename from filedata where fid=%s and added_by=%s',[fid,session.get('user')])
    filedata=cursor.fetchone()
    f_data=BytesIO(filedata[0]) #In-memory mysql stores binary stream data,
    #available as BytesIO objects
    return send_file(f_data,as_attachment=True,download_name=filedata[1])

@app.route('/deletefile/<fid>')
def deletefile(fid):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from filedata where fid=%s',[fid])
        mydb.commit()
        flash(f'File deleted successfully')
        return redirect(url_for('viewallfiles')) 

@app.route('/getexceldata')
def getexceldata():
    cursor=mydb.cursor(buffered=True)
    cursor.execute('select * from notes where added_by=%s',[session.get('user')])
    content=cursor.fetchall() #return all notes data in list of tuples
    columns=['notes_id','title','notes_data','created_at','created_by']
    data=[list(i) for i in content]
    data.insert(0,columns) #
    return excel.make_response_from_array(data,'xlsx',filename='notesdata')

@app.route('/search',methods=['GET','POST'])
def search():
    if request.method=='POST':
        search_data=request.form['s_data']
        string=['A-Za-z0-9']
        pattern=re.compile(f'^{string}',re.IGNORECASE)
        if (pattern.match(search_data)):
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select * from notes where nid like %s or title like %s or description like %s and added_by=%s',[search_data+'%',search_data+'%',search_data+'%',session.get('user')])
            matcheddata=cursor.fetchall()
            return render_template('search.html',sdata=matcheddata)
        else:
            flash('NO data Found')
    return render_template('dashboard.html')


@app.route('/forgotpassword',methods=('GET','POST'))
def forgotpassword():
    if session.get('user'):
        if request.method=='POST':
            f_email=request.form['email']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(*) from users where email=%s',[f_email])
            count_email=cursor.fetchone()
            if count_email[0]==1:
                subject=f'Reset link for SNM website forgot password'
                body=f"click to reset link: {url_for('newpassword',data=entoken(f_email),_external=True)}"
                send_mail(to=f_email,subject=subject,body=body)
                flash(f'Reset link has been set to given mailID{f_email}')
                return redirect(url_for('login'))
            elif count_email[0]==0:
                flash(f'Please register your account')
                return redirect(url_for('register'))
                
        return render_template('forgotpassword.html')
    else:
        flash('Please login')
        return redirect(url_for('login'))

@app.route('/newpassword/<data>',methods=['GET','POST'])
def newpassword(data):
    if session.get('user'):
        if request.method=='POST':
            npassword=request.form['new_password']
            cpassword=request.form['confirm_password']
            if npassword==cpassword:
                email=detoken(data)
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update users set password=%s where email=%s',[npassword,email])
                mydb.commit()
                return(f'newpassword updated successfully Please login')
                # return redirect(url_for('login'))
            else:
                flash('Mismatched password Please check')
                return redirect(url_for('newpassword',data=data))
        return render_template('newpassword.html')
    else:
        flash('Please login')
        return redirect(url_for('login'))

app.run(use_reloader=True,debug=True)