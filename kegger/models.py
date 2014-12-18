import datetime

from flask.ext.mongoengine import MongoEngine

from downspout import services

# Create models
db = MongoEngine()


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
    
    artist = db.ReferenceField('Artist')
    title = db.StringField(max_length=50)
    date = db.DateTimeField(default=datetime.datetime.now)
    data = db.ReferenceField('File')


class File(db.Document):
    
    name = db.StringField(max_length=50)
    data = db.FileField()


