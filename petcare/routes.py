# --- Standard Library Imports ---
import os
import pickle
import secrets
from datetime import datetime

# --- Third-Party Imports ---
import numpy as np
import pandas as pd
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from bson.objectid import ObjectId
from itsdangerous import URLSafeTimedSerializer

# --- Local Application Imports ---
from petcare import app, mongo, bcrypt, oauth, mail
from .forms import (
    RegistrationForm, AddPet, LoginForm, AddVet, VetRegistrationForm, VetLoginForm,
    EditProfileForm, CompleteVetRegistrationForm, CompleteUserRegistrationForm,
    country_codes
)
from .models import User, Pet, HealthReport, VetLicense

# ==============================================================================
# 1. SETUP & INITIALIZATION
# ==============================================================================

# --- ML Model Loading ---
with open('pet_health_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('encoders.pkl', 'rb') as f:
    encoders = pickle.load(f)

# --- Timed Serializer for Tokens ---
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])


# ==============================================================================
# 2. CORE & STATIC ROUTES
# ==============================================================================

@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/main')
@login_required
def main_page():
    return render_template('main.html')


# ==============================================================================
# 3. AUTHENTICATION & REGISTRATION
# ==============================================================================

# --- Standard Registration ---

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated: return redirect(url_for('main_page'))
    form = RegistrationForm()
    if form.validate_on_submit():
        full_phone_number = f"{form.country_code.data}{form.phone.data}"
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.users.insert_one({
            "username": form.username.data.title(), "email": form.email.data.lower(),
            "password": hashed_password, "phone": full_phone_number, "address": form.address.data,
            "is_vet": False, "is_admin": False, "verified": False
        })
        send_verification_email(form.email.data.lower())
        flash('Your account has been created! Please check your email to verify your account.', 'success')
        return redirect(url_for('login_page'))
    return render_template('register.html', form=form)


@app.route('/vet_register', methods=['GET', 'POST'])
def vet_register_page():
    if current_user.is_authenticated: return redirect(url_for('main_page'))
    form = VetRegistrationForm()
    if form.validate_on_submit():
        full_phone_number = f"{form.country_code.data}{form.phone.data}"
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.users.insert_one({
            "username": form.username.data.title(), "email": form.email.data.lower(),
            "password": hashed_password, "phone": full_phone_number, "address": form.address.data,
            "vet_license": form.vet_license.data, "qualification": form.qualification.data,
            "is_vet": True, "is_admin": False, "verified": False
        })
        send_verification_email(form.email.data.lower())
        flash('Your veterinarian account has been created! Please check your email to verify your account.', 'success')
        return redirect(url_for('vet_login_page'))
    return render_template('vet_register.html', form=form)


# --- Standard Login & Logout ---

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if current_user.is_authenticated: return redirect(url_for('main_page'))
    form = LoginForm()
    if form.validate_on_submit():
        user_data = mongo.db.users.find_one({"username": form.username.data.title()})
        if user_data and not user_data.get('is_vet') and bcrypt.check_password_hash(user_data['password'], form.password.data):
            user = User(user_data)
            if not user.verified:
                session['unverified_user_id'] = str(user_data['_id'])
                flash('Your account is not verified. Please check your email.', 'warning')
                return redirect(url_for('unverified'))
            login_user(user)
            return redirect(url_for('main_page'))
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)


@app.route('/vet_login', methods=['GET', 'POST'])
def vet_login_page():
    if current_user.is_authenticated: return redirect(url_for('main_page'))
    form = VetLoginForm()
    if form.validate_on_submit():
        vet_data = mongo.db.users.find_one(
            {"username": form.username.data.title(), "is_vet": True, "vet_license": form.vet_license.data})
        if vet_data and bcrypt.check_password_hash(vet_data['password'], form.password.data):
            user = User(vet_data)
            if not user.verified:
                session['unverified_user_id'] = str(vet_data['_id'])
                flash('Your account is not verified. Please check your email.', 'warning')
                return redirect(url_for('unverified'))
            login_user(user)
            return redirect(url_for('main_page'))
        flash('Invalid veterinarian credentials.', 'danger')
    return render_template('vet_login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash('You have been logged out!', category='info')
    return redirect(url_for('home_page'))


# --- Email Verification & Resending ---

def send_verification_email(user_email):
    """Generates a token and sends a verification email."""
    token = s.dumps(user_email, salt='email-confirm-salt')
    msg = Message('Confirm Your Email for PetCare', recipients=[user_email])
    link = url_for('verify_email', token=token, _external=True)
    msg.body = f'Welcome to PetCare! Please click the link to verify your email address: {link}'
    mail.send(msg)


@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-confirm-salt', max_age=3600)
    except Exception:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('login_page'))

    user = mongo.db.users.find_one({"email": email})
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login_page'))

    if user.get('verified'):
        flash('Account already verified. Please log in.', 'success')
    else:
        mongo.db.users.update_one({"email": email}, {"$set": {"verified": True}})
        flash('Your account has been verified! You can now log in.', 'success')

    if user.get('is_vet'):
        return redirect(url_for('vet_login_page'))
    else:
        return redirect(url_for('login_page'))


