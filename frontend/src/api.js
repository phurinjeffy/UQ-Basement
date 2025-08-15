// frontend/src/api.js
import axios from "axios";

const API_BASE = "http://localhost:8000"; // Change if backend runs elsewhere

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
