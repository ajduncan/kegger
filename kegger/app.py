import datetime
import os
import os.path as op

from flask import Flask, render_template, send_from_directory, url_for
from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib import rediscli
from flask.ext.admin.form import rules
from flask.ext.admin.contrib.mongoengine import ModelView
from redis import Redis
from rq import Queue

from downspout import services, utils

# Create application
app = Flask(__name__)

app.config['MONGODB_SETTINGS'] = {'DB': 'testing'}

# Create models
db = MongoEngine()
db.init_app(app)


# Define mongoengine documents
class User(db.Document):
    
    name = db.StringField(max_length=40)
    password = db.StringField(max_length=40)

    def __unicode__(self):
        return self.name


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
    
    column_searchable_list = ('name',)
    column_filters = ('name', 'email')


# Customized admin views
class UserView(ModelView):

    column_filters = ['name']
    column_searchable_list = ('name', 'password')



class ArtistView(ModelView):

    column_filters = ['name', 'service']
    form_ajax_refs = {
        'service': {
            'fields': ['name']
        }
    }


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def index():
    return render_template('index.html')


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


# meh, add a route for media, files, etc and something like
# http://www.boxcontrol.net/simple-stream-your-media-with-flask-python-web-framework-tutorial.html


# figure out the downspout portion of this problem, add a sync service
# consider using workers to perform the sync, but store in mongo.


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, 
                        'Example: MongoEngine', 
                        base_template='layout.html', 
                        template_mode='bootstrap3')

    # Add views
    admin.add_view(UserView(User, name="Users"))
    admin.add_view(ModelView(Artist))
    admin.add_view(ModelView(Media))
    admin.add_view(ModelView(File))
    admin.add_view(rediscli.RedisCli(Redis()))

    # Start app
    app.run(debug=True)
