import React from "react";

function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-base-200">
      <h1 className="text-6xl font-bold text-red-600 mb-4">404</h1>
      <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">Page Not Found</h2>
      <p className="text-gray-700 dark:text-gray-300 mb-6">Sorry, the page you are looking for does not exist.</p>
      <a href="/" className="btn btn-primary">Go Home</a>
    </div>
  );
}

export default NotFound;
