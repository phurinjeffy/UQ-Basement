import { useState, useEffect } from "react";
import AddCourses from "../components/AddCourses";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

function Home() {
  const [isSignup, setIsSignup] = useState(false);
  const [form, setForm] = useState({
    email: "",
    password: "",
    confirmPassword: "",
  });
  const { login, signup, loading, error } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const link = document.createElement("link");
    link.href =
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap";
    link.rel = "stylesheet";
    document.head.appendChild(link);
  }, []);

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (isSignup && form.password !== form.confirmPassword) {
      alert("Passwords do not match");
      return;
    }
    let success = false;
    if (isSignup) {
      success = await signup(form.email, form.password);
    } else {
      success = await login(form.email, form.password);
    }
    if (success) {
      navigate("/dashboard");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200 px-4">
      <div className="hero bg-base-100 dark:bg-gray-800 rounded-2xl shadow-2xl p-10 max-w-4xl w-full mx-auto flex flex-col lg:flex-row gap-10 transition-colors">
        {/* Always show login/signup, redirect handled by PrivateRoute */}
        {true ? (
          <>
            <div className="flex-1 text-center lg:text-left">
              <h1
                className="text-5xl lg:text-6xl font-bold text-gray-900 dark:text-gray-100 mb-6"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                Welcome to UQ Basement
              </h1>
              <p className="text-gray-700 dark:text-gray-300 text-lg">
                Access your courses, track progress, and prepare for exams
                efficiently. Log in or sign up below to continue.
              </p>
            </div>

            <div className="flex-1 flex justify-center">
              <div className="card bg-base-100 dark:bg-gray-900 w-full max-w-sm shadow-xl rounded-xl p-6 transition-colors">
                <div className="card-body">
                  <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
                    {/* No extra fields for signup, just email and password */}
                    <label className="label text-gray-800 dark:text-gray-200">
                      UQ Email
                    </label>
                    <input
                      type="email"
                      name="email"
                      className="input input-bordered w-full text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700"
                      placeholder="s4123456@uq.edu.au"
                      value={form.email}
                      onChange={handleChange}
                      required
                    />
                    <label className="label text-gray-800 dark:text-gray-200">
                      Password
                    </label>
                    <input
                      type="password"
                      name="password"
                      className="input input-bordered w-full text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700"
                      placeholder="Password"
                      value={form.password}
                      onChange={handleChange}
                      required
                    />
                    {isSignup && (
                      <>
                        <label className="label text-gray-800 dark:text-gray-200">
                          Confirm Password
                        </label>
                        <input
                          type="password"
                          name="confirmPassword"
                          className="input input-bordered w-full text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700"
                          placeholder="Confirm Password"
                          value={form.confirmPassword}
                          onChange={handleChange}
                          required
                        />
                      </>
                    )}
                    {error && (
                      <div className="text-red-500 text-sm">{error}</div>
                    )}
                    <button
                      className="btn btn-primary mt-4 w-full py-3 text-lg"
                      type="submit"
                      disabled={loading}
                    >
                      {loading
                        ? isSignup
                          ? "Signing up..."
                          : "Logging in..."
                        : isSignup
                        ? "Sign Up"
                        : "Log In"}
                    </button>
                  </form>
                  <div className="mt-4 text-center">
                    <button
                      className="link link-hover text-blue-600 dark:text-blue-400 text-sm"
                      onClick={() => setIsSignup((v) => !v)}
                    >
                      {isSignup
                        ? "Already have an account? Log in"
                        : "Don't have an account? Sign up"}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <AddCourses />
        )}
      </div>
    </div>
  );
}

export default Home;
