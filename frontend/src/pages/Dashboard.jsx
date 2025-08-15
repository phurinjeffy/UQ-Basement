const Dashboard = () => {
  const courses = [
    { id: 1, name: "COMP3506", title: "Algorithms & Data Structures" },
    { id: 2, name: "COMP3702", title: "Artificial Intelligence" },
    { id: 3, name: "COMP3710", title: "Pattern Recognition" },
    { id: 4, name: "COMP4601", title: "Software Architecture" },
  ];

  const username = "Student";
  const progressValue = 65;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto p-6">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            Hello {username}!
          </h2>
          <p className="text-gray-700 dark:text-gray-300">
            Welcome back to your academic dashboard. Select a course to get started with exam preparation.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Course Selection */}
          <div className="lg:col-span-2">
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
              Your Courses
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {courses.map((course) => (
                <button
                  key={course.id}
                  className="h-auto p-6 flex flex-col items-center justify-center text-center border-2 border-gray-300 dark:border-gray-600 rounded-xl hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="font-semibold text-lg text-gray-900 dark:text-gray-100">{course.name}</div>
                  <div className="text-sm text-gray-700 dark:text-gray-300 mt-1">{course.title}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Progress & Statistics */}
          <div className="space-y-6">
            {/* Progress Card */}
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-gray-100 font-semibold">
                📈 <span>Progress</span>
              </div>
              <div className="text-center mb-4">
                <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">{progressValue}%</div>
                <div className="text-sm text-gray-900 dark:text-gray-100">Overall Progress</div>
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
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg p-4">
              <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-gray-100 font-semibold">
                📄 <span>Statistics</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-500 dark:text-gray-400">Mock Exams Taken</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">12</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-500 dark:text-gray-400">Topics Mastered</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">8</span>
              </div>
              <div className="flex justify-between mb-1">
                <span className="text-sm text-gray-500 dark:text-gray-400">Study Streak</span>
                <span className="font-semibold text-gray-900 dark:text-gray-100">5 days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-500 dark:text-gray-400">Avg. Score</span>
                <span className="font-semibold text-blue-600 dark:text-blue-400">78%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
