# E-Learning Django Project

This is a **Django-based e-learning website** that allows users to sign up, log in, and manage their learning activities.

## Features

* **User Authentication:** Sign up and login.
* **User Profile:**

  * Home
  * Learner Dashboard
  * Update Modules (choose modules to learn)
  * Take Assignments (related to chosen modules)
  * Read Courses (related to modules)
  * Grades
  * Announcements (notifications for new courses)
* **Manager Profile** for managing content and users.
* Active notifications for updates.

## Project Setup

### 1. Clone the repository

```bash
git clone https://github.com/raghadisraghad/e-learning-website
cd e-learning-website
```

### 2. Create and activate virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.1. Apply migrations

```bash
python manage.py migrate
```

### 4.2. Create superuser:

```bash
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

Open your browser and go to:

```
http://127.0.0.1:8000/
```

### 6. Additional Notes

* The project uses **SQLite** database (default Django DB).
* Notifications are active for new course additions.
* Update your modules in the profile to personalize your learning experience.
