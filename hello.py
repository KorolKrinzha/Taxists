# -*- coding: utf-8 -*-
from flask import Flask, render_template, url_for, request, redirect, abort, session, send_file
import json
import datetime
import mysql.connector
from flaskext.mysql import MySQL
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dbkeys import db_host, db_user, db_password, db_database, secretkey, salt


app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = secretkey  # session cokie


# =====================DB CONNECT============================#
# mydb = mysql.connector.connect(host=db_host, user=db_user, password=db_password, database=db_database)
# mycursor = mydb.cursor(buffered=True)

# =====================DB INSERT FORMULAS============================#

addFormulaevent = "INSERT INTO events ( title, place, dates, currentdate ,contacts, content, user_id, user_fullname) \
VALUES (%s, %s, %s, curdate(),  %s, %s, %s, %s )"
addFormulauser = "INSERT INTO users ( fullname, username, email, password ,do) \
VALUES (%s, %s,  %s, %s, 0)"
addFormulaparticipant = "INSERT INTO participants ( event_id, event_title, id, fullname) \
VALUES (%s, %s, %s, %s)"


# =====================FOR BEAUTIFUL DB OUTPUT============================#
def ultimate_executor(func):
    mydb = mysql.connector.connect(
        host=db_host, user=db_user, password=db_password, database=db_database)
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute(func)
    row_headers = [x[0] for x in mycursor.description]
    rv = mycursor.fetchall()
    json_data = []
    for result in rv[::-1]:
        json_data.append(dict(zip(row_headers, result)))
    result = json_data

    mydb.close()
    mycursor.close()

    return result


# =====================NAMINGS============================#
mainname = "Лицей.Таксисты"
shoptitle = "Магаз"
api = "Проекты"
eventstitle = "События"
coffeshop = "Айтикафе"
signintitle = "Регистрация"
logintitle = "Авторизация"


# =====================MAIN PAGE============================#
@app.route("/", methods=['POST', 'GET'])
def index():
    return render_template('index.html', mainname=mainname)


# =====================CHECK SESSION============================#
@app.route("/user")
def usersession():

    if "fullname" in session and session["do"]:
        user = session["fullname"]
        return f"<h1>{user}</h1>"
    else:
        return redirect("/")





# =====================ADMINISTRATION============================#
@app.route("/manager", methods=['POST', 'GET'])
def deletefiles():
    if session and  "fullname" in session and session['do']:
        mydb = mysql.connector.connect(
            host=db_host, user=db_user, password=db_password, database=db_database)
        mycursor = mydb.cursor(buffered=True)
        if session and "fullname" in session:
            events = ultimate_executor('SELECT * FROM events')
            user = session["fullname"]
            if request.method == 'POST':
                delete_id = request.form['delete_id']
                mycursor.execute(
                    "DELETE FROM events WHERE event_id='%s'" % delete_id)
                mycursor.execute(
                    "DELETE FROM participants WHERE event_id='%s'" % delete_id)

                mydb.commit()

                return redirect(route)

            mycursor.close()
            mydb.close()

            return render_template("manage.html", user=user, events=events, msg="Удалить")
        else:
            abort(404)
    else:
        abort(404)        
    


# =====================ERROR HANDLERS============================#
# NOT FOUND PAGE
@app.errorhandler(404)
def page_not_found(e):

    return render_template('404.html'), 404

# IN CASE SMTH GETS WRONG THE USER WILL SEE SOME FUNNY IMAGE


@app.errorhandler(500)
def internal_server_error(e):

    return render_template('500.html'), 500  # !!!


# =====================USER SETTINGS============================#
# PERSONAL PAGE FOR EVERY LOGGED USER
@app.route("/mypage", methods=['GET', 'POST'])
def mypage():
    if session and session['id']:
        user = session['fullname']
        return render_template('mypage.html', user=user)
    else:
        redirect('/login')


@app.route("/mypage/profile", methods=['GET', 'POST'])
def mypageprofile():
    if session and session['id']:
        msg = ""

        user = ultimate_executor(
            "SELECT  * FROM users WHERE id='%s'" % session['id'])[0]
        oldemail = user['email']
        if request.method == "POST":

            email = request.form['email']

            # CHECKING IF THE EMAIL ALREADY EXISTS OR NOT
            list = []
            json_data = ultimate_executor("SELECT email FROM users")

            for dicti in json_data:
                for k, v in dicti.items():
                    list.append(v)
            list = [element for element in list if element != oldemail]
            if str(email) in list:

                msg = "Данная почта уже была зарегестрирована...("

            else:
                username = request.form['username']

                mydb = mysql.connector.connect(
                    host=db_host, user=db_user, password=db_password, database=db_database)
                mycursor = mydb.cursor(buffered=True)
                # UPDATING THE USER`S ROW
                mycursor.execute(
                    'UPDATE `users` SET `email`  = %s, username= %s   WHERE `users`.`id`= %s', (email, username, session['id']))

                mydb.commit()

                mydb.close()
                mycursor.close()
                # GOING BACK TO USER MANAGER
                return redirect("/mypage")

        return render_template('mypageprofile.html', user=user, msg=msg)
    else:
        abort(404)  # FOR UNAUTHORIZED


