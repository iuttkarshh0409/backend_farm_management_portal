# Farm Management Portal 🐄

**Farm Management Portal** is a comprehensive, production-ready REST API backend that digitalizes and modernizes farm operations. By leveraging cutting-edge web technologies and robust database design, it provides complete livestock management, health record tracking, and multi-role user authentication with specialized dashboards for farmers, veterinarians, and administrators.

---

## 📋 Table of Contents

- [Features](#-features)
- [Technology Stack](#️-technology-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#-prerequisites)
  - [Installation](#️-installation)
- [API Documentation](#-api-documentation)
- [Authentication](#-authentication)
- [Database Schema](#-database-schema)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Project Lead](#-project-lead)
- [License](#-license)
- [Contact](#-contact)

---

## ✨ Features

- **Multi-Role Authentication**: Secure JWT-based authentication system supporting farmers, veterinarians, and administrators with role-based access control.
- **Livestock Management**: Complete animal registration, tracking, and profile management with multi-species support (cattle, buffalo, goat, sheep, poultry).
- **Health Record System**: Comprehensive medical history tracking with veterinarian integration, treatment records, and appointment scheduling.
- **Dashboard Analytics**: Data-driven insights with specialized dashboards for farmers, veterinarians, and administrators showing real-time statistics.
- **Veterinary Services**: Advanced vet-animal assignment system with appointment scheduling and treatment tracking capabilities.
- **Search & Filtering**: Powerful animal search functionality with filters by species, health status, and production metrics.
- **Production Ready**: Professional-grade architecture with comprehensive error handling, input validation, and security measures.

---

## 🛠️ Technology Stack

- **Backend**: Python, Flask
- **Database ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Database**: SQLite (Development), PostgreSQL (Production)
- **Security**: bcrypt, CORS, Input Validation
- **API Design**: RESTful Architecture
- **Testing**: pytest, API Testing Suite

---

## 🚀 Getting Started

Set up and run the Farm Management Portal locally with these steps.

### 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git
- SQLite (included with Python) or PostgreSQL (for production)

### 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/farm-management-portal.git
   ```

2. **Navigate to the Project Directory**
   ```bash
   cd farm-management-portal
   ```

3. **Set Up a Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```bash
   # Database Configuration
   DATABASE_URL=sqlite:///farm_portal.db
   
   # JWT Configuration
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
   JWT_ACCESS_TOKEN_EXPIRES=3600
   JWT_REFRESH_TOKEN_EXPIRES=2592000
   
   # Flask Configuration
   FLASK_ENV=development
   FLASK_DEBUG=1
   SECRET_KEY=your-flask-secret-key-change-in-production
   
   # Optional: SMS/Email Configuration
   TWILIO_ACCOUNT_SID=your-twilio-sid
   TWILIO_AUTH_TOKEN=your-twilio-token
   MAIL_SERVER=smtp.gmail.com
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-email-password
   ```

6. **Initialize the Database**
   ```bash
   python run.py
   # This will create the database and tables automatically
   ```

7. **Run the Application**
   ```bash
   python run.py
   ```
   Visit `http://127.0.0.1:5000` in your browser. The API will be available at `http://127.0.0.1:5000/api/v1`.

---

## 🌐 API Documentation

### Base URL
```
http://127.0.0.1:5000/api/v1
```

### Core Endpoints

#### Authentication
- `POST /auth/login` - User login
- `POST /auth/refresh` - Refresh JWT token  
- `POST /auth/logout` - User logout

#### User Management
- `POST /users/register/farmer` - Register farmer
- `POST /users/register/veterinarian` - Register veterinarian
- `POST /users/verify` - Verify account with OTP
- `GET /users/{id}` - Get user profile
- `PUT /users/{id}/profile` - Update user profile

#### Animal Management
- `POST /animals` - Register new animal
- `GET /animals` - List animals (role-filtered)
- `GET /animals/{id}` - Get animal details
- `PUT /animals/{id}` - Update animal profile
- `POST /animals/{id}/assign-vet` - Assign veterinarian
- `GET /animals/search` - Search animals with filters

#### Health Records
- `POST /animals/{id}/health-records` - Create health record
- `GET /animals/{id}/health-records` - Get health history

#### Dashboard APIs
- `GET /farmers/{id}/dashboard` - Farmer dashboard
- `GET /veterinarians/{id}/dashboard` - Veterinarian dashboard
- `GET /animals/stats` - System statistics (admin)

### Sample API Calls

**Register Farmer:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/users/register/farmer \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Farmer",
    "email": "john@farm.com", 
    "phone": "9876543210",
    "password": "SecurePass123!",
    "farm_name": "Green Valley Farm"
  }'
```

**Login User:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@farm.com",
    "password": "SecurePass123!"
  }'
```

**Register Animal:**
```bash
curl -X POST http://127.0.0.1:5000/api/v1/animals \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "tag_id": "COW001",
    "name": "Lakshmi",
    "species": "cattle",
    "gender": "female",
    "health_status": "healthy"
  }'
```

---

## 🔐 Authentication

The API uses **JWT (JSON Web Tokens)** for secure, stateless authentication.

### Token Types
- **Access Token**: Short-lived (1 hour) for API access
- **Refresh Token**: Long-lived (30 days) for token renewal

### User Roles & Permissions
| Role | Permissions |
|------|-------------|
| **Farmer** | Register animals, view own animals, assign vets, view health records |
| **Veterinarian** | View assigned animals, create health records, manage treatments |
| **Administrator** | Full system access, user management, analytics, all operations |

### Security Features
- 🔒 bcrypt password hashing
- 🔑 JWT token security with expiration
- 📱 OTP account verification
- 🛡️ Comprehensive input validation
- 🚫 SQL injection prevention
- 🌐 CORS configuration

---

## 💾 Database Schema

### Key Models

**User Model (Base)**
- Multi-role inheritance (Farmer, Veterinarian, Admin)
- Secure authentication with password hashing
- Account verification and status management

**Animal Model**
- Unique tag-based identification
- Multi-species support with breed tracking
- Health status and production monitoring
- Farmer-veterinarian relationships

**Health Record Model**  
- Comprehensive medical history tracking
- Veterinarian-recorded treatments
- Appointment scheduling and follow-ups

### Relationships
```
Users (1) ←→ (N) Animals ←→ (N) HealthRecords
  ↓              ↓
Farmers     Veterinarians
```

---

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies (if not already installed)
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage report
pytest --cov=app

# Run specific test category
pytest tests/test_auth.py -v
```

### Manual API Testing
```bash
# Test server health
curl http://127.0.0.1:5000/health

# Test user registration
curl -X POST http://127.0.0.1:5000/api/v1/users/register/farmer \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","phone":"1234567890","password":"Test123!"}'

# Test authentication
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test123!"}'
```

### Test Coverage
- ✅ User authentication & authorization
- ✅ Animal registration & management  
- ✅ Health record CRUD operations
- ✅ Role-based access control
- ✅ Input validation & error handling
- ✅ Dashboard functionality

---

## 🛠️ Troubleshooting

- **Import Errors**: Ensure virtual environment is activated and all dependencies are installed (`pip install -r requirements.txt`).
- **Database Issues**: Check if `farm_portal.db` file is created. Delete and restart if corrupted.
- **Flask Not Starting**: Verify Python version (3.8+) and Flask installation (`pip show flask`).
- **JWT Token Errors**: Ensure `JWT_SECRET_KEY` is set in `.env` file.
- **Permission Denied**: Check file permissions and virtual environment activation.
- **Port Already in Use**: Change port in `run.py` or kill existing Flask processes.

For further issues, check the [GitHub Issues](https://github.com/yourusername/farm-management-portal/issues) page.

---

## 🤝 Contributing

We welcome contributions to make Farm Management Portal even better! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m 'Add YourFeature'`).
4. Push to the branch (`git push origin feature/YourFeature`).
5. Open a Pull Request.

### Development Guidelines
- Follow PEP 8 Python style guidelines
- Write tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting PR

See our [Contributing Guidelines](CONTRIBUTING.md) for more details.

---



- **[Your Name]** - *Full Stack Developer & Project Architect*  
  GitHub: [yourusername](https://github.com/iuttkarshh0409) | Email: [dubeyutkarsh](mailto:your.email@domain.com)@gmail.com

---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 📬 Contact

For questions, bug reports, or feature requests:
- 🐛 **Issues**: [GitHub Issues](https://github.com/yourusername/farm-management-portal/issues)
- 📧 **Email**: [your.email@domain.com](mailto:your.email@domain.com)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/farm-management-portal/discussions)

---

🚀 **Digitize, Manage, Scale with Farm Management Portal!**