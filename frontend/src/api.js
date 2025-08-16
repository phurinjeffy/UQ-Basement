// frontend/src/api.js
import axios from "axios";


const API_BASE = "http://localhost:8000/api/v1"; // Match backend router prefix

export async function loginUser(email, password) {
    const res = await axios.post(`${API_BASE}/users/login`, { email, password });
    return res.data;
}

export async function signupUser({ email, password }) {
    const res = await axios.post(`${API_BASE}/users`, { email, password });
    return res.data;
}

export async function fetchUserProfile(userId) {
    const res = await axios.get(`${API_BASE}/users/${userId}`);
    return res.data;
}

export async function deleteUser(userId) {
    const res = await axios.delete(`${API_BASE}/users/${userId}`);
    return res.data;
}

// AI endpoints for past papers
export async function getPapers(courseCode) {
    // Triggers backend to download all PDFs for a course
    const res = await axios.post(`${API_BASE}/ai/get-papers/${courseCode}`);
    return res.data;
}

export async function listPastPapers(courseCode) {
    // Returns array of PDF filenames
    const res = await axios.get(`${API_BASE}/ai/past-papers/${courseCode}`);
    return res.data;
}

export function getPastPaperPdfUrl(courseCode, filename) {
    // Returns direct URL to download/view PDF
    return `${API_BASE}/ai/past-papers/${courseCode}/${filename}`;
}

export async function fetchCourses(hint = "") {
    const params = {
        limit: 6,
        offset: 0,
        include_enrollment_count: false,
    };

    if (hint) {
        params.name = hint;
    }

    const res = await axios.get(`${API_BASE}/courses`, { params });
    return res.data.courses || [];
}

// Fetch course details by course_id
export async function fetchCourseById(courseId) {
    const res = await axios.get(`${API_BASE}/courses/${courseId}`);
    return res.data;
}

export async function updateEnrollments(userId, courses) {
    console.log("here", courses);
    const payload = courses.map(course => ({
        user_id: userId,
        course_id: course.id,
        semester: "Semester 2",
        year: 2025,
        grade: "",
        exam_date: course.examDate || null,
        exam_time: course.examTime || null
    }));
    const res = await axios.put(`${API_BASE}/enrollments/update?user_id=${userId}`, payload);
    return res.data;
}

export async function getEnrollments(userId) {
    const res = await axios.get(`${API_BASE}/enrollments`, {
        params: { user_id: userId }
    });
    return res.data.enrollments || [];
}

export async function fetchEnrollmentDetails(userId, courseName) {
    const res = await axios.get(`${API_BASE}/enrollment-details`, {
        params: { user_id: userId, course_name: courseName }
    });
    console.log(res.data);
    return res.data;
}

// Create a quiz and upload questions in one step (Mock Exam automation)
export async function createQuizAndUploadQuestions({ course_code, title, course_id, topic, description, time_limit }) {
    try {
        const res = await axios.post(
            `${API_BASE}/ai/create-quiz-and-upload-questions/${course_code}`,
            {},
            {
                params: {
                    title,
                    course_id,
                    topic,
                    description,
                    time_limit,
                },
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${localStorage.getItem("token")}`,
                },
            }
        );
        return res.data;
    } catch (err) {
        console.error("Quiz+Questions creation error:", err.response?.data || err);
        throw err;
    }
}

// Generate questions JSON for a course
export async function generateQuestionsJson(course_code) {
    try {
        const res = await axios.post(`${API_BASE}/ai/generate-questions-json/${course_code}`);
        return res.data;
    } catch (err) {
        console.error("Generate questions JSON error:", err.response?.data || err);
        throw err;
    }
}

// Fetch course details by code (e.g., DECO2500)
export async function fetchCourseByCode(courseCode) {
    const res = await axios.get(`${API_BASE}/courses/search-by-code`, {
        params: { code: courseCode }
    });
    return res.data;
}

// Fetch quizzes (mock exams) for a course including questions
export async function fetchQuizzes(courseId, page = 1, size = 50) {
    const res = await axios.get(`${API_BASE}/quiz/`, {
        params: {
            page,
            size,
            include_questions: true,
            course_id: courseId,
        },
    });
    return res.data; // consumer should handle array or paged shape
}