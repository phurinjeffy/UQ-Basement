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
- **AI-Powered Autograder**: Automatic and intelligent scoring of responses
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
- **AWS S3 Compatible Storage** for past papers (e.g. Supabase Storage)

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
uvicorn main:app --reload
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
   - Receive detailed feedback and explanations
   - Track your progress over time

4. **AI Study Assistant**
   - Ask questions about specific exam problems
   - Get step-by-step solutions and explanations
   - Understand key concepts and methodologies


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
- **AWS S3**: (via Supabase Storage) Cloud storage for past papers

## 🔌 API Endpoints

### 👤 Authentication & Users
- `GET /api/v1/users` - List all users (admin)
- `POST /api/v1/users` - User registration
- `POST /api/v1/users/login` - User login
- `GET /api/v1/users/{user_id}` - Get user profile
- `PUT /api/v1/users/{user_id}` - Update user profile
- `PUT /api/v1/users/{user_id}/password` - Change user password
- `DELETE /api/v1/users/{user_id}` - Delete user account
- `POST /api/v1/users/{user_id}/courses` - Add courses to user
- `GET /api/v1/users/{user_id}/courses` - Get user's courses
- `DELETE /api/v1/users/{user_id}/courses/{course_code}` - Remove course from user

### 📚 Courses Management
- `GET /api/v1/courses` - List courses with pagination and filters
- `GET /api/v1/courses/search-by-code` - Search course by code
- `GET /api/v1/courses/{course_id}` - Get specific course details
- `POST /api/v1/courses` - Create new course
- `PUT /api/v1/courses/{course_id}` - Update course information
- `DELETE /api/v1/courses/{course_id}` - Delete course
- `POST /api/v1/sync-uq-courses` - Sync courses from UQ API
- `POST /api/v1/batch-create-courses` - Bulk create courses

### 📝 Enrollments
- `POST /api/v1/enrollments` - Create new enrollment
- `GET /api/v1/enrollments` - Get enrollments (filtered by user)
- `DELETE /api/v1/enrollments/{enrollment_id}` - Delete enrollment
- `PUT /api/v1/enrollments/update` - Bulk update enrollments
- `GET /api/v1/enrollment-details` - Get detailed enrollment info

### 🧠 Quiz System
- `POST /api/v1/quiz/` - Create new quiz
- `GET /api/v1/quiz/` - List all quizzes
- `GET /api/v1/quiz/{quiz_id}` - Get specific quiz with questions
- `PUT /api/v1/quiz/{quiz_id}` - Update quiz details
- `DELETE /api/v1/quiz/{quiz_id}` - Delete quiz
- `GET /api/v1/quiz/by-user/{user_id}` - Get quizzes by user
- `GET /api/v1/quiz/by-user-course/{user_id}/{course_id}` - Get quizzes by user and course
- `GET /api/v1/quiz/course/{course_id}` - Get quizzes for a course
- `GET /api/v1/quiz/{quiz_id}/questions` - Get questions for a quiz
- `POST /api/v1/quiz/{quiz_id}/questions/{question_id}` - Add question to quiz
- `DELETE /api/v1/quiz/{quiz_id}/questions/{question_id}` - Remove question from quiz

### ❓ Questions Management
- `POST /api/v1/question/` - Create new question
- `POST /api/v1/question/bulk-import` - Bulk import questions
- `GET /api/v1/question/` - List questions with filters
- `GET /api/v1/question/{question_id}` - Get specific question
- `PUT /api/v1/question/{question_id}` - Update question
- `DELETE /api/v1/question/{question_id}` - Delete question
- `GET /api/v1/question/stats` - Get question statistics
- `GET /api/v1/question/topics` - Get all available topics
- `POST /api/v1/question/{question_id}/choices` - Add choices to question
- `DELETE /api/v1/question/{question_id}/choices/{choice_id}` - Delete choice

### 📋 Answers & Results
- `POST /api/v1/add-answers` - Submit quiz answers
- `GET /api/v1/all/answers` - Get all answers (filtered by user/quiz)
- `GET /api/v1/checks/{user_id}/{quiz_id}` - Get answer validation results

### 🤖 AI-Powered Features

#### Past Papers Management
- `POST /api/v1/ai/get-papers/{course_code}` - Download past papers for course
- `GET /api/v1/ai/past-papers/{course_code}` - List available past papers
- `GET /api/v1/ai/past-papers/{course_code}/{filename}` - Download/view specific paper

#### Question Generation & AI Processing
- `POST /api/v1/ai/generate-questions-json/{course_code}` - Generate questions from past papers
- `POST /api/v1/ai/create-quiz-and-upload-questions/{course_code}` - Create complete quiz with AI-generated questions
- `POST /api/v1/ai/solve-paper` - Get AI assistance for exam problems

#### Answer Checking & Validation
- `POST /api/v1/ai/complete-answer-check-flow` - Complete answer validation workflow
- `POST /api/v1/ai/fetch-answers` - Fetch answers for AI processing
- `POST /api/v1/ai/check-answers-from-file` - AI-powered answer checking
- `POST /api/v1/ai/upload-checked-answers-from-file` - Upload validated answers

### 📊 Additional Features
- **Pagination**: Most list endpoints support `limit`, `offset`, and `page` parameters
- **Search**: Full-text search available for courses and questions
- **Real-time Processing**: Background tasks for AI processing
- **Bulk Operations**: Batch creation and updates for efficiency

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **UQ Library** for providing access to past papers (via Student Login)
- **UQCS Hackathon 2025** for the inspiration and platform
- **OpenRouter & OpenAI** for AI capabilities
- **Supabase** for the excellent backend infrastructure
- **React & FastAPI Communities** for amazing documentation


---

**Made with ❤️ for UQ students by UQ students**

*UQ-Basement - Transform your exam preparation with AI-powered mock exams!*
