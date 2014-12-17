import datetime
import os
import os.path as op

from flask import Flask, render_template, send_from_directory, url_for, redirect, request
from flask.ext import admin, login
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib import rediscli
from flask.ext.admin.form import rules
from flask.ext.admin.contrib.mongoengine import ModelView
from redis import Redis
from rq import Queue
from wtforms import form, fields, validators

from downspout import services, utils

# Create application
app = Flask(__name__)

# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = '123456790'

app.config['MONGODB_SETTINGS'] = {'DB': 'testing'}

# Create models
db = MongoEngine()
db.init_app(app)


# Create user model. For simplicity, it will store passwords in plain text.
# Obviously that's not right thing to do in real world application.
class User(db.Document):

    login = db.StringField(max_length=80, unique=True)
    email = db.StringField(max_length=120)
    password = db.StringField(max_length=64)

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    # Required for administrative interface
    def __unicode__(self):
        return self.login


class Artist(db.Document):
    
    name = db.StringField(max_length=40)
    service = db.StringField(choices=services)


class Media(db.Document):
    
    artist = db.ListField(db.ReferenceField('Artist'))
    title = db.StringField(max_length=50)
    date = db.DateTimeField(default=datetime.datetime.now)
    data = db.ReferenceField('File')


class File(db.Document):
    
    name = db.StringField(max_length=50)
    data = db.FileField()


# Customized admin interface
class CustomView(ModelView):
    
    list_template = 'list.html'
    create_template = 'create.html'
    edit_template = 'edit.html'


class UserAdmin(CustomView):
    
    column_searchable_list = ('login',)
    column_filters = ('login', 'email')


# Customized admin views
class UserView(ModelView):

    column_filters = ['login']
    column_searchable_list = ('login', 'password')

    def is_accessible(self):
        return login.current_user.is_authenticated()



class ArtistView(ModelView):

    column_filters = ['name', 'service']
    form_ajax_refs = {
        'service': {
            'fields': ['name']
        }
    }


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):

    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return User.objects(login=self.login.data).first()


class RegistrationForm(form.Form):

    login = fields.TextField(validators=[validators.required()])
    email = fields.TextField()
    password = fields.PasswordField(validators=[validators.required()])


    def validate_login(self, field):
        if User.objects(login=self.login.data):
            raise validators.ValidationError('Duplicate username')


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.setup_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()


# Create customized model view class
class AuthModelView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated()


# Create customized index view class
class AuthAdminIndexView(admin.AdminIndexView):

    def is_accessible(self):
        return login.current_user.is_authenticated()


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    return render_template('index.html', user=login.current_user)


# need a login requirement here etc.
@app.route('/fetch/<service>/<artist>')
def fetch(service, artist):
    q = Queue(connection=Redis())
    result = q.enqueue(utils.fetch, service, artist)
    return render_template('fetch.html')


@app.route('/artists/')
def artists():
    return render_template('artists.html', artists=Artist.objects())


@app.route('/artist/<name>')
def artist(name):
    return render_template('artist.html', artists=Artist.objects(name=name))


@app.route('/login/', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('login_form.html', form=form)


@app.route('/register/', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User()

        form.populate_obj(user)
        user.save()

        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('login_form.html', form=form)


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))


# meh, add a route for media, files, etc and something like
# http://www.boxcontrol.net/simple-stream-your-media-with-flask-python-web-framework-tutorial.html


# figure out the downspout portion of this problem, add a sync service
# consider using workers to perform the sync, but store in mongo.


if __name__ == '__main__':
    # Initialize flask-login
    init_login()

    # Create admin
    admin = admin.Admin(app, 
                        'Kegger', 
                        base_template='layout.html', 
                        template_mode='bootstrap3',
                        index_view=AuthAdminIndexView()
                        )

    # Add views
    admin.add_view(UserView(User, name="Users"))
    admin.add_view(ModelView(Artist))
    admin.add_view(ModelView(Media))
    admin.add_view(ModelView(File))
    admin.add_view(rediscli.RedisCli(Redis()))

    # Start app
    app.run(debug=True)
