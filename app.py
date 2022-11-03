from logging import exception
from flask import Flask, render_template, request, redirect, url_for, flash, session
from transcribe.assembly import upload, save_transcript
from pathlib import Path
import os
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from forms import UserForm, LoginForm, TranscriptForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://vmiibldxtmcphr:254659b967cf2bdb333c38fb6b13926ab49005e2e7ad74c9bdf33fecf4480a18@ec2-3-229-165-146.compute-1.amazonaws.com:5432/d9lf9889m8460d"
# app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:password@localhost/class"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY");

db = SQLAlchemy(app)
migrate = Migrate(app, db) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))
    
with app.app_context():         
    db.create_all()
    
# Set upload folder for transcriptions
UPLOAD_FOLDER = "static/transcripts"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
      
# ===== Routes =====
@app.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated == False:
        flash("Create an account to get the full Clask experience", category="disclaimer")
    transcript = ""
    if request.method == "POST":

        if "file" not in request.files:
            flash("File not found", category="error")

        file = request.files["file"]
        if file.filename == "":
            flash("Please Upload a File", category="error")
        
        if file:
            file.save(os.path.join(app.config["UPLOAD_FOLDER"]), file.filename)
            path_to_download_folder = str(f"{os.path.expanduser( '~' )}/Downloads")
            # path_to_download_folder = str(os.path.join(Path.home(), "Downloads"))
            # path = f"{path_to_download_folder}/{file.filename}"
            path = (f"/static/transcripts/{file.filename}")
        
            audio_url = upload(path)
            transcript = save_transcript(audio_url, path)
            
            return redirect(url_for("transcript", transcript=transcript))

    return render_template('index.html', transcript=transcript)

@app.route("/transcript/<transcript>", methods=["GET", "POST"])
def transcript(transcript):
    # do form validation here for each transcription
    form = TranscriptForm()
    transcriptor = None
    # if not logged in, redirect to previous page after logging in
    if current_user.is_authenticated == False:
        session['url'] = url_for('transcript', transcript=transcript)
        print(session["url"])

    if form.validate_on_submit():   
        if current_user.is_authenticated:
            transcriptor = current_user.id
        transcript = Transcripts(title=form.title.data, content=form.content.data, author=form.author.data, transcriptor_id=transcriptor)
        db.session.add(transcript)
        db.session.commit()
        return redirect(url_for("dashboard"))
        
    transcript = transcript
    return render_template("transcription.html", transcript=transcript, form=form)

@app.route("/flaskclass/signup", methods=["GET", "POST"])
def signup():
    form = UserForm()
    
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first() # finds user by email
        if user is None:
            hashed_password = generate_password_hash(form.password.data, "sha256")
            user = Users(name=form.name.data, email=form.email.data, password_hash=hashed_password)
            db.session.add(user)
            db.session.commit()
            login_user(user) 
            flash("Account Created! Welcome to Clask", category="success")
            return redirect(url_for("dashboard")) 
        else:
            flash("Account with that email already exists", category="error")
            return redirect(url_for("signup"))
        
    all_users = Users.query.order_by(Users.date_added)
    return render_template("signup.html", form=form, all_users=all_users)

@app.route("/flaskclass/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)  
                if 'url' in session:
                    return redirect(session['url'])
                else:
                    return redirect(url_for("dashboard"))
            else:
                flash("Wrong Password", category="error")
        else:
            flash("No User Found", category="error")
    
    return render_template("login.html", form=form)

@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/flaskclass/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    transcripts = Transcripts.query.order_by(Transcripts.date_added)
    return render_template("dashboard.html", transcripts=transcripts) 

@app.route("/update/user/<int:id>", methods=["GET", "POST"])
@login_required
def update_user(id):
    form = UserForm()
    update_user = Users.query.get_or_404(id)
    if current_user.id == update_user.id:
        if request.method == "POST": # Needs to be request.method (validate_on_submit requires all fields to be filled)
            update_user.name = request.form["name"]
            update_user.email = request.form["email"]
            try:
                db.session.commit() #commits update_user.info to db
                print("User Updated Successfully")
                return redirect(url_for("dashboard"))
            except:
                print("Update Failed")
                return render_template("update_user.html", update_user=update_user, form=form)
        else:
            return render_template("update_user.html", update_user=update_user, form=form)
    else:
        print("Permission Denied")
        return redirect(url_for("dashboard"))

@app.route("/delete/user/<int:id>")
@login_required
def delete_user(id):
    delete_user = Users.query.get_or_404(id)
    if current_user.id == delete_user.id:
        try:
            db.session.delete(delete_user)
            db.session.commit()
            return redirect(url_for("signup"))
        except:
            print(exception)
            return redirect(url_for("signup"))
    else:
        print("Permission Denied")
        return redirect(url_for("dashboard"))

@app.route("/flaskclass/transcript/<int:id>")
def flaskclass_transcript(id):
    transcript = Transcripts.query.get_or_404(id)
    return render_template("transcript.html", transcript=transcript)

@app.route("/edit/transcript/<int:id>", methods=["GET", "POST"])
@login_required
def flaskclass_edit_transcript(id):
    transcript = Transcripts.query.get_or_404(id)
    if transcript.transcriptor.id == current_user.id:
        form = TranscriptForm()
        if form.validate_on_submit():
            transcript.title = form.title.data
            transcript.content = form.content.data
            transcript.author = form.author.data
                
            #commit to db
            db.session.add(transcript)
            db.session.commit()
            print("Transcript Updated")
            return redirect(url_for('flaskclass_transcript', id=transcript.id))
            
        form.title.data = transcript.title
        form.content.data = transcript.content
        form.author.data = transcript.author
        return render_template("edit_transcript.html", form=form, transcript=transcript)
    else:
        print("Permission Denied")
        return redirect(url_for("dashboard"))

@app.route("/delete/transcript/<int:id>")
@login_required
def delete_transcript(id):
    delete_transcript = Transcripts.query.get_or_404(id)
    if current_user.id == delete_transcript.transcriptor.id:
        try:
            db.session.delete(delete_transcript)
            db.session.commit()
            print("Transcript Deleted")
            return redirect(url_for("dashboard"))
        except:
            print(exception)
            return redirect(url_for("dashboard"))
    else:
        print("Permission Denied")
        return redirect(url_for("dashboard"))
    
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html")
    
    
# ===== Models =====
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255))
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign one to many
    transcripts = db.relationship("Transcripts", backref="transcriptor")
    
    @property
    def password(self):
        raise AttributeError("Password is not attributable")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return "<Name %r>" % self.name

class Transcripts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    author = db.Column(db.String(255), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    # whoever makes the transcription, the transcriptor id gets set to the user id of whoever made it
    transcriptor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    

if __name__ == "__main__":
    app.run(debug=True, threaded=True)