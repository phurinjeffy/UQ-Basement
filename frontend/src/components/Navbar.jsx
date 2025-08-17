import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";

function Navbar() {
  const { logout, user } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  // Load Google Fonts
  useEffect(() => {
    const link = document.createElement("link");
    link.href =
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap";
    link.rel = "stylesheet";
    document.head.appendChild(link);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  // Use email prefix as username, fallback to 'U'
  let username = "U";
  try {
    if (user && user.email) {
      username = user.email.split("@")[0];
    }
  } catch {}

  return (
    <nav className="sticky top-0 z-50 backdrop-blur-lg bg-white/80 dark:bg-slate-900/80 border-b border-slate-200/50 dark:border-slate-700/50 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex-shrink-0">
            <Link
              to="/dashboard"
              className="flex items-center space-x-3 group"
            >
              <div className="relative">
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white dark:border-slate-900"></div>
              </div>
              <div className="hidden sm:block">
                <h1 
                  className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent group-hover:from-purple-600 group-hover:to-pink-600 transition-all duration-300"
                  style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
                >
                  UQ-Basement
                </h1>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">Academic Helper</p>
              </div>
            </Link>
          </div>

          {/* Dark Mode Toggle */}
          <div className="hidden md:block">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-all duration-200 group"
              aria-label="Toggle dark mode"
            >
              {isDark ? (
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-3">
            {/* Mobile Dark Mode Toggle */}
            <button
              onClick={toggleTheme}
              className="md:hidden p-2 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 transition-all duration-200 group"
              aria-label="Toggle dark mode"
            >
              {isDark ? (
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5 group-hover:rotate-12 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>

            <div className="dropdown dropdown-end">
              <div
                tabIndex={0}
                role="button"
                className="flex items-center space-x-3 p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200 cursor-pointer group"
              >
                <div className="text-right hidden sm:block">
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    {username}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Student</p>
                </div>
                <div className="relative">
                  <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold shadow-lg group-hover:shadow-xl transition-shadow duration-300">
                    {username[0].toUpperCase()}
                  </div>
                  <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-400 rounded-full border-2 border-white dark:border-slate-900"></div>
                </div>
              </div>

              <ul
                tabIndex={0}
                className="menu menu-sm dropdown-content bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-xl mt-3 w-52 p-2 z-50"
              >
                <li className="mb-1">
                  <Link 
                    to="/profile" 
                    className="flex items-center space-x-3 p-3 rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors duration-200"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span className="font-medium">View Profile</span>
                  </Link>
                </li>
                <li>
                  <button
                    className="flex items-center space-x-3 p-3 w-full text-left rounded-lg text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors duration-200"
                    onClick={handleLogout}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span className="font-medium">Logout</span>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
