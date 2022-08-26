from flask import Flask, render_template, redirect, request, url_for, flash
from flask_login import LoginManager, login_user, logout_user, UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, Boolean, ForeignKey

import os
from datetime import date

from sqlalchemy.orm import relationship

today = date.today()


from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'


app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Task(db.Model, UserMixin):
    __tablename__='task'
    id = db.Column(Integer, primary_key=True)
    task = db.Column(String)
    status=db.Column(String)
    date=db.Column(String)
    user_id=db.Column(Integer, ForeignKey('user.id'))


class User(db.Model, UserMixin):
    __tablename__='user'
    id=db.Column(Integer, primary_key=True)
    name=db.Column(String)
    email=db.Column(String)
    password=db.Column(String)
    tasks=relationship("Task")

# db.drop_all()
# db.create_all()


login_manager=LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/', methods=['POST','GET'])
def login():
    if request.method=='POST':
        email=request.form.get('email')
        password=request.form.get('password')

        user=User.query.filter_by(email=email).first()

        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                flash(f'Welcome {user.name}!')
                return redirect(url_for('home'))
            else:
                flash('Incorrect password, try again')
                return redirect(url_for('login'))
        else:
            flash('Email does not exist, register instead')
            return redirect('register')
    else:

        return render_template('login.html')


@app.route('/home')
def home():
    # tasks=current_user.tasks
    # all_tasks_rows = Task.query.all()
    all_tasks_rows = current_user.tasks

    return render_template('index.html', tasks=all_tasks_rows)


@app.route('/register', methods=['POST','GET'])
def register():
    if request.method=='POST':
        name=request.form.get('name')
        email=request.form.get('email')
        password=request.form.get('password')

        if not User.query.filter_by(email=email).first():
            hashed_password=generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            new_user=User(
                name=name,
                email=email,
                password=hashed_password
            )

            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            flash(f'Welcome {name}!')
            return redirect(url_for('home'))
        else:
            flash("Email already exits, login instead")
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/add', methods=['POST', 'GET'])
def add():
    task = request.form.get('task')

    new_task=Task(
        task=task,
        date=today.strftime("%B %d, %Y "),
        status='active',
        user_id=current_user.id
    )

    db.session.add(new_task)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/done/<int:task_id>')
def done(task_id):
    target_task=Task.query.filter_by(id=task_id).first()
    dashed_task=f"<s>{target_task.task}</s>"
    target_task.task=dashed_task
    target_task.status='done'
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/delete/<int:task_id>')
def delete(task_id):
    target_task=Task.query.filter_by(id=task_id).first()

    db.session.delete(target_task)
    db.session.commit()

    return redirect(url_for('home'))


@app.route('/active')
def active():
    list_of_active_task=[]
    all_active_tasks=Task.query.filter_by(status='active')
    for task in all_active_tasks:
        if task.user_id==current_user.id:
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


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
