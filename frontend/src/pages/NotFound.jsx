import React from "react";
import { Link } from "react-router-dom";

function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex flex-col items-center justify-center px-4">
      <div className="text-center animate-fadeInUp">
        {/* 404 Number with gradient */}
        <div className="relative mb-8">
          <h1 className="text-8xl md:text-9xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            404
          </h1>
          <div className="absolute inset-0 text-8xl md:text-9xl font-bold text-gray-200 -z-10 transform translate-x-2 translate-y-2">
            404
          </div>
        </div>

        {/* Error Message */}
        <div className="mb-8">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-4">
            Oops! Page Not Found
          </h2>
          <p className="text-gray-600 text-lg max-w-md mx-auto">
            The page you're looking for seems to have vanished into thin air. 
            Let's get you back on track!
          </p>
        </div>

        {/* Illustration */}
        <div className="mb-8">
          <svg className="w-32 h-32 mx-auto text-indigo-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.464-.881-6.08-2.33C5.92 15.3 6 18.6 6 21h12c0-2.4.08-5.7.08-8.33A7.963 7.963 0 0112 15z" />
          </svg>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="px-8 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transform hover:scale-[1.05] transition-all duration-200 shadow-lg"
          >
            Go Home
          </Link>
          <Link
            to="/dashboard"
            className="px-8 py-3 bg-white text-gray-700 rounded-xl font-semibold hover:bg-gray-50 transform hover:scale-[1.05] transition-all duration-200 shadow-lg border border-gray-200"
          >
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
