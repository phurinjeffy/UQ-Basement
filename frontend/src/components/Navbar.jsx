import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Navbar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  // Load Google Fonts
  useEffect(() => {
    const link = document.createElement("link");
    link.href =
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap";
    link.rel = "stylesheet";
    document.head.appendChild(link);
  }, []);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <div className="navbar bg-gray-100 dark:bg-gray-800 shadow-md h-20 px-6 z-50">
      <div className="navbar-start">
        {/* Hamburger toggle for drawer */}
        <label
          htmlFor="my-drawer"
          className="btn btn-ghost btn-circle drawer-button"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6 text-gray-900 dark:text-gray-100"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M4 6h16M4 12h16M4 18h7"
            />
          </svg>
        </label>
      </div>

      <div className="navbar-center">
        <Link
          to="/dashboard"
          className="text-3xl font-bold text-gray-900 dark:text-gray-100"
          style={{ fontFamily: "'Inter', sans-serif" }}
        >
          UQ-Basement
        </Link>
      </div>

      <div className="navbar-end">
        <div className="dropdown dropdown-end">
          <div
            tabIndex={0}
            role="button"
            className="btn btn-ghost btn-circle avatar"
          >
            <div className="w-10 h-10 rounded-full bg-neutral text-neutral-content flex items-center justify-center text-lg font-semibold">
              SY
            </div>
          </div>

          <ul
            tabIndex={0}
            className="menu menu-sm dropdown-content bg-gray-100 dark:bg-gray-800 rounded-box mt-3 w-40 p-2 shadow"
          >
            <li>
              <Link to="/profile" className="text-gray-900 dark:text-gray-100">
                View Profile
              </Link>
            </li>
            <li>
              <button
                className="text-gray-900 dark:text-gray-100"
                onClick={handleLogout}
              >
                Logout
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Navbar;
