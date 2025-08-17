import { useNavigate } from "react-router-dom";
import React, { useState, useEffect } from "react";
import AddCourses from "../components/AddCourses.jsx";
import { updateEnrollments, getEnrollments, fetchCourseById, getUserQuizzes, getUserExamStats, getAvailableQuizzes, fetchResults } from "../api.js";
import Breadcrumbs from "../components/Breadcrumbs";

const Dashboard = () => {
  const [showAddCourses, setShowAddCourses] = useState(false);
  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [recentActivity, setRecentActivity] = useState([]);
  const [examStats, setExamStats] = useState({ exams_taken: 0, avg_score: 0 });
  const [userCreatedQuizzes, setUserCreatedQuizzes] = useState(0);
  const [showResultsModal, setShowResultsModal] = useState(false);
  const [selectedResultsExam, setSelectedResultsExam] = useState(null);
  const [currentResultsQuestionIndex, setCurrentResultsQuestionIndex] = useState(0);

  // Fetch enrollments on mount
  useEffect(() => {
    async function fetchEnrollmentsAndDetails() {
      let userId = "";
      try {
        const token = localStorage.getItem("token");
        if (token) {
          const payload = JSON.parse(atob(token.split('.')[1]));
          userId = payload.user_id;
        }
        if (!userId) return;

        // Fetch enrollments
        const enrollments = await getEnrollments(userId);
        const merged = await Promise.all(
          enrollments.map(async (e) => {
            let courseDetail = null;
            try {
              courseDetail = await fetchCourseById(e.course_id);
            } catch {}
            return {
              id: e.course_id,
              name: courseDetail?.course?.name,
              title: courseDetail?.course?.course_title,
              examDate: e.exam_date || "",
              examTime: e.exam_time || "",
            };
          })
        );
        setCourses(merged);

        // Fetch user quizzes for recent activity and stats
        try {
          // Get exam statistics based on submitted answers
          const examStatsRes = await getUserExamStats(userId);
          setExamStats({
            exams_taken: examStatsRes.exams_taken || 0,
            avg_score: examStatsRes.avg_score || 0
          });

          // Get user's created quizzes for progress calculation
          const quizzesRes = await getUserQuizzes(userId);
          const quizzes = quizzesRes.data?.quizzes || [];
          setUserCreatedQuizzes(quizzes.length);

          // Build recent activity from quizzes
          const activity = quizzes
            .slice(0, 5) // Get latest 5 quizzes
            .map(quiz => ({
              type: "Mock Exam",
              course: quiz.course_id || "Unknown Course",
              title: quiz.title,
              date: new Date(quiz.created_at || Date.now()).toISOString().split('T')[0],
              topic: quiz.topic,
              questions: quiz.questions?.length || 0,
              quiz: quiz // Include the full quiz object for results
            }));
          
          setRecentActivity(activity);
        } catch (err) {
          console.error("Error fetching quizzes:", err);
        }

      } catch (err) {
        console.error("Error fetching dashboard data:", err);
      } finally {
        setLoadingCourses(false);
      }
    }
    fetchEnrollmentsAndDetails();
  }, []);

  const handleConfirmCourses = async (newCourses) => {
    setCourses(
      newCourses.map((c, idx) => ({
        id: c.id || idx + 1,
        name: c.name,
        title: c.course_title || c.title || "",
        examDate: c.examDate || "",
        examTime: c.examTime || "",
      }))
    );
    setShowAddCourses(false);
    let userId = "";
    try {
      const token = localStorage.getItem("token");
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        userId = payload.user_id;
      }
    } catch {}
    if (userId) {
      await updateEnrollments(userId, newCourses);
    }
  };

  let username = "Student";
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (user && user.email) {
      username = user.email.split("@")[0];
    }
  } catch {}

  const navigate = useNavigate();
  
  // Calculate progress based on exams taken vs user's own created exams
  const calculateProgress = () => {
    if (userCreatedQuizzes === 0) return 0;
    return Math.round((examStats.exams_taken / userCreatedQuizzes) * 100);
  };
  
  const progressValue = calculateProgress();

  // Function to handle viewing exam results
  const handleViewResults = async (quiz) => {
    try {
      const token = localStorage.getItem("token");
      let userId = "";
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        userId = payload.user_id;
      }
      
      const results = await fetchResults(userId, quiz.id);
      setSelectedResultsExam({
        exam: quiz,
        results: results
      });
      setCurrentResultsQuestionIndex(0);
      setShowResultsModal(true);
    } catch (err) {
      console.error("Error fetching results:", err);
    }
  };

  // Function to check if quiz has results
  const checkQuizResults = async (quiz) => {
    try {
      const token = localStorage.getItem("token");
      let userId = "";
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        userId = payload.user_id;
      }
      
      const results = await fetchResults(userId, quiz.id);
      return results.checks && results.checks.length > 0;
    } catch (err) {
      return false;
    }
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case "Mock Exam":
        return (
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        );
      case "Study Session":
        return (
          <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
          </div>
        );
      default:
        return (
          <div className="w-10 h-10 bg-gradient-to-br from-gray-500 to-slate-500 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        );
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 dark:from-slate-900 dark:via-slate-800 dark:to-indigo-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <Breadcrumbs
            routes={[
              {
                label: "Dashboard",
                icon: (
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="h-4 w-4 stroke-current">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z" />
                  </svg>
                ),
              },
            ]}
          />
          
          <div className="mt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                Welcome back, {username}! 👋
              </h1>
              <p className="mt-2 text-slate-600 dark:text-slate-300">
                Ready to ace your exams? Let's continue your learning journey.
              </p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Exams Taken</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{examStats.exams_taken}</p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Mock Exams</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{userCreatedQuizzes}</p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </div>
                </div>
              </div>

              <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-600 dark:text-slate-400">Courses Enrolled</p>
                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{courses.length}</p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Courses Section */}
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Your Courses</h2>

                </div>
                <button
                  onClick={() => setShowAddCourses(true)}
                  className="inline-flex items-center px-3 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg transform hover:-translate-y-0.5 transition-all duration-200 text-sm"
                >
                  <svg className="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21.71 8.71c1.25-1.25.68-2.816 0-3.43-0.68-0.614-2.18-1.25-3.43 0l-1.34 1.34c-0.92-0.12-2.07 0.21-2.91 1.05-0.84 0.84-1.17 1.99-1.05 2.91l-8.34 8.34c-0.78 0.78-0.78 2.05 0 2.83 0.78 0.78 2.05 0.78 2.83 0l8.34-8.34c0.92 0.12 2.07-0.21 2.91-1.05 0.84-0.84 1.17-1.99 1.05-2.91l1.34-1.34z" />
                  </svg>
                  Manage
                </button>
              </div>

              {loadingCourses ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Array.from({ length: 4 }).map((_, idx) => (
                    <div key={idx} className="animate-pulse">
                      <div className="bg-slate-200 dark:bg-slate-700 rounded-xl h-24"></div>
                    </div>
                  ))}
                </div>
              ) : courses.length === 0 ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">No courses yet</h3>
                  <p className="text-slate-500 dark:text-slate-400 mb-4">Get started by adding your first course</p>
                  <button
                    onClick={() => setShowAddCourses(true)}
                    className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-xl hover:shadow-lg transition-shadow duration-200"
                  >
                    Add Course
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {courses.map((course) => {
                    let countdown = "";
                    let badgeColor = "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400";
                    
                    if (course.examDate) {
                      const now = new Date();
                      const exam = new Date(course.examDate);
                      now.setHours(0, 0, 0, 0);
                      exam.setHours(0, 0, 0, 0);
                      const diff = Math.floor((exam - now) / (1000 * 60 * 60 * 24));
                      
                      if (diff < 0) {
                        countdown = "Exam passed";
                        badgeColor = "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400";
                      } else if (diff === 0) {
                        countdown = "Exam today!";
                        badgeColor = "bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400";
                      } else if (diff === 1) {
                        countdown = "Tomorrow";
                        badgeColor = "bg-orange-100 text-orange-800 dark:bg-orange-900/20 dark:text-orange-400";
                      } else if (diff <= 7) {
                        countdown = `${diff} days`;
                        badgeColor = "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400";
                      } else {
                        countdown = `${diff} days`;
                        badgeColor = "bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400";
                      }
                    }

                    return (
                      <button
                        key={course.id}
                        onClick={() => navigate(`/courses/${course.name}`)}
                        className="group p-4 bg-white/50 dark:bg-slate-700/50 rounded-xl border border-slate-200/50 dark:border-slate-600/50 hover:bg-white dark:hover:bg-slate-700 hover:shadow-lg transform hover:-translate-y-1 transition-all duration-200"
                      >
                        <div className="flex flex-col h-full">
                          <div className="flex items-start justify-between mb-3">
                            <div className="text-left flex-1">
                              <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                                {course.name}
                              </h3>
                              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 line-clamp-2">
                                {course.title}
                              </p>
                            </div>
                            {countdown && (
                              <span className={`ml-2 px-2 py-1 text-xs font-medium rounded-full whitespace-nowrap ${badgeColor}`}>
                                {countdown}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center justify-between mt-auto">
                            <span className="text-xs text-slate-400 dark:text-slate-500">Click to explore</span>
                            <svg className="w-4 h-4 text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Recent Activity */}
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">Recent Activity</h2>
              {recentActivity.length > 0 ? (
                <div className="space-y-4">
                  {recentActivity.map((activity, idx) => (
                    <div key={idx} className="flex items-center space-x-4 p-3 bg-white/50 dark:bg-slate-700/50 rounded-xl">
                      {getActivityIcon(activity.type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 dark:text-white truncate">
                          {activity.title || activity.type}
                        </p>
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                          {activity.topic && `${activity.topic} • `}{activity.date}
                        </p>
                      </div>
                      <div className="flex items-center space-x-2">
                        {activity.quiz && (
                          <button
                            onClick={() => handleViewResults(activity.quiz)}
                            className="px-3 py-1 text-xs bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg hover:bg-indigo-200 dark:hover:bg-indigo-900/50 transition-colors duration-200"
                          >
                            View Results
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="w-12 h-12 bg-slate-100 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <p className="text-slate-500 dark:text-slate-400">No recent activity</p>
                  <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">Start a mock exam to see your activity here</p>
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Profile Card */}
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl text-center">
              <div className="relative inline-block mb-4">
                <div className="w-20 h-20 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-2xl font-bold text-white shadow-lg">
                  {username[0].toUpperCase()}
                </div>
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-400 rounded-full border-4 border-white dark:border-slate-800"></div>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{username}</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm">UQ Student</p>
            </div>

            {/* Progress Card */}
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Progress</h3>
                <span className="text-2xl">📈</span>
              </div>
              <div className="text-center mb-6">
                <div className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  {progressValue}%
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400">Overall Progress</p>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 h-3 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out"
                  style={{ width: `${progressValue}%` }}
                />
              </div>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Exams Taken:</span>
                  <span className="font-medium text-slate-900 dark:text-white">{examStats.exams_taken}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Mock Exams Created:</span>
                  <span className="font-medium text-slate-900 dark:text-white">{userCreatedQuizzes}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Courses Enrolled:</span>
                  <span className="font-medium text-slate-900 dark:text-white">{courses.length}</span>
                </div>
                {examStats.avg_score > 0 && (
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600 dark:text-slate-400">Avg Score:</span>
                    <span className="font-medium text-slate-900 dark:text-white">{examStats.avg_score}%</span>
                  </div>
                )}
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 text-center mt-4">
                {userCreatedQuizzes === 0 
                  ? "Create your first mock exam! �"
                  : progressValue === 0 
                  ? "Ready to take your created exams! 🚀" 
                  : progressValue < 25 
                  ? "Just getting started! 🌱" 
                  : progressValue < 50 
                  ? "Making good progress! 💪" 
                  : progressValue < 75 
                  ? "You're doing great! 🎉" 
                  : progressValue < 100
                  ? "Almost finished all your exams! 🔥"
                  : "All your exams completed! 🏆"}
              </p>
            </div>

            {/* Quick Actions */}
            <div className="bg-white/70 dark:bg-slate-800/70 backdrop-blur-lg rounded-2xl p-6 border border-white/20 dark:border-slate-700/20 shadow-xl">
              <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full flex items-center justify-center px-4 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl hover:shadow-lg transition-shadow duration-200">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Start Mock Exam
                </button>
                <button className="w-full flex items-center justify-center px-4 py-3 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-600 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors duration-200">
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Review Materials
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Add Courses Modal */}
        {showAddCourses && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={() => setShowAddCourses(false)} />
            <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden border border-white/20 dark:border-slate-700/20">
              <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Manage Courses</h2>
                <button
                  onClick={() => setShowAddCourses(false)}
                  className="w-10 h-10 flex items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors duration-200"
                >
                  <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-80px)]">
                <AddCourses
                  onConfirm={handleConfirmCourses}
                  initialCourses={courses.map(c => ({
                    id: c.id,
                    name: c.name,
                    course_title: c.title,
                    examDate: c.examDate,
                    examTime: c.examTime
                  }))}
                />
              </div>
            </div>
          </div>
        )}

        {/* Results Modal */}
        {showResultsModal && selectedResultsExam && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={() => setShowResultsModal(false)} />
            <div className="relative bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden border border-white/20 dark:border-slate-700/20">
              <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
                <div>
                  <div className="font-semibold text-slate-900 dark:text-slate-100 truncate">{selectedResultsExam.exam?.title} - Results</div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">
                    Score: {selectedResultsExam.results?.checks?.filter(check => check.result === 'correct').length || 0}/{selectedResultsExam.results?.checks?.length || 0}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    Question {Math.min(currentResultsQuestionIndex + 1, selectedResultsExam.results?.checks?.length || 0)} / {selectedResultsExam.results?.checks?.length || 0}
                  </span>
                  <button
                    onClick={() => {
                      setShowResultsModal(false);
                      setSelectedResultsExam(null);
                    }}
                    className="w-10 h-10 flex items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors duration-200"
                  >
                    <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
              
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-160px)]">
                {selectedResultsExam.results?.checks && selectedResultsExam.results.checks[currentResultsQuestionIndex] && (
                  <div className="space-y-6">
                    {/* Question */}
                    <div className="bg-slate-50 dark:bg-slate-700/50 rounded-xl p-4">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-2">Question:</h3>
                      <p className="text-slate-700 dark:text-slate-300">
                        {selectedResultsExam.results.checks[currentResultsQuestionIndex]?.question || 'Question not available.'}
                      </p>
                    </div>

                    {/* Result Badge */}
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      selectedResultsExam.results.checks[currentResultsQuestionIndex]?.result === 'correct' 
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' 
                        : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                    }`}>
                      {selectedResultsExam.results.checks[currentResultsQuestionIndex]?.result === 'correct' ? (
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                      )}
                      {selectedResultsExam.results.checks[currentResultsQuestionIndex]?.result === 'correct' ? 'Correct' : 'Incorrect'}
                    </div>

                    {/* Your Answer */}
                    <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4">
                      <h3 className="font-medium text-blue-900 dark:text-blue-300 mb-2">Your Answer:</h3>
                      <p className="text-blue-800 dark:text-blue-200">
                        {selectedResultsExam.results.checks[currentResultsQuestionIndex]?.userAnswer || 'No answer provided'}
                      </p>
                    </div>

                    {/* Correct Answer */}
                    <div className="bg-green-50 dark:bg-green-900/20 rounded-xl p-4">
                      <h3 className="font-medium text-green-900 dark:text-green-300 mb-2">Correct Answer:</h3>
                      <p className="text-green-800 dark:text-green-200">
                        {selectedResultsExam.results.checks[currentResultsQuestionIndex]?.realAnswer || 'No model answer available'}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Navigation */}
              <div className="flex items-center justify-between p-6 border-t border-slate-200 dark:border-slate-700">
                <button
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    currentResultsQuestionIndex === 0 
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed dark:bg-slate-700 dark:text-slate-500' 
                      : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-600 dark:text-slate-200 dark:hover:bg-slate-500'
                  }`}
                  onClick={() => setCurrentResultsQuestionIndex((i) => Math.max(0, i - 1))}
                  disabled={currentResultsQuestionIndex === 0}
                >
                  Previous
                </button>
                
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {Math.round(((selectedResultsExam.results?.checks?.filter(check => check.result === 'correct').length || 0) / (selectedResultsExam.results?.checks?.length || 1)) * 100)}% Score
                  </span>
                </div>

                <button
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    currentResultsQuestionIndex === (selectedResultsExam.results?.checks?.length || 1) - 1 
                      ? 'bg-slate-100 text-slate-400 cursor-not-allowed dark:bg-slate-700 dark:text-slate-500' 
                      : 'bg-slate-200 text-slate-700 hover:bg-slate-300 dark:bg-slate-600 dark:text-slate-200 dark:hover:bg-slate-500'
                  }`}
                  onClick={() => setCurrentResultsQuestionIndex((i) => Math.min((selectedResultsExam.results?.checks?.length || 1) - 1, i + 1))}
                  disabled={currentResultsQuestionIndex === (selectedResultsExam.results?.checks?.length || 1) - 1}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
