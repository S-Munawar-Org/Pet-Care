# PetCare - Intelligent Pet Health Management

PetCare is a modern web application designed to empower pet owners and veterinarians with the tools they need to manage and monitor pet health effectively. By leveraging cutting-edge machine learning and generative AI, the platform provides data-driven insights, personalized recommendations, and a centralized system for tracking a pet's health history.

## ✨ Key Features

* **AI-Powered Pet Advisor:**
    * **Ask Anything:** Get instant, detailed advice on your pet's health, diet, and training by asking questions in natural language.
    * **Diet & Training Plans:** Generate custom weekly diet plans and step-by-step training guides tailored to your pet's specific needs.
    * **Dynamic Image Generation:** Receive a gallery of beautiful, AI-generated images related to your query, bringing the advice to life.
* **Intelligent Health Analysis:** Get instant health assessments (Healthy, At-Risk, Unhealthy) based on a pet's vital signs, symptoms, and lifestyle factors.
* **Comprehensive Pet Profiles:** Manage detailed profiles for multiple pets, including their species, breed, gender, and date of birth.
* **Complete Health History:** Keep a chronological record of all health analyses, making it easy to track a pet's wellness over time and share it with professionals.
* **Veterinarian & Admin Dashboards:** Dedicated portals for veterinarians to manage consulted pets and for administrators to approve new veterinarian licenses.
* **Secure Authentication:** Robust login system with email verification and Google OAuth for both pet owners and veterinarians.
* **Light & Dark Mode:** A modern, theme-able user interface for a comfortable viewing experience.

## 📸 Screenshots

| Register | Login |
| :--- | :--- |
| ![Register Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Register.png) | ![Login Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Login.png) |
| **Home** | **Add Pet** |
| ![Home Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Home.png) | ![Add Pet Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Add_Pet.png) |
| **Health Analysis** | **Consult Veterinarian** |
| ![Health Analysis](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Health_Analysis.png) | ![Consult Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Consult_vet.png) |
| **Profile** | **AI Pet Advisor** |
| ![Profile Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/Profile.png) | ![AI Pet Advisor Page](https://raw.githubusercontent.com/S-Munawar/Pet-Care/main/static/images/AI_Pet_Advisor.png) |

## 🛠️ Technology Stack

![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![Scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)
![Bootstrap](httpshttps://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

* **Backend:** Flask, Flask-Login, Flask-Bcrypt, Gunicorn
* **Database:** MongoDB (with Flask-PyMongo)
* **Machine Learning:** Scikit-learn, Pandas, NumPy
* **Generative AI:** Google Gemini API (for text), Google Imagen API (for images)
* **Frontend:** HTML, CSS, JavaScript, Bootstrap
* **Authentication:** Google OAuth, Flask-Mail for email verification
* **Deployment:** Docker

## 🚀 Getting Started

Follow these instructions to get a local copy of the project up and running.

### Prerequisites

* Python 3.9 or higher
* A running MongoDB instance (local or cloud-based)
* A Google AI API Key
* Docker (for containerized deployment)

### Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/S-Munawar/Pet-Care.git](https://github.com/S-Munawar/Pet-Care.git)
    cd Pet-Care
    ```

2.  **Create and Activate a Virtual Environment**
    ```bash
    # On Windows
    python -m venv venv
    venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    * Create a file named `.env` in the root of the project.
    * Add your configuration details to this file. It must include your MongoDB connection string, a secret key, email credentials, and your Google AI API key.
        ```env
        SECRET_KEY='a_very_long_and_random_secret_key'
        MONGO_URI='your_mongodb_connection_string'
        
        # Get this from Google AI Studio. It is required for the AI Pet Advisor.
        GEMINI_API_KEY='your_google_ai_api_key'
        
        # Example for local MongoDB:
        # MONGO_URI='mongodb://localhost:27017/petcare_db'
        
        # Email Configuration (for verification emails)
        MAIL_SERVER='smtp.gmail.com'
        MAIL_PORT=587
        MAIL_USE_TLS=True
        MAIL_USERNAME='your_email@gmail.com'
        MAIL_PASSWORD='your_app_password' 
        ```

### Running the Application

Once everything is installed and configured, you can start the Flask development server:

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`.

### Creating an Admin User

To create the first administrator account, run the `create_admin.py` script from your **terminal** (not the IDE's run console):

```bash
python create_admin.py
```

Follow the prompts to set up the username, email, and password for the admin account.

## 🐳 Docker Deployment

You can also run the application in a Docker container for a standardized deployment.

1.  **Build the Docker Image**
    ```bash
    docker build -t petcare-app .
    ```

2.  **Run the Docker Container**
    * Make sure to provide your `MONGO_URI` and `GEMINI_API_KEY` as environment variables.
    ```bash
    docker run -d -p 5000:5000 --restart always \
      -e MONGO_URI="your_mongodb_connection_string" \
      -e GEMINI_API_KEY="your_google_ai_api_key" \
      --name petcare-container \
      petcare-app
    ```

## Author

**Shaik Abdul Munawar**

* [LinkedIn Profile](https://www.linkedin.com/in/shaik-abdul-munawar-b35821284)