@app.route('/unverified')
def unverified():
    return render_template('unverified.html')


@app.route('/resend_verification')
def resend_verification():
    user_id = session.get('unverified_user_id')
    if not user_id:
        flash('No user to verify. Please log in again.', 'danger')
        return redirect(url_for('login_page'))

    user_data = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        flash('User not found.', 'danger')
        return redirect(url_for('login_page'))

    if user_data.get('verified'):
        flash('This account is already verified.', 'info')
        return redirect(url_for('login_page'))

    send_verification_email(user_data['email'])
    flash('A new verification email has been sent to your address.', 'success')

    if user_data.get('is_vet'):
        return redirect(url_for('vet_login_page'))
    else:
        return redirect(url_for('login_page'))


# ==============================================================================
# 4. GOOGLE OAUTH ROUTES
# ==============================================================================

@app.route('/google/login')
def google_login():
    """Redirects to Google, remembering the user's intended role."""
    role = request.args.get('role')
    session['google_auth_role'] = 'vet' if role == 'vet' else 'user'
    redirect_uri = url_for('google_auth', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@app.route('/google/auth')
def google_auth():
    """Handles the callback from Google and directs the user to the correct completion page."""
    try:
        # Check MongoDB connection
        if mongo is None:
            print("MongoDB instance is None")
            flash("Database connection error. Please try again.", "danger")
            return redirect(url_for('login_page'))
            
        if mongo.db is None:
            print("MongoDB database is None")
            flash("Database connection error. Please try again.", "danger")
            return redirect(url_for('login_page'))
            
        # Test database access
        try:
            mongo.db.users.find_one({})
        except Exception as db_error:
            print(f"Database access error: {db_error}")
            flash("Database access error. Please try again.", "danger")
            return redirect(url_for('login_page'))
            
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        intended_role = session.pop('google_auth_role', 'user')

        if not user_info:
            flash("Could not retrieve user information from Google.", "danger")
            return redirect(url_for('login_page'))

        user_email = user_info['email'].lower()
        user_name = user_info.get('name', 'New User')
        existing_user = mongo.db.users.find_one({"email": user_email})

        if existing_user:
            user = User(existing_user)
            if intended_role == 'vet' and not user.is_vet:
                flash("This email is registered as a Pet Owner. Please log in through the Pet Owner portal.", "danger")
                return redirect(url_for('login_page'))
            elif intended_role == 'user' and user.is_vet:
                flash("This email is registered as a Veterinarian. Please log in through the Veterinarian portal.", "danger")
                return redirect(url_for('vet_login_page'))

            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('main_page'))

        else:
            # Handle registration for new Google user
            random_password = secrets.token_hex(16)
            hashed_password = bcrypt.generate_password_hash(random_password).decode('utf-8')
            new_user_data = {
                "username": user_name.title(), "email": user_email, "password": hashed_password,
                "phone": "", "address": "", "is_vet": False, "is_admin": False, "verified": True
            }
            result = mongo.db.users.insert_one(new_user_data)
            newly_created_user = mongo.db.users.find_one({"_id": result.inserted_id})
            login_user(User(newly_created_user))

            if intended_role == 'vet':
                flash("Welcome! Please complete your veterinarian profile.", "info")
                return redirect(url_for('complete_vet_registration'))
            else:
                flash("Welcome! Please complete your profile to continue.", "info")
                return redirect(url_for('complete_user_registration'))

    except Exception as e:
        import traceback
        print(f"Error during Google authentication: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        flash(f"Google authentication error: {str(e)}", "danger")
        return redirect(url_for('login_page'))


@app.route('/complete_user_registration', methods=['GET', 'POST'])
@login_required
def complete_user_registration():
    form = CompleteUserRegistrationForm()
    if form.validate_on_submit():
        full_phone_number = f"{form.country_code.data}{form.phone.data}"
        update_data = {"phone": full_phone_number, "address": form.address.data}
        mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': update_data})
        flash("Your profile is complete. Welcome to PetCare!", "success")
        return redirect(url_for('main_page'))
    return render_template('complete_user_registration.html', form=form)


@app.route('/complete_vet_registration', methods=['GET', 'POST'])
@login_required
def complete_vet_registration():
    if current_user.is_vet:
        return redirect(url_for('main_page'))
    form = CompleteVetRegistrationForm()
    if form.validate_on_submit():
        full_phone_number = f"{form.country_code.data}{form.phone.data}"
        update_data = {
            "is_vet": True, "vet_license": form.vet_license.data,
            "qualification": form.qualification.data, "phone": full_phone_number,
            "address": form.address.data, "verified": True
        }
        mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': update_data})
        flash("Your veterinarian profile is complete. Welcome!", "success")
        return redirect(url_for('main_page'))
    return render_template('complete_vet_registration.html', form=form)


# ==============================================================================
# 5. USER PROFILE & PET MANAGEMENT
# ==============================================================================

@app.route('/profile')
@login_required
def profile_page():
    user_pets = current_user.get_pets()
    return render_template('profile.html', pets=user_pets)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.is_admin:
        flash("Admin profiles cannot be edited from the web interface.", "info")
        return redirect(url_for('admin_dashboard_page'))
    form = EditProfileForm()
    if form.validate_on_submit():
        full_phone_number = f"{form.country_code.data}{form.phone.data}"
        update_data = {'phone': full_phone_number, 'address': form.address.data}
        if not current_user.is_vet:
            update_data['username'] = form.username.data.title()
        if current_user.is_vet:
            update_data['qualification'] = form.qualification.data
        if form.password.data:
            update_data['password'] = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        mongo.db.users.update_one({'_id': ObjectId(current_user.id)}, {'$set': update_data})
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('profile_page'))
    # Pre-populate form
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.address.data = current_user.address
    user_phone = current_user.phone
    if user_phone:
        sorted_codes = sorted([code[0] for code in country_codes], key=len, reverse=True)
        for code in sorted_codes:
            if user_phone.startswith(code):
                form.country_code.data = code
                form.phone.data = user_phone[len(code):]
                break
    if current_user.is_vet:
        form.qualification.data = current_user.qualification
        form.username.render_kw = {'readonly': True}
    return render_template('edit_profile.html', form=form)


