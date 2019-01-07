import firebase_admin
from firebase_admin import credentials, db

cred = credentials.Certificate('db/serviceAccountKey.json')
firebase_default_app = firebase_admin.initialize_app(cred, {
    'databaseURL' : 'https://testjson-807aa.firebaseio.com'
})

# Get a database reference to our blog.
firebase_ref = db.reference('/')

daily = 100.00
monthly = 200.00
drawer = 1000.00

users_ref = firebase_ref.child('Data2')
try:
    users_ref.set({
        'Daily': daily,
        'Monthly': monthly,
        'Drawer': drawer
    })
except:
    print "This is an error message!"