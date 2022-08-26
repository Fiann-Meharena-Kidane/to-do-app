from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, Boolean

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'


app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Task(db.Model):
    __tablename__='task'
    id = db.Column(Integer, primary_key=True)
    task = db.Column(String)
    status=db.Column(String)


# db.drop_all()
# db.create_all()


@app.route('/')
def home():
    all_tasks_rows = Task.query.all()

    return render_template('index.html', tasks=all_tasks_rows)


@app.route('/add', methods=['POST', 'GET'])
def add():
    task = request.form.get('task')

    new_task=Task(
        task=task,
        status='active'
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
    all_active_tasks=Task.query.filter_by(status='active')

    return render_template('index.html', tasks=all_active_tasks)


@app.route('/completed')
def completed():
    all_active_tasks=Task.query.filter_by(status='done')

    return render_template('index.html', tasks=all_active_tasks)


if __name__ == '__main__':
    app.run(debug=True)
