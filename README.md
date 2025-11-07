# 🚗⚡ EV Charging Station Booking System

A comprehensive web application for managing Electric Vehicle (EV) charging station bookings with integrated wallet system, real-time location tracking, and admin management.

## 🌟 Features

### For Users:
- 🔍 **Browse Stations**: Search and filter charging stations by location, price, rating, and amenities
- 📍 **Location-Based Sorting**: Automatically shows nearby stations first using GPS
- 🗺️ **Interactive Map View**: View all stations on Google Maps with markers
- 📅 **Book Stations**: Reserve charging slots with flexible time duration (30 mins to 5+ hours)
- ⚡ **Charger Power Selection**: Choose from different charging speeds (3kW to 120kW)
- 💰 **Digital Wallet**: Add money, view transaction history, and manage balance
- 🧭 **Navigation**: Get directions from current location to charging station
- ⭐ **Reviews & Ratings**: Rate and review charging stations
- 🔖 **Bookmarks**: Save favorite stations for quick access
- 🔔 **Notifications**: Real-time updates for bookings and payments
- 📊 **Dashboard**: View booking history, wallet balance, and statistics

### For Admins:
- 🏢 **Station Management**: Add, update, and delete charging stations
- 👥 **User Management**: View all registered users
- 💳 **Payment Approval**: Approve/reject user wallet top-up requests
- 📋 **Booking Overview**: Monitor all bookings across the platform
- 📈 **Analytics**: Track system usage and statistics

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: HTML, CSS, Bootstrap 5
- **JavaScript**: Vanilla JS for interactivity
- **APIs**: Google Maps API for navigation and location services

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)
- Modern web browser

## 🚀 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/vaibhav-049/EV-Charging-Station-Booking-System.git
   cd EV-Charging-Station-Booking-System
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python import_sqlite.py
   ```

4. **Add coordinates to stations (for map view)**
   ```bash
   python add_coordinates.py
   ```

5. **Run the application**
   ```bash
   python run_flask.py
   ```

6. **Access the application**
   - Open browser and go to: `http://127.0.0.1:5000`
   - For mobile access on same WiFi: `http://<your-ip>:5000`

## 📱 Mobile Access

To access from phone on same WiFi network:
1. Find your computer's IP address: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
2. Open browser on phone
3. Visit: `http://<your-ip>:5000`

## 🔐 Default Credentials

**Admin Login:**
- Username: `admin`
- Password: `admin`

**Test User:**
- Create a new account via signup page

## 📊 Database Schema

The application uses 9 tables:
1. `ev_charging_stations_reduced` - Station details with coordinates
2. `users` - User accounts
3. `wallets` - User wallet balances
4. `wallet_transactions` - Transaction history
5. `payment_requests` - Wallet top-up requests
6. `bookings` - Station reservations
7. `reviews` - User reviews and ratings
8. `bookmarks` - Saved favorite stations
9. `comments` - Station comments
10. `notifications` - User notifications

## 🎯 Usage Guide

### Booking a Station:
1. Login/Signup as a user
2. Browse available stations
3. Click "Book Now" on desired station
4. Select charger power (affects cost)
5. Choose date, time, and duration
6. Confirm booking (amount deducted from wallet)
7. Use "Get Directions" for navigation

### Adding Money to Wallet:
1. Go to Wallet page
2. Enter amount and payment details
3. Submit payment request
4. Wait for admin approval
5. Balance updated automatically upon approval

### Admin Operations:
1. Login as admin
2. Manage stations, users, payments, and bookings
3. Approve/reject payment requests
4. Monitor system activity

## 🌈 Key Highlights

- ✅ **Real-time Cost Calculator**: Automatic cost calculation based on power and duration
- ✅ **GPS Integration**: Location-based station sorting with distance display
- ✅ **Wallet System**: Secure payment handling with transaction history
- ✅ **Booking Cancellation**: Instant refunds to wallet
- ✅ **Responsive Design**: Works seamlessly on desktop and mobile
- ✅ **Admin Approval Workflow**: Secure payment verification process
- ✅ **Notification System**: Keep users informed about important events

## 📁 Project Structure

```
dbms_pbl/
├── flask_app/
│   ├── __init__.py
│   └── routes.py
├── templates/
│   ├── base.html
│   ├── landing.html
│   ├── index.html
│   ├── station_detail.html
│   ├── book_station.html
│   ├── user_*.html
│   └── admin_*.html
├── static/
│   └── css/
│       └── *.css
├── database/
│   └── ev_stations.db
├── app_db.py
├── run_flask.py
├── import_sqlite.py
├── add_coordinates.py
└── requirements.txt
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available for educational purposes.

## 👨‍💻 Developer

**Vaibhav Rajput**
- GitHub: [@vaibhav-049](https://github.com/vaibhav-049)
- Email: rvaibhav403@gmail.com

## 🙏 Acknowledgments

- EV charging station data for Indian locations
- Bootstrap for responsive UI components
- Google Maps API for location services

## 📞 Support

For issues or questions, please open an issue on GitHub or contact the developer.

---

**Made with ❤️ for a greener future! 🌱**
