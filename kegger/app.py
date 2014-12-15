import datetime
import os
import os.path as op

from flask import Flask
from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.form import rules
from flask.ext.admin.contrib.mongoengine import ModelView


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
    service = db.ListField(db.ReferenceField('Service'))


class Service(db.Document):
    
    name = db.StringField(max_length=20)

    def __unicode__(self):
        return self.name


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


# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a>'


if __name__ == '__main__':
    # Create admin
    admin = admin.Admin(app, 
                        'Example: MongoEngine', 
                        base_template='layout.html', 
                        template_mode='bootstrap3')

    # Add views
    admin.add_view(UserView(User, name="Users"))
    admin.add_view(ModelView(Artist))
    admin.add_view(ModelView(Service))
    admin.add_view(ModelView(Media))
    admin.add_view(ModelView(File))

    # Start app
    app.run(debug=True)
