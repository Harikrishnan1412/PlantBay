PlantBay 🌱🛒
PlantBay is an E-Commerce platform designed for buying and selling plants. Built using Django, Bootstrap, AJAX, and the All-auth library, PlantBay offers a seamless shopping experience with robust features for both users and administrators.

Key Features
User Authentication: Secure email-based login, sign-up, password reset, and verification.
Product Management: Category-wise filters and a powerful search function for easy navigation.
Promo Code Discounts: Apply promo codes during checkout for discounts.
Stripe Integration: Secure payment gateway integration for smooth transactions.
Email Notifications: Automated payment confirmations and order updates sent to users.
Admin Dashboard: Manage coupons, handle refunds, and analyze orders with advanced filtering options.
Getting Started
To run PlantBay locally:

Clone this repository.
Set up your Python environment and install dependencies:
Copy code
pip install -r requirements.txt
Configure your database settings in settings.py.
Apply migrations and create a superuser:
Copy code
python manage.py migrate
python manage.py createsuperuser
Start the development server:
Copy code
python manage.py runserver
Access the admin dashboard at http://127.0.0.1:8000/admin/ to manage the platform.
Contributing
Contributions are welcome! Please fork this repository and submit pull requests to contribute new features, fix bugs, or improve documentation.
