from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

import os
from datetime import date
from email.message import EmailMessage
import ssl
import smtplib

# email setup
my_email = os.environ.get('to-do-app-email')
my_password = os.environ.get('to-do-app-email-password')
target_email =os.environ.get('to-do-app-email-message')


today = date.today()
current_year = date.today().year

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('finan-to-do-app-secret')

# try local db, if error go with sqlllite db,
try:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('LOCAL_DB_URL')
except:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Task(db.Model, UserMixin):
    __tablename__ = 'task'
    id = db.Column(Integer, primary_key=True)
    task = db.Column(String)
    status = db.Column(String)
    date = db.Column(String)
    user_id = db.Column(Integer, ForeignKey('user.id'))


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String)
    email = db.Column(String)
    password = db.Column(String)
    tasks = relationship("Task")


# db.drop_all()
# db.create_all()


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        # get user credentials
        user = User.query.filter_by(email=email).first()
        # if user found in our db,
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash(f'Welcome {user.name}!')
                return redirect(url_for('home'))
            # login user and redirect to home
            else:
                flash('Incorrect password, try again')
                return redirect(url_for('login'))
        else:
            flash('Email does not exist, register instead')
            return redirect('register')
    else:

        return render_template('login.html', year=current_year)


@app.route('/home')
@login_required
def home():
    all_tasks_rows = current_user.tasks
    # display tasks which belong only to the current user

    return render_template('index.html', tasks=all_tasks_rows, year=current_year)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not User.query.filter_by(email=email).first():
            # if email is not registered,
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            new_user = User(
                name=name,
                email=email,
                password=hashed_password
            )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash(f'Welcome {name}!')
            return redirect(url_for('home'))
        # add user, redirect user to homepage
        else:
            flash("Email already exits, login instead")
            return redirect(url_for('login'))

    return render_template('register.html', year=current_year)


@app.route('/add', methods=['POST', 'GET'])
@login_required
def add():
    task = request.form.get('task')

    new_task = Task(
        task=task,
        date=today.strftime("%B %d, %Y "),
        status='active',
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/done/<int:task_id>')
@login_required
def done(task_id):
    target_task = Task.query.filter_by(id=task_id).first()
    dashed_task = f"<s>{target_task.task}</s>"
    target_task.task = dashed_task
    target_task.status = 'done'
    # get the selected task, modify its structure that it is rendered as a dashed
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete/<int:task_id>')
@login_required
def delete(task_id):
    target_task = Task.query.filter_by(id=task_id).first()

    db.session.delete(target_task)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/active')
def active():
    list_of_active_task = []
    all_active_tasks = Task.query.filter_by(status='active')
    # get all active ones, then filter only those with id same as the current user,

    for task in all_active_tasks:
        if task.user_id == current_user.id:
            list_of_active_task.append(task)
    return render_template('index.html', tasks=list_of_active_task)


@app.route('/completed')
def completed():
    list_of_finished_task = []
    all_finished_tasks = Task.query.filter_by(status='done')
    for task in all_finished_tasks:
        if task.user_id == current_user.id:
            list_of_finished_task.append(task)

    return render_template('index.html', tasks=list_of_finished_task)


@app.route('/progress')
def progress():
    list_of_active_task = []
    all_active_tasks = Task.query.filter_by(status='active')
    # get all active ones, then filter only those with id same as the current user,

    for task in all_active_tasks:
        if task.user_id == current_user.id:
            list_of_active_task.append(task)
    number_of_active = len(list_of_active_task)

    list_of_finished_task = []
    all_finished_tasks = Task.query.filter_by(status='done')
    for task in all_finished_tasks:
        if task.user_id == current_user.id:
            list_of_finished_task.append(task)
    number_of_finished = len(list_of_finished_task)

    # get number of active and finished, calculate percentile,
    try:
        percentage = (number_of_finished / (number_of_active + number_of_finished)) * 100
    except ZeroDivisionError:
        percentage = 0
    else:
        percentage = round(percentage)

    link_start = "https://quickchart.io/chart?c={type:'radialGauge',data:{datasets:[{data:["
    link_end = "],backgroundColor:'green'}]}}"

    complete_link = link_start + str(percentage) + link_end

    return render_template('index.html', year=current_year, percentage=complete_link)
    # pass percentage


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/email', methods=['POST', 'GET'])
def email():
    # return 'hello'
    if request.method == 'POST':
        user_name = current_user.name
        subject = request.form.get('subject')
        updated_subject = f"{user_name} | {subject}"
        body = request.form.get('message')

        # build the email content

        em = EmailMessage()
        em['From'] = current_user.name
        em['To'] = target_email
        em['Subject'] = updated_subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(my_email, my_password)
            smtp.sendmail(my_email, target_email, em.as_string())
        # send email,
        flash('Message Sent! Thank you.')
        return redirect(url_for('home', year=current_year))

    else:
        return render_template('index.html', year=current_year, email=True)


if __name__ == '__main__':
    app.run(debug=True)
