import React, { useEffect, useState } from "react";
import { fetchUserProfile, deleteUser, getUserEnrollments, getUserExamStats } from "../api";
import { useNavigate } from "react-router-dom";

function Profile() {
  const [user, setUser] = useState(null);
  const [enrollments, setEnrollments] = useState([]);
  const [examStats, setExamStats] = useState({ exams_taken: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    // Extract userId from JWT token
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/", { replace: true });
      return;
    }
    let userId = "";
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      userId = payload.user_id;
    } catch {}
    if (!userId) {
      navigate("/", { replace: true });
      return;
    }

    const fetchProfileData = async () => {
      try {
        // Fetch user profile
        const userRes = await fetchUserProfile(userId);
        setUser(userRes.user);

        // Fetch user enrollments
        const enrollmentsRes = await getUserEnrollments(userId);
        console.log("Enrollments response:", enrollmentsRes);
        setEnrollments(enrollmentsRes.enrollments || []);

        // Fetch user exam stats (actual exams taken)
        const examStatsRes = await getUserExamStats(userId);
        console.log("Exam stats response:", examStatsRes);
        setExamStats({
          exams_taken: examStatsRes.exams_taken || 0
        });

        setLoading(false);
      } catch (err) {
        console.error("Error fetching profile data:", err);
        setError("Failed to load profile data");
        setLoading(false);
      }
    };

    fetchProfileData();
  }, [navigate]);

  const handleDelete = async () => {
    if (
      !window.confirm(
        "Are you sure you want to delete your account? This cannot be undone."
      )
    )
      return;
    try {
      await deleteUser(user.id);
  localStorage.removeItem("token");
      navigate("/", { replace: true });
    } catch (err) {
      setError("Failed to delete account");
    }
  };

  if (loading)
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          <p className="text-gray-600">Loading your profile...</p>
        </div>
      </div>
    );
  if (error)
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">⚠️</div>
          <p className="text-red-600 font-medium">{error}</p>
        </div>
      </div>
    );
  if (!user) return null;

  // Use email prefix as display name
  const displayName = user && user.email ? user.email.split("@")[0] : "User";
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50 flex flex-col items-center justify-center px-4 py-10">
      <div className="bg-white/90 backdrop-blur-lg rounded-3xl shadow-xl border border-white/20 p-10 max-w-lg w-full flex flex-col items-center animate-fadeInUp">
        {/* Profile Avatar */}
        <div className="relative mb-8">
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-5xl font-bold text-white shadow-lg">
            {displayName[0].toUpperCase()}
          </div>
          <div className="absolute -bottom-2 -right-2 w-8 h-8 bg-green-500 rounded-full border-4 border-white flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        </div>

        {/* Profile Info */}
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-3">
            {displayName}
          </h2>
          <div className="bg-gray-50 rounded-lg p-3 inline-block">
            <div className="text-sm text-gray-500 mb-1">Email Address</div>
            <div className="font-mono text-gray-800">{user.email}</div>
          </div>
        </div>

        {/* Profile Stats */}
        <div className="grid grid-cols-2 gap-4 w-full mb-8">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-indigo-600">{enrollments.length}</div>
            <div className="text-sm text-gray-600">Courses</div>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-purple-600">{examStats.exams_taken}</div>
            <div className="text-sm text-gray-600">Exams Taken</div>
          </div>
        </div>

        {/* Courses List */}
        <div className="w-full mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Enrolled Courses</h3>
          {enrollments.length > 0 ? (
            <div className="space-y-2">
              {enrollments.map((enrollment, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-3 text-sm">
                  <div className="font-medium text-gray-800">
                    {enrollment.course?.name || 'Unknown Course'}
                  </div>
                  <div className="text-gray-600">
                    {enrollment.course?.course_title || 'No title available'}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {enrollment.semester} {enrollment.year}
                    {enrollment.exam_date && (
                      <span className="ml-2">• Exam: {enrollment.exam_date}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
              No courses enrolled yet
            </div>
          )}
        </div>

        {/* Recent Exams */}
        <div className="w-full mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3">Exam Performance</h3>
          {examStats.exams_taken > 0 ? (
            <div className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-2xl font-bold text-green-600 mb-1">
                {examStats.exams_taken}
              </div>
              <div className="text-sm text-gray-600">
                {examStats.exams_taken === 1 ? 'Exam Completed' : 'Exams Completed'}
              </div>
              <div className="text-xs text-gray-500 mt-2">
                Keep taking more exams to improve your skills!
              </div>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-lg p-4 text-center text-gray-500">
              No exams taken yet
              <div className="text-xs text-gray-400 mt-1">
                Start your first mock exam to track your progress
              </div>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="w-full space-y-3">
          <button
            className="w-full py-3 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transform hover:scale-[1.02] transition-all duration-200 shadow-lg"
            onClick={() => navigate('/dashboard')}
          >
            Go to Dashboard
          </button>
          <button
            className="w-full py-3 px-6 bg-red-500 text-white rounded-xl font-semibold hover:bg-red-600 transform hover:scale-[1.02] transition-all duration-200 shadow-lg"
            onClick={handleDelete}
          >
            Delete Account
          </button>
        </div>
      </div>
    </div>
  );
}

export default Profile;
