import os
from flask import Flask
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
# Import the Mail extension
from flask_mail import Mail
from whitenoise import WhiteNoise

load_dotenv()

app = Flask(__name__)

# --- Configuration ---
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")

# --- Email Configuration ---
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

# --- Static Files Configuration ---
# It tells your app to serve files from the 'static' directory.
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

# --- Initialize Extensions ---
try:
    mongo = PyMongo(app)
    # Test the connection
    mongo.db.list_collection_names()
except Exception as e:
    print(f"MongoDB initialization error: {e}")
    mongo = None
bcrypt = Bcrypt(app)
oauth = OAuth(app)
# Initialize Mail
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"

# --- Google OAuth Configuration ---
# This part will now correctly load the client ID and secret from the environment
oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)
# --- End of OAuth Configuration ---

from petcare import routes
