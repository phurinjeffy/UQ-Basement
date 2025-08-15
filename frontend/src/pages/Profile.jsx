import React from "react";

// Dummy user data for now; replace with backend fetch later
const user = {
  name: "Student Name",
  studentId: "s4123456",
  year: "3rd Year",
  courses: [
    "COMP3506 - Algorithms & Data Structures",
    "COMP3702 - Artificial Intelligence",
    "COMP3710 - Pattern Recognition",
    "COMP4601 - Software Architecture",
  ],
  profilePic: null, // Replace with image URL if available
};

function Profile() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-base-200 px-4 py-10">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl p-10 max-w-lg w-full flex flex-col items-center">
        <div className="w-32 h-32 rounded-full bg-blue-600 dark:bg-blue-400 flex items-center justify-center text-5xl font-bold text-white mb-6">
          {user.profilePic ? (
            <img
              src={user.profilePic}
              alt="Profile"
              className="w-full h-full rounded-full object-cover"
            />
          ) : (
            user.name[0]
          )}
        </div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {user.name}
        </h2>
        <div className="text-gray-500 dark:text-gray-400 mb-1">
          Student ID: <span className="font-mono">{user.studentId}</span>
        </div>
        <div className="text-gray-500 dark:text-gray-400 mb-4">{user.year}</div>
        <div className="w-full">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Courses Taken
          </h3>
          <ul className="list-disc list-inside text-gray-700 dark:text-gray-300">
            {user.courses.map((course, idx) => (
              <li key={idx}>{course}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Profile;
