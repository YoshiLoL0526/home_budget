# 🏠 Home Budget 💸

## 📝 Description

A robust Python web application built with Django framework for managing personal home finances and budgeting. Features a responsive user interface using Bootstrap 5 for a modern and intuitive experience. This tool helps users track expenses, create budgets, and make informed financial decisions through an easy-to-use web dashboard.

## ⭐ Key Features

### Financial Management

- 💰 Track income and expenses
- 📊 Create and manage monthly/yearly budgets
- 🏷️ Transaction categorization
- 📱 Mobile-friendly responsive interface

### Analytics & Reporting

- 📈 Generate detailed financial reports
- 📉 Interactive graphs and metrics
- 📆 Month-to-month comparison

### User Experience

- 🎨 Personalized profile settings
- 🔔 Custom alerts and notifications (Not implemented yet)
- 🔒 Secure data encryption
- 💾 Automatic data backup

## 🚀 Installation

```bash
git clone https://github.com/yoshilol0526/home_budget.git
cd home_budget
pip install -r requirements.txt
```

## ⚙️ Configuration

### 🔧 Setup environment vars

```env
SECRET_KEY = your-secret-key
DEBUG = True   # Use False for production
ALLOWED_HOSTS = *

CSRF_TRUSTED_ORIGINS = http://localhost

DB_USER = postgres-user
DB_PASSWORD = postgres-password
DB_HOST = postgres-host
DB_PORT = 5432
DB_NAME = db-name
```

### 🗃️ Migrate the database

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

## 🎯 Usage

```bash
python manage.py runserver
```

## 🤝 Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## 📜 License

MIT License - See LICENSE file for details
