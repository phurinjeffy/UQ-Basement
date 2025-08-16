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