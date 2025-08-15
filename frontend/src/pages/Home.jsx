import { useState, useEffect } from "react";
import AddCourses from "../components/AddCourses";

function Home() {
  const [showAddCourses, setShowAddCourses] = useState(false);

  // Load Google Fonts
  useEffect(() => {
    const link = document.createElement("link");
    link.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap";
    link.rel = "stylesheet";
    document.head.appendChild(link);
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-base-200 px-4">
      <div className="hero bg-base-100 dark:bg-gray-800 rounded-2xl shadow-2xl p-10 max-w-4xl w-full mx-auto flex flex-col lg:flex-row gap-10 transition-colors">
        {!showAddCourses ? (
          <>
            <div className="flex-1 text-center lg:text-left">
              <h1
                className="text-5xl lg:text-6xl font-bold text-gray-900 dark:text-gray-100 mb-6"
                style={{ fontFamily: "'Inter', sans-serif" }}
              >
                Welcome to UQ Basement
              </h1>
              <p className="text-gray-700 dark:text-gray-300 text-lg">
                Access your courses, track progress, and prepare for exams efficiently. Log in below to continue.
              </p>
            </div>

            <div className="flex-1 flex justify-center">
              <div className="card bg-base-100 dark:bg-gray-900 w-full max-w-sm shadow-xl rounded-xl p-6 transition-colors">
                <div className="card-body">
                  <fieldset className="flex flex-col gap-4">
                    <label className="label text-gray-800 dark:text-gray-200">UQ Student ID</label>
                    <input
                      type="text"
                      className="input input-bordered w-full text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700"
                      placeholder="s4123456"
                    />
                    <label className="label text-gray-800 dark:text-gray-200">Password</label>
                    <input
                      type="password"
                      className="input input-bordered w-full text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-700"
                      placeholder="Password"
                    />
                    <div className="text-right">
                      <a className="link link-hover text-sm text-blue-600 dark:text-blue-400">
                        Forgot password?
                      </a>
                    </div>
                    <button
                      className="btn btn-primary mt-4 w-full py-3 text-lg"
                      onClick={() => setShowAddCourses(true)}
                    >
                      Continue
                    </button>
                  </fieldset>
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