@app.route("/mypage/delete", methods=['GET', 'POST'])
def mydelete():
    mydb = mysql.connector.connect(
        host=db_host, user=db_user, password=db_password, database=db_database)
    mycursor = mydb.cursor(buffered=True)
    if session and "fullname" in session:
        events = ultimate_executor("SELECT  * FROM events WHERE user_id='%s'" % session['id'])
        user = session["fullname"]
        if request.method == 'POST':
            delete_id = request.form['delete_id']
            if type(delete_id)==int:

                mycursor.execute(
                    "DELETE FROM events WHERE event_id='%s'" % delete_id)
                mycursor.execute(
                    "DELETE FROM participants WHERE event_id='%s'" % delete_id)

                mydb.commit()
            else:
                
                abort(500)                

            return redirect("/mypage/delete")

        mycursor.close()
        mydb.close()

        return render_template("manage.html", user=user, events=events, msg="Удалить")
    else:
        abort(404)







@app.route("/mypage/unsign", methods=['GET', 'POST'])
def unsign():
    if session and "fullname" in session:
        events = ultimate_executor(
            "SELECT * FROM events WHERE event_id in (SELECT event_id FROM participants WHERE participants.id = '%s')" % session['id'])
        user = session["fullname"]
        if request.method == 'POST':
            delete_id = request.form['delete_id']
            if type(delete_id)==int:

                mydb = mysql.connector.connect(
                    host=db_host, user=db_user, password=db_password, database=db_database)
                mycursor = mydb.cursor(buffered=True)

                mycursor.execute(
                    'DELETE FROM participants WHERE  id = %s AND event_id = %s', (session['id'], delete_id))

                mydb.commit()

                mycursor.close()
                mydb.close()
             else:
                 abort(500)   

            return redirect("/mypage/unsign")
        return render_template("manage.html", user=user, events=events, msg="Отписаться")
    else:
        abort(404)


# =====================CONFIRM ACCOUNT============================#
@app.route("/login", methods=['GET', 'POST'])
def login():
    msg = ''

    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        try:

            mydb = mysql.connector.connect(
                host=db_host, user=db_user, password=db_password, database=db_database)
            mycursor = mydb.cursor(buffered=True)


            account = mycursor.execute(
                'SELECT * FROM users WHERE email = %s AND do = %s', (username, 0))
            account = mycursor.fetchone()
            
            check = account[3]


            mycursor.close()
            mydb.close()

        except:

            mydb = mysql.connector.connect(
                host=db_host, user=db_user, password=db_password, database=db_database)
            mycursor = mydb.cursor(buffered=True)

            account = mycursor.execute(
                'SELECT * FROM users WHERE email = %s AND do = %s', (username, 1))
            account = mycursor.fetchone()
            check = account[3]

            mycursor.close()
            mydb.close()

        if account and check_password_hash(check, password):
            session['loggedin'] = True
            session['id'] = account[0]
            session['fullname'] = account[1]
            session['do'] = bool(account[5])

            return redirect("/")
        else:

            msg = 'Неправильный логин/пароль...  :('

    return render_template('login.html', login=logintitle, msg=msg)


# =====================CREATE ACCOUNT============================#
@app.route("/signin", methods=['GET', 'POST'])
def signin():
    msg = ""

    if request.method == "POST":
        email = request.form['email']
        list = []
        json_data = ultimate_executor("SELECT email FROM users")

        for dicti in json_data:
            for k, v in dicti.items():
                list.append(v)

        if email in list:
            msg = "Данная почта уже была зарегестрирована...("
        else:

            fullname = request.form['fullname']
            username = request.form['username']

            password = request.form['password']
            password = generate_password_hash(password)
            print(password)
            newuser = (
                fullname,
                username,
                email,
                password
            )
            mydb = mysql.connector.connect(
                host=db_host, user=db_user, password=db_password, database=db_database)
            mycursor = mydb.cursor(buffered=True)
            mycursor.execute(addFormulauser, newuser)
            mydb.commit()
            

            

            account = mycursor.execute(
                'SELECT * FROM users WHERE email = %s AND password = %s', (email, password))
            account = mycursor.fetchone()
            
            


            mycursor.close()
            mydb.close()



            session.permanent = True
            session['loggedin'] = True
            session['do'] = False  # bool(account[5])
            session['fullname'] = account[1]
            session['id'] = account[0]

            return redirect("/")

    return render_template('signin.html', signin=signintitle, msg=msg)