@app.route('/add_pet', methods=['GET', 'POST'])
@login_required
def add_pet_page():
    form = AddPet()
    if request.method == 'POST':
        species = request.form.get('pet_species')
        if species == 'Dog': form.pet_breed.choices = form.dog_breeds
        elif species == 'Cat': form.pet_breed.choices = form.cat_breeds
        else: form.pet_breed.choices = form.horse_breeds
    else:
        form.pet_breed.choices = form.dog_breeds
    if form.validate_on_submit():
        dob_datetime = datetime.combine(form.pet_dob.data, datetime.min.time())
        mongo.db.pets.insert_one({
            "name": form.pet_name.data.title(), "species": form.pet_species.data,
            "breed": form.pet_breed.data, "gender": form.pet_gender.data,
            "dob": dob_datetime, "owner_id": ObjectId(current_user.id)
        })
        flash(f'Pet {form.pet_name.data.title()} added!', 'success')
        return redirect(url_for('profile_page'))
    breeds_data = {'Dog': form.dog_breeds, 'Cat': form.cat_breeds, 'Horse': form.horse_breeds}
    return render_template('add_pet.html', form=form, breeds_data=breeds_data)

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    """Handles the cascading deletion of a user account."""
    if current_user.is_admin:
        flash("Admin accounts cannot be deleted from the web interface.", "danger")
        return redirect(url_for('profile_page'))

    # Find all pets owned by the current user
    pets_to_delete = list(mongo.db.pets.find({"owner_id": ObjectId(current_user.id)}))
    pet_ids_to_delete = [pet['_id'] for pet in pets_to_delete]

    # If the user has pets, delete their health reports first
    if pet_ids_to_delete:
        mongo.db.health_reports.delete_many({"pet_id": {"$in": pet_ids_to_delete}})

    # Delete all pets owned by the user
    mongo.db.pets.delete_many({"owner_id": ObjectId(current_user.id)})

    # If the user is a vet, remove their links to consulted pets
    if current_user.is_vet:
        mongo.db.vet_pet_links.delete_many({"vet_id": ObjectId(current_user.id)})

    # Finally, delete the user themselves
    mongo.db.users.delete_one({"_id": ObjectId(current_user.id)})

    logout_user()
    flash("Your account and all associated data have been permanently deleted.", "success")
    return redirect(url_for('home_page'))

