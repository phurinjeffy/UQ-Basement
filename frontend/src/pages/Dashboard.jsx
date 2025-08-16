import { useNavigate } from "react-router-dom";
import React, { useState, useEffect } from "react";
import AddCourses from "../components/AddCourses.jsx";
import { updateEnrollments, getEnrollments, fetchCourseById } from "../api.js";

const Dashboard = () => {
  const [showAddCourses, setShowAddCourses] = useState(false);
  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true); // New state for loading

  // Fetch enrollments on mount
  useEffect(() => {
    async function fetchEnrollmentsAndDetails() {
      const userId = "f8808c59-719c-4f7a-8ea5-ef372bdd700d";
      try {
        const enrollments = await getEnrollments(userId);
        // Fetch course details for each enrolled course
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
      } catch (err) {
        // Optionally handle error
      } finally {
        setLoadingCourses(false); // Set loading to false after fetch
      }
    }
    fetchEnrollmentsAndDetails();
  }, []);

  // Handler for confirming courses from AddCourses
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
    // Connect to backend
    let userId = "";
    try {
      const user = JSON.parse(localStorage.getItem("user"));
      if (user && user.id) {
        userId = user.id;
      }
    } catch {}
    if (userId) {
      await updateEnrollments(userId, newCourses);
    }
  };

  // Use email prefix as username
  let username = "Student";
  try {
    const user = JSON.parse(localStorage.getItem("user"));
    if (user && user.email) {
      username = user.email.split("@")[0];
    }
  } catch {}
  const navigate = useNavigate();
  const progressValue = 65;
  const recentActivity = [
    { type: "Mock Exam", course: "COMP3506", date: "2025-08-15", score: 82 },
    {
      type: "Study Session",
      course: "COMP3702",
      date: "2025-08-14",
      duration: "1h 30m",
    },
    { type: "Mock Exam", course: "COMP3710", date: "2025-08-13", score: 75 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-10 px-4 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar: Profile, Progress, Stats */}
          <aside className="lg:col-span-1 space-y-8">
            {/* Profile Card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-6 flex flex-col items-center">
              <div className="w-20 h-20 rounded-full bg-blue-600 dark:bg-blue-400 flex items-center justify-center text-3xl font-bold text-white mb-3">
                {username[0]}
              </div>
              <div className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-1">
                {username}
              </div>
              <div className="text-gray-500 dark:text-gray-400 text-sm">
                UQ Student
              </div>
            </div>

            {/* Progress Card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-gray-100 font-semibold">
                📈 <span>Progress</span>
              </div>
              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                  {progressValue}%
                </div>
                <div className="text-sm text-gray-900 dark:text-gray-100">
                  Overall Progress
                </div>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 h-4 rounded-full mb-2">
                <div
                  className="bg-blue-600 dark:bg-blue-400 h-4 rounded-full"
                  style={{ width: `${progressValue}%` }}
                />
              </div>
              <div className="text-sm text-gray-900 dark:text-gray-100 text-center">
                Keep going! You're making great progress.
              </div>
            </div>

            {/* Statistics Card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-xl p-6">
              <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-gray-100 font-semibold">
                📄 <span>Statistics</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Mock Exams Taken
                </span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  12
                </span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Topics Mastered
                </span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  8
                </span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Study Streak
                </span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  5 days
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  Avg. Score
                </span>
                <span className="font-semibold text-blue-600 dark:text-blue-400">
                  78%
                </span>
              </div>
            </div>
          </aside>

          {/* Main Content */}
          <main className="lg:col-span-3 space-y-8">
            {/* Welcome & Quick Actions */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 mb-2">
              <div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-1">
                  Hello {username}!
                </h2>
                <p className="text-gray-700 dark:text-gray-300">
                  Welcome back to your academic dashboard. Select a course to
                  get started with exam preparation.
                </p>
              </div>
              {/* Quick Actions */}
              {/* <div className="flex flex-wrap gap-3">
          <button className="btn btn-primary">Start Mock Exam</button>
          <button className="btn btn-outline">Review Past Papers</button>
        </div> */}
            </div>

            {/* Courses Section */}
            <section>
              <div className="flex items-center justify-between my-4">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                  Your Courses
                </h3>
                <button
                  className="btn btn-sm btn-outline flex items-center gap-2"
                  onClick={() => setShowAddCourses(true)}
                >
                  Manage
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                {loadingCourses ? (
                  Array.from({ length: 3 }).map((_, idx) => (
                    <div
                      key={idx}
                      className="h-auto p-6 flex flex-col items-center justify-center text-center border-2 border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 shadow hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                    >
                      <div className="flex items-center justify-center gap-2 font-semibold text-lg mb-2">
                        <span className="skeleton w-20 h-6 rounded" />
                      </div>
                      <div className="skeleton w-32 h-4 rounded mb-1" />
                    </div>
                  ))
                ) : (
                  <React.Fragment>
                    {courses.length === 0 ? (
                      <div className="col-span-full flex flex-col items-center justify-center py-12">
                        <div className="text-lg text-gray-500 dark:text-gray-400 mb-2">
                          No courses found.
                        </div>
                        <div className="text-sm text-gray-400">
                          Click{" "}
                          <span className="font-semibold">Manage</span> to get
                          started.
                        </div>
                      </div>
                    ) : (
                      courses.map((course) => {
                        let countdown = "";
                        let badgeColor = "badge-info badge-outline";
                        if (course.examDate) {
                          const now = new Date();
                          const exam = new Date(course.examDate);
                          // Remove time portion for accurate day diff
                          now.setHours(0, 0, 0, 0);
                          exam.setHours(0, 0, 0, 0);
                          const diff = Math.ceil(
                            (exam - now) / (1000 * 60 * 60 * 24)
                          );
                          if (diff < 0) {
                            countdown = "Exam passed";
                            badgeColor = "badge badge-outline badge-success";
                          } else if (diff === 0) {
                            // If examTime is set, show hours left
                            if (course.examTime) {
                              const [examHour, examMinute] = course.examTime
                                .split(":")
                                .map(Number);
                              const nowTime = new Date();
                              const examDateTime = new Date(course.examDate);
                              examDateTime.setHours(examHour || 0, examMinute || 0, 0, 0);
                              const msLeft = examDateTime - nowTime;
                              const hoursLeft = Math.max(
                                0,
                                Math.floor(msLeft / (1000 * 60 * 60))
                              );
                              if (msLeft > 0) {
                                countdown = `${hoursLeft} hour${
                                  hoursLeft !== 1 ? "s" : ""
                                } left!`;
                              } else {
                                countdown = "Exam started!";
                              }
                            } else {
                              countdown = "Exam today!";
                            }
                            badgeColor = "badge badge-error badge-outline";
                          } else if (diff === 1) {
                            countdown = "Exam tomorrow";
                            badgeColor = "badge badge-error badge-outline";
                          } else if (diff >= 2 && diff <= 7) {
                            countdown = `${diff} days left`;
                            badgeColor = "badge badge-warning badge-outline";
                          } else {
                            countdown = `${diff} days left`;
                            badgeColor = "badge badge-info badge-outline";
                          }
                        }
                        return (
                          <button
                            key={course.id}
                            className="h-auto p-6 flex flex-col items-center justify-center text-center border-2 border-gray-300 dark:border-gray-600 rounded-xl hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                            onClick={() => navigate(`/courses/${course.name}`)}
                          >
                            <div className="flex items-center justify-center gap-2 font-semibold text-lg text-gray-900 dark:text-gray-100">
                              {course.name}
                              {course.examDate && (
                                <span className={badgeColor + " text-xs"}>{countdown}</span>
                              )}
                            </div>
                            <div className="text-sm text-gray-700 dark:text-gray-300 mt-1">
                              {course.title}
                            </div>
                          </button>
                        );
                      })
                    )}
                    {showAddCourses && (
                      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
                        <div className="relative bg-base-100 rounded-xl shadow-lg w-full max-w-5xl mx-auto p-0">
                          <button
                            className="absolute top-2 right-2 btn btn-sm btn-circle btn-ghost"
                            onClick={() => setShowAddCourses(false)}
                            aria-label="Close"
                          >
                            ✕
                          </button>
                          <div className="p-4">
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
                  </React.Fragment>
                )}
              </div>
            </section>

            {/* Recent Activity Section */}
            <section>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Recent Activity
              </h3>
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6">
                {recentActivity.length === 0 ? (
                  <div className="text-gray-500 dark:text-gray-400">
                    No recent activity.
                  </div>
                ) : (
                  <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                    {recentActivity.map((activity, idx) => (
                      <li
                        key={idx}
                        className="py-3 flex items-center justify-between"
                      >
                        <div>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {activity.type}
                          </span>
                          <span className="ml-2 text-gray-700 dark:text-gray-300">
                            {activity.course}
                          </span>
                          <span className="ml-2 text-gray-500 dark:text-gray-400 text-sm">
                            {activity.date}
                          </span>
                        </div>
                        <div className="text-right">
                          {activity.type === "Mock Exam" && (
                            <span className="text-blue-600 dark:text-blue-400 font-semibold">
                              Score: {activity.score}%
                            </span>
                          )}
                          {activity.type === "Study Session" && (
                            <span className="text-green-600 dark:text-green-400 font-semibold">
                              {activity.duration}
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </section>
          </main>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