# =====================EVENTS============================#
@app.route("/events", methods=['POST', 'GET'])
def events():
    msg = ""

    if request.method == 'POST':
        if session:
            # print("ok")
            fullname = session['fullname']
            user_id = session['id']
            post_title = request.form['title']
            post_place = request.form['place']
            post_dates = request.form['dates']
            post_contacts = request.form['contacts']
            post_content = request.form['content']

            eventnew = (
                post_title,
                post_place,
                post_dates,
                post_contacts,
                post_content,
                session['id'],
                session['fullname']
            )

            mydb = mysql.connector.connect(
                host=db_host, user=db_user, password=db_password, database=db_database)
            mycursor = mydb.cursor(buffered=True)
            mycursor.execute(addFormulaevent, eventnew)

            mydb.commit()

            mycursor.close()
            mydb.close()

        else:
            msg = "Зарегистрируйтесь, чтобы создать событие"

    events = ultimate_executor("SELECT * FROM events")
    return render_template('events.html',
                           events=events, eventstitle=eventstitle, msg=msg)


@app.route("/events/<int:event_id>", methods=['GET', 'POST'])
def event(event_id):

    json_data = ultimate_executor("SELECT event_id FROM events")
    event = []
    for dicti in json_data:
        for k, v in dicti.items():
            event.append(v)

    if event_id not in event:
        abort(404)

    msg = ""

    event = ultimate_executor(
        "SELECT  * FROM events WHERE event_id='%s'" % event_id)[0]
    participants = ultimate_executor(
        "SELECT  * FROM participants WHERE event_id='%s'" % event_id)

    if request.method == 'POST':

        if session:

            users = ultimate_executor(
                "SELECT  id FROM participants WHERE event_id='%s'" % event_id)
            listedin = tuple(d['id'] for d in users)

            # print(user)
            if session["id"] in listedin:
                msg = "Вы уже участвуете в этом событии. Не забудьте принять участие!"
            else:
                user = session['id']
                username = session['fullname']

                #newparticipant = (event_id, True,user, username )
                newparticipant = (event_id, event['title'], user, username)

                mydb = mysql.connector.connect(
                    host=db_host, user=db_user, password=db_password, database=db_database)
                mycursor = mydb.cursor(buffered=True)

                mycursor.execute(addFormulaparticipant, newparticipant)
                mydb.commit()

                mycursor.close()
                mydb.close()

                return redirect("")

        else:
            msg = "Зарегистрируйтесь, чтобы участвовать..."

        ###################KOSTIL##########################
        # print(participants)

    return render_template('event.html', event=event, participants=participants, msg=msg)


@app.route("/users/<int:id>", methods=['GET', 'POST'])
def user(id):

    managable = False
    json_data = ultimate_executor("SELECT id FROM users")
    list = []
    for dicti in json_data:
        for k, v in dicti.items():
            list.append(v)

    if id not in list:
        abort(404)

    user = ultimate_executor("SELECT  * FROM users WHERE id='%s'" % id)[0]

    user_events = ultimate_executor(
        "SELECT  * FROM participants WHERE `participants`.`id`='%s' AND EXISTS (SELECT 1 FROM `events` WHERE events.event_id=participants.event_id) " % id)
    managed_events = ultimate_executor(
        "SELECT  * FROM events WHERE `events`.`user_id`='%s' " % id)

    if session:

        if session['id'] == user['id']:

            managable = True

    return render_template('user.html', user=user, user_events=user_events, managed_events=managed_events, managable=managable)


# =====================SHOP============================#
@app.route("/shop", methods=['POST', 'GET'])
def shop():
    shoplist = ultimate_executor("SELECT * FROM shoplist")
    return render_template('shop.html', shoplist=shoplist, shoptitle=shoptitle)


@app.route("/shop/<name>", methods=['GET', 'POST'])
def shopitem(name):
    json_data = ultimate_executor("SELECT name FROM shoplist")
    shop = []
    for dicti in json_data:
        for k, v in dicti.items():
            shop.append(v)

    if name not in shop:
        abort(404)

    shop = ultimate_executor(
        "SELECT  * FROM shoplist WHERE name='%s'" % name)[0]
    # print(shop)

    return render_template('test.html', shop=shop)


# =====================ITCAFE============================#
@app.route("/coffee", methods=['GET', 'POST'])
def coffee():
    coffee = ultimate_executor("SELECT * FROM coffee")
    return render_template('coffee.html', coffeshop=coffeshop, coffee=coffee)


# =====================JSONOUTPUT============================#
@app.route('/get', methods=['GET'])
def get_post():

    json_data = ultimate_executor("SELECT * FROM events")
    json_data = {"results": json_data}
    return json.dumps(json_data,  ensure_ascii=False)


# =====================JSONINPUT============================#
@app.route('/input', methods=['POST'])
def get_outputs():

    req = request.get_json()

    post_title = req['title']
    post_place = req['place']
    post_dates = req['dates']
    post_contacts = req['contacts']
    post_content = req['content']

    eventnew = (
        post_title,
        post_place,
        post_dates,
        post_contacts,
        post_content
    )

    mydb = mysql.connector.connect(
        host=db_host, user=db_user, password=db_password, database=db_database)
    mycursor = mydb.cursor(buffered=True)
    mycursor.execute(addFormulaevent, eventnew)
    mydb.commit()

    mycursor.close()
    mydb.close()

    return redirect('/get')


# =====================RUNFLASK============================#
if __name__ == "__main__": 
    app.run(debug=False, host='0.0.0.0', port=5000)