@app.route('/remove_pet/<pet_id>', methods=['POST'])
@login_required
def remove_pet_page(pet_id):
    pet_to_delete = Pet.get_by_id(pet_id)
    if pet_to_delete and (pet_to_delete['owner_id'] == ObjectId(current_user.id) or current_user.is_admin):
        mongo.db.pets.delete_one({"_id": ObjectId(pet_id)})
        mongo.db.health_reports.delete_many({"pet_id": ObjectId(pet_id)})
        flash('Pet has been removed successfully!', 'success')
    else:
        flash('Pet not found or you do not have permission.', 'danger')
    return redirect(url_for('profile_page'))


# ==============================================================================
# 6. HEALTH ANALYSIS & VETERINARIAN FEATURES
# ==============================================================================

@app.route('/select_pet')
@login_required
def select_pet_page():
    if current_user.is_vet or current_user.is_admin:
        all_pets = list(mongo.db.pets.find())
    else:
        all_pets = current_user.get_pets()
    # Logic to identify which pets a vet has already consulted
    consulted_pet_ids = []
    if current_user.is_vet:
        links = mongo.db.vet_pet_links.find({"vet_id": ObjectId(current_user.id)})
        consulted_pet_ids = [str(link['pet_id']) for link in links]
    return render_template('select_pet.html', pets=all_pets, consulted_pet_ids=consulted_pet_ids)


@app.route('/analyze_pet_health/<pet_id>', methods=['GET'])
@login_required
def analyze_pet_health_page(pet_id):
    selected_pet = Pet.get_by_id(pet_id)
    if not (current_user.is_vet or current_user.is_admin) and selected_pet.get('owner_id') != ObjectId(current_user.id):
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main_page'))
    age = None
    if selected_pet.get('dob'):
        dob = selected_pet['dob']
        today = datetime.utcnow()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return render_template('analyze_pet_health.html', selected_pet=selected_pet, pet_id=pet_id, age=age, breed=selected_pet.get('breed'))


@app.route('/ai_pet_advisor')
@login_required
def ai_pet_advisor_page():
    """Renders the AI Pet Advisor page and passes the API key."""
    # Get the API key from your environment variables
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    # Pass the key to the template
    return render_template('ai_pet_advisor.html', gemini_api_key=gemini_api_key)



