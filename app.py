from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resources.db'
app.secret_key = 'supersecretkey'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Resource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(200), nullable=True)  # New column for link
    description = db.Column(db.String(200), nullable=False)
    topics = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(20), nullable=False)

@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        resources = Resource.query.filter(
            (Resource.title.contains(search_query)) |
            (Resource.description.contains(search_query)) |
            (Resource.topics.contains(search_query))
        ).all()
    else:
        resources = Resource.query.all()
    return render_template('index.html', resources=resources)

@app.route('/add', methods=['GET', 'POST'])
def add_resource():
    if request.method == 'POST':
        title = request.form['title']
        link = request.form['link']  # Get link from form
        description = request.form['description']
        topics = request.form['topics']
        level = request.form['level']
        new_resource = Resource(title=title, link=link, description=description, topics=topics, level=level)
        db.session.add(new_resource)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_resource.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_resource(id):
    resource = Resource.query.get_or_404(id)
    if request.method == 'POST':
        resource.title = request.form['title']
        resource.link = request.form['link']  # Update link
        resource.description = request.form['description']
        resource.topics = request.form['topics']
        resource.level = request.form['level']
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('update_resource.html', resource=resource)

@app.route('/delete/<int:id>', methods=['POST'])
def delete_resource(id):
    resource = Resource.query.get_or_404(id)
    db.session.delete(resource)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/export', methods=['GET', 'POST'])
def export():
    if request.method == 'POST':
        email = request.form['email']
        subject = request.form['subject']
        message = request.form['message']
        resources = Resource.query.all()
        resource_list = "\n".join([f"{resource.title}: {resource.description} (Topics: {resource.topics}, Level: {resource.level})" for resource in resources])
        full_message = f"{message}\n\n{resource_list}"
        send_email(email, subject, full_message)
        flash('Email sent successfully!', 'success')
        return redirect(url_for('index'))
    else:
        search_query = request.args.get('search')
        if search_query:
            resources = Resource.query.filter(
                (Resource.title.contains(search_query)) |
                (Resource.description.contains(search_query)) |
                (Resource.topics.contains(search_query))
            ).all()
        else:
            resources = Resource.query.all()
        return render_template('export.html', resources=resources)

def send_email(to_email, subject, content):
    from_email = os.getenv('EMAIL_USER')
    from_password = os.getenv('EMAIL_PASS')
    
    msg = MIMEText(content)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    smtp_server = 'smtp.gmail.com'  # Example for Gmail
    smtp_port = 587  # Common port for TLS

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)