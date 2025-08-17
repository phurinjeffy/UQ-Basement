# UQ-Basement 🎓

**AI-Powered Mock Exam Platform for University of Queensland Students**

UQ-Basement is an intelligent web application that revolutionizes exam preparation by automatically generating mock exams from past papers using AI. Built for the UQCS Hackathon 2025, it provides UQ students with personalized practice exams, AI-powered answer checking, and comprehensive study tools.

## 🌟 Features

### 📚 Past Papers Management
- **Automated Download**: Seamlessly downloads past papers from UQ Library resources
- **Smart Organization**: Sorts papers by year and semester for easy navigation
- **PDF Viewer**: Built-in PDF viewer with AI assistance for solving questions
- **S3 Storage**: Efficient cloud storage for all past paper documents

### 🤖 AI-Powered Mock Exams
- **Question Generation**: AI extracts and generates practice questions from past papers
- **Multiple Question Types**: Supports multiple choice, short answer, essay, and calculation questions
- **Intelligent Parsing**: Advanced text processing to identify and format questions properly
- **Answer Validation**: AI-powered answer checking with detailed feedback

### 📋 Quiz System
- **Interactive Interface**: Clean, responsive quiz interface with progress tracking
- **Auto-save**: Automatic saving of answers to prevent data loss
- **Timed Exams**: Configurable time limits for realistic exam simulation
- **Results Analysis**: Comprehensive feedback on performance with correct answers

### 👤 User Management
- **Authentication**: Secure JWT-based authentication system
- **Course Enrollment**: Track enrolled courses and exam schedules
- **Personal Dashboard**: Overview of courses, upcoming exams, and progress
- **Profile Management**: User settings and preferences

## 🏗️ Architecture

### Backend (FastAPI)
```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration and environment setup
├── models.py            # Pydantic models for API validation
├── requirements.txt     # Python dependencies
├── ai/                  # AI processing modules
│   ├── download_past_papers.py    # Selenium-based paper downloader
│   ├── llama_exam_processor.py    # Question generation from papers
│   └── llama_answer_processor.py  # Answer checking and validation
└── routers/            # API endpoint modules
    ├── users.py        # User authentication and management
    ├── courses.py      # Course information and enrollment
    ├── quiz.py         # Quiz creation and management
    ├── questions.py    # Question handling
    ├── answers.py      # Answer submission and checking
    ├── enrollments.py  # Course enrollment tracking
    └── ai.py          # AI-powered features and integrations
```

### Frontend (React + Vite)
```
frontend/
├── src/
│   ├── pages/          # Main application pages
│   │   ├── Home.jsx           # Landing page
│   │   ├── Dashboard.jsx      # User dashboard
│   │   ├── MockExam.jsx       # Main exam interface
│   │   ├── Profile.jsx        # User profile
│   │   └── NotFound.jsx       # 404 page
│   ├── components/     # Reusable components
│   │   ├── Navbar.jsx         # Navigation component
│   │   ├── PDFWithAI.jsx      # PDF viewer with AI assistance
│   │   ├── AddCourses.jsx     # Course enrollment component
│   │   ├── Breadcrumbs.jsx    # Navigation breadcrumbs
│   │   └── PrivateRoute.jsx   # Protected route wrapper
│   ├── context/        # React context providers
│   │   └── AuthContext.jsx    # Authentication state management
│   ├── api.js          # API client functions
│   ├── App.jsx         # Main application component
│   └── main.jsx        # Application entry point
├── package.json        # Dependencies and scripts
└── vite.config.js      # Vite configuration
```

## 🚀 Getting Started

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Supabase Account** for database and storage
- **OpenRouter API Key** for AI services (optional: OpenAI API key)
- **AWS S3 Compatible Storage** for past papers

### 🔧 Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/UQ-Basement.git
cd UQ-Basement
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
```

#### 4. Environment Configuration

Create a `.env` file in the `backend` directory:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# AI Service Configuration
OPENROUTER_KEY=your_openrouter_api_key
OPENAI_API_KEY=your_openai_api_key  # Optional

# S3 Storage Configuration
S3_ENDPOINT_URL=your_s3_endpoint
S3_ACCESS_KEY_ID=your_s3_access_key
S3_SECRET_ACCESS_KEY=your_s3_secret_key
```

#### 5. Database Setup

Set up your Supabase database with the following tables:
- `users` - User authentication and profiles
- `courses` - Course information
- `enrollments` - User course enrollments
- `quiz` - Mock exam metadata
- `questions` - Exam questions
- `answers` - User responses
- `checked_answers` - AI-validated answers

