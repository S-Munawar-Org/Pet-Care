import os
import getpass
from pymongo import MongoClient
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv


def create_admin_user():
    """
    A secure command-line tool to create the first admin user.
    Loads database configuration from the .env file.
    """
    # Load environment variables from .env file
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")

    if not mongo_uri:
        print("\nError: MONGO_URI not found in your .env file.")
        print("Please ensure your .env file is correctly configured.")
        return

    client = None  # Initialize client to None
    try:
        client = MongoClient(mongo_uri)
        db = client.petcare_db  # Specify database name
        users_collection = db.users
        bcrypt = Bcrypt()
    except Exception as e:
        print(f"\nError: Could not connect to the database.")
        print(f"Details: {e}")
        return

    print("--- Create PetCare Admin User ---")

    # Check if an admin already exists
    if users_collection.find_one({"is_admin": True}):
        print("\nAn admin account already exists. No new admin will be created.")
        client.close()
        return

    # Get admin details from user input
    username = input("Enter admin username: ").strip().title()
    email = input("Enter admin email: ").strip().lower()

    # Securely get password
    password = getpass.getpass("Enter admin password: ")
    confirm_password = getpass.getpass("Confirm admin password: ")

    # Validate input
    if not all([username, email, password]):
        print("\nError: Username, email, and password are required.")
        client.close()
        return

    if password != confirm_password:
        print("\nError: Passwords do not match.")
        client.close()
        return

    if users_collection.find_one({"username": username}):
        print(f"\nError: Username '{username}' already exists.")
        client.close()
        return

    if users_collection.find_one({"email": email}):
        print(f"\nError: Email '{email}' already exists.")
        client.close()
        return

    # Hash the password and create the admin user
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    admin_data = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "phone": "",  # Admin can add this later via profile page
        "address": "",  # Admin can add this later
        "is_vet": False,
        "is_admin": True,
        "verified": True  # Admins are verified by default
    }

    try:
        users_collection.insert_one(admin_data)
        print(f"\nAdmin user '{username}' created successfully!")
        print("You can now log in using the main /login route.")
    except Exception as e:
        print(f"\nError: Could not create admin user in the database.")
        print(f"Details: {e}")
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    create_admin_user()