@app.route('/predict_health', methods=['POST'])
@login_required
def predict_health():
    try:
        data = request.get_json()
        species = data.get('species')
        temp = float(data.get('temperature') or 0)
        hr = int(data.get('heart_rate') or 0)
        rr = int(data.get('respiratory_rate') or 0)
        weight = float(data.get('weight') or 0)

        vital_ranges = {
            "Dog": {"temp": (35, 42), "hr": (40, 240), "rr": (5, 60)},
            "Cat": {"temp": (36, 41), "hr": (120, 260), "rr": (15, 50)},
            "Horse": {"temp": (36, 40), "hr": (20, 80), "rr": (8, 40)}
        }
        if species in vital_ranges:
            ranges = vital_ranges[species]
            if not (ranges['temp'][0] <= temp <= ranges['temp'][1]):
                return jsonify({"error": f"Impossible Temperature for a {species}. Must be between {ranges['temp'][0]} and {ranges['temp'][1]}."}), 400
            if not (ranges['hr'][0] <= hr <= ranges['hr'][1]):
                return jsonify({"error": f"Impossible Heart Rate for a {species}. Must be between {ranges['hr'][0]} and {ranges['hr'][1]}."}), 400
            if not (ranges['rr'][0] <= rr <= ranges['rr'][1]):
                return jsonify({"error": f"Impossible Respiratory Rate for a {species}. Must be between {ranges['rr'][0]} and {ranges['rr'][1]}."}), 400

        pet_id = data.get('pet_id')
        model_input = {
            'species': species, 'breed': data.get('breed'), 'age': float(data.get('age')), 'weight': weight,
            'temperature': temp, 'heart_rate': hr, 'respiratory_rate': rr,
            'vaccination_status': data.get('vaccination_status'), 'hydration': data.get('hydration'),
            'activity_level': data.get('activity_level'), 'diet': data.get('diet')
        }
        features_df = pd.DataFrame([model_input])
        for col in ['species', 'breed', 'vaccination_status', 'hydration', 'activity_level', 'diet']:
            le = encoders[col]
            features_df[col] = features_df[col].apply(lambda x: le.transform([x])[0] if x in le.classes_ else -1)

        symptoms_list = data.get('symptoms', ['None'])
        mlb = encoders['symptoms']
        symptoms_encoded = mlb.transform([symptoms_list])
        symptom_df = pd.DataFrame(symptoms_encoded, columns=[str(c) for c in mlb.classes_], index=features_df.index)
        features_df = pd.concat([features_df, symptom_df], axis=1)

        model_feature_names = [str(col) for col in model.feature_names_in_]
        features_df.columns = [str(col) for col in features_df.columns]
        for col in model_feature_names:
            if col not in features_df.columns:
                features_df[col] = 0
        features_df = features_df[model_feature_names]

        predicted_status = model.predict(features_df)[0]
        confidence = round(np.max(model.predict_proba(features_df)) * 100)

        result = {}
        if predicted_status == 'Healthy':
            result = {'status': 'Healthy', 'description': 'Overall health is excellent.', 'health_score': 100, 'confidence': f'{confidence}%', 'immediate_actions': ['Continue with regular care.'], 'lifestyle_changes': ['Maintain a balanced diet and regular exercise.'], 'monitoring_plan': ['Annual check-ups.'], 'vet_care': {'Annual dental cleaning': 'Medium', 'Regular parasite prevention': 'Medium'}}
        elif predicted_status == 'At Risk':
            result = {'status': 'At Risk', 'description': 'Minor issues detected that require monitoring.', 'health_score': 65, 'confidence': f'{confidence}%', 'immediate_actions': ['Schedule a non-urgent vet consultation.', 'Monitor symptoms closely.'], 'lifestyle_changes': ['Review diet for potential allergens.'], 'monitoring_plan': ['Check vital signs daily.'], 'vet_care': {'Diagnostic tests (blood work)': 'High', 'Follow-up consultation': 'High'}}
        else:
            result = {'status': 'Unhealthy', 'description': 'Significant health concerns detected.', 'health_score': 30, 'confidence': f'{confidence}%', 'immediate_actions': ['Seek veterinary care immediately.'], 'lifestyle_changes': ['Provide a comfortable resting area.'], 'monitoring_plan': ["Follow the veterinarian's treatment plan precisely."], 'vet_care': {'Emergency veterinary visit': 'Critical', 'Advanced imaging': 'High'}}

        report_input_data = model_input.copy()
        report_input_data['symptoms'] = ", ".join(symptoms_list)
        vet_id = current_user.id if current_user.is_vet else None
        HealthReport.create(pet_id, report_input_data, result, vet_id)
        return jsonify(result)
    except Exception as e:
        print(f"Error in /predict_health: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "An internal server error occurred."}), 500


@app.route('/pet_health_history/<pet_id>')
@login_required
def pet_health_history_page(pet_id):
    pet = Pet.get_by_id(pet_id)
    if not (current_user.is_vet or current_user.is_admin) and pet['owner_id'] != ObjectId(current_user.id):
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main_page'))
    history = Pet.get_health_history(pet_id)
    return render_template('pet_health_history.html', pet=pet, history=history)


@app.route('/delete_health_report/<report_id>', methods=['POST'])
@login_required
def delete_health_report(report_id):
    report_to_delete = mongo.db.health_reports.find_one({"_id": ObjectId(report_id)})
    if not report_to_delete:
        flash("Health report not found.", "danger")
        return redirect(url_for('main_page'))
    pet = Pet.get_by_id(report_to_delete['pet_id'])
    if pet and str(pet['owner_id']) == current_user.id:
        mongo.db.health_reports.delete_one({"_id": ObjectId(report_id)})
        flash("Health report has been successfully deleted.", "success")
    else:
        flash("You do not have permission to delete this report.", "danger")
    return redirect(url_for('pet_health_history_page', pet_id=report_to_delete['pet_id']))


@app.route('/delete_selected_reports', methods=['POST'])
@login_required
def delete_selected_reports():
    report_ids_str = request.form.get('report_ids_to_delete')
    pet_id = request.form.get('pet_id')
    if not report_ids_str or not pet_id:
        flash("Invalid request. Please try again.", "danger")
        return redirect(url_for('main_page'))
    pet = Pet.get_by_id(pet_id)
    if not pet or str(pet['owner_id']) != current_user.id:
        flash("You do not have permission to perform this action.", "danger")
        return redirect(url_for('pet_health_history_page', pet_id=pet_id))
    report_ids = [ObjectId(id) for id in report_ids_str.split(',')]
    result = mongo.db.health_reports.delete_many({"_id": {"$in": report_ids}})
    if result.deleted_count > 0:
        flash(f"Successfully deleted {result.deleted_count} health report(s).", "success")
    else:
        flash("No reports were deleted.", "warning")
    return redirect(url_for('pet_health_history_page', pet_id=pet_id))


@app.route('/consult_veterinarian')
@login_required
def consult_veterinarian_page():
    vets = list(mongo.db.users.find({"is_vet": True}))
    return render_template('consult_veterinarian.html', vets=vets)


@app.route('/add_consulted_pet/<pet_id>', methods=['POST'])
@login_required
def add_consulted_pet(pet_id):
    if not current_user.is_vet:
        flash("Only veterinarians can perform this action.", "danger")
        return redirect(url_for('select_pet_page'))
    existing_link = mongo.db.vet_pet_links.find_one({"vet_id": ObjectId(current_user.id), "pet_id": ObjectId(pet_id)})
    if existing_link:
        flash("This pet is already in your consulted list.", "info")
    else:
        mongo.db.vet_pet_links.insert_one({"vet_id": ObjectId(current_user.id), "pet_id": ObjectId(pet_id), "date_added": datetime.utcnow()})
        flash("Pet added to your consulted list.", "success")
    return redirect(url_for('select_pet_page'))


@app.route('/remove_consulted_pet/<pet_id>', methods=['POST'])
@login_required
def remove_consulted_pet(pet_id):
    if not current_user.is_vet:
        flash("Only veterinarians can perform this action.", "danger")
        return redirect(url_for('vet_dashboard_page'))
    mongo.db.vet_pet_links.delete_one({"vet_id": ObjectId(current_user.id), "pet_id": ObjectId(pet_id)})
    flash("Pet removed from your consulted list.", "success")
    return redirect(request.referrer or url_for('vet_dashboard_page'))


# ==============================================================================
# 7. VET & ADMIN DASHBOARDS
# ==============================================================================

@app.route('/vet_dashboard')
@login_required
def vet_dashboard_page():
    if not current_user.is_vet:
        flash("You are not authorized to view this page.", "danger")
        return redirect(url_for('main_page'))
    links = mongo.db.vet_pet_links.find({"vet_id": ObjectId(current_user.id)})
    consulted_pet_ids = [link['pet_id'] for link in links]
    consulted_pets = list(mongo.db.pets.find({"_id": {"$in": consulted_pet_ids}}))
    return render_template('vet_dashboard.html', consulted_pets=consulted_pets)


@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard_page():
    if not current_user.is_admin:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('main_page'))
    form = AddVet()
    if form.validate_on_submit():
        if not VetLicense.get(form.vet_license.data):
            mongo.db.vetlicenses.insert_one({"vet_license": form.vet_license.data})
            flash('Vet License added successfully!', 'success')
        else:
            flash('Vet License already exists!', 'danger')
        return redirect(url_for('admin_dashboard_page'))
    licenses = list(mongo.db.vetlicenses.find())
    return render_template('admin_dashboard.html', form=form, licenses=licenses)