### 🏃‍♂️ Running the Application

#### Start Backend Server
```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

#### Start Frontend Development Server
```bash
cd frontend
npm run dev
# Application runs on http://localhost:5173
```

## 📖 Usage Guide

### For Students

1. **Account Setup**
   - Register with your UQ email
   - Enroll in your courses
   - Set exam dates and times

2. **Accessing Past Papers**
   - Navigate to your course page
   - Click "Get Past Papers" to download available papers
   - Browse papers organized by year and semester
   - View PDFs with built-in AI assistance

3. **Taking Mock Exams**
   - Generate AI-powered mock exams from past papers
   - Complete timed practice exams
   - Receive detailed feedback and explanations
   - Track your progress over time

4. **AI Study Assistant**
   - Ask questions about specific exam problems
   - Get step-by-step solutions and explanations
   - Understand key concepts and methodologies

### For Administrators

- **Course Management**: Add and manage course information
- **User Analytics**: Track usage and performance metrics
- **Content Moderation**: Review AI-generated content quality

## 🛠️ Technology Stack

### Backend Technologies
- **FastAPI**: High-performance Python web framework
- **Pydantic**: Data validation and settings management
- **httpx**: Async HTTP client for external API calls
- **boto3**: AWS SDK for S3 storage operations
- **PyPDF2**: PDF text extraction and processing
- **Selenium**: Web automation for paper downloads
- **JWT**: JSON Web Tokens for authentication

### Frontend Technologies
- **React 19**: Modern JavaScript UI library
- **Vite**: Fast build tool and development server
- **React Router**: Client-side routing
- **Axios**: HTTP client for API requests
- **Tailwind CSS**: Utility-first CSS framework
- **DaisyUI**: Component library for Tailwind
- **PDF.js**: PDF rendering in the browser

### AI & ML Services
- **OpenRouter**: Access to various LLM models
- **OpenAI GPT**: Alternative AI service
- **Local LLM Support**: Fallback for offline operation

### Infrastructure
- **Supabase**: Backend-as-a-Service (database, auth, storage)
- **AWS S3**: Cloud storage for past papers
- **Vercel/Netlify**: Frontend deployment (recommended)
- **Railway/Heroku**: Backend deployment options

## 🔌 API Endpoints

### Authentication
- `POST /api/v1/users` - User registration
- `POST /api/v1/users/login` - User login
- `GET /api/v1/users/{user_id}` - Get user profile

### Courses & Enrollment
- `GET /api/v1/courses` - List available courses
- `POST /api/v1/enrollments` - Enroll in courses
- `GET /api/v1/enrollment-details` - Get enrollment info

### AI Features
- `POST /ai/get-papers/{course_code}` - Download past papers
- `GET /ai/past-papers/{course_code}` - List available papers
- `POST /ai/generate-questions-json/{course_code}` - Generate questions
- `POST /ai/solve-paper` - Get AI assistance for problems
- `POST /ai/create-quiz-and-upload-questions/{course_code}` - Create mock exam

### Quiz System
- `POST /api/v1/quiz` - Create new quiz
- `GET /api/v1/quiz/by-user/{user_id}` - Get user's quizzes
- `POST /api/v1/add-answers` - Submit quiz answers
- `GET /api/v1/checks/{user_id}/{quiz_id}` - Get answer validation

## 🤝 Contributing

We welcome contributions to improve UQ-Basement! Here's how you can help:

### Development Setup
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m 'Add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style
- **Python**: Follow PEP 8 guidelines
- **JavaScript/React**: Use ESLint configuration provided
- **Documentation**: Update README for significant changes
- **Testing**: Add tests for new features

### Areas for Contribution
- 🎨 UI/UX improvements
- 🤖 AI model fine-tuning
- 📊 Analytics and reporting features
- 🔒 Security enhancements
- 📱 Mobile responsiveness
- 🌐 Internationalization

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **University of Queensland** for providing access to past papers
- **UQCS Hackathon 2025** for the inspiration and platform
- **OpenRouter & OpenAI** for AI capabilities
- **Supabase** for the excellent backend infrastructure
- **React & FastAPI Communities** for amazing documentation

## 📞 Support

- **Issues**: Report bugs via [GitHub Issues](https://github.com/yourusername/UQ-Basement/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/yourusername/UQ-Basement/discussions)
- **Email**: Contact us at support@uq-basement.com

---

**Made with ❤️ for UQ students by UQ students**

*UQ-Basement - Transform your exam preparation with AI-powered mock exams!*