import { useState } from "react";
import { fetchCourses } from "../api";

function AddCourses({ onConfirm, initialCourses = [] }) {
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [courses, setCourses] = useState(initialCourses);
  const [loading, setLoading] = useState(false);

  // Fixed fetchSuggestions function - remove unnecessary parameters
  const fetchSuggestions = async (hint) => {
    if (!hint.trim()) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const coursesData = await fetchCourses(hint);
      setSuggestions(coursesData);
    } catch (e) {
      console.error("Error fetching courses:", e);
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  };

  // Handle input change with debouncing for better UX
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInput(value);
    
    // Clear suggestions if input is empty
    if (!value.trim()) {
      setSuggestions([]);
      setLoading(false);
      return;
    }
    
    fetchSuggestions(value);
  };

  // Add course from suggestion (store object)
  const addCourse = (courseObj) => {
    if (!courses.some((c) => c.name === courseObj.name)) {
      setCourses([...courses, courseObj]);
    }
    setInput("");
    setSuggestions([]);
  };

  // Remove course from list
  const removeCourse = (courseObj) => {
    setCourses(courses.filter((c) => c.name !== courseObj.name));
  };

  // Confirm selected courses
  const handleConfirm = () => {
    if (onConfirm) onConfirm(courses);
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-8 bg-white/90 dark:bg-slate-800/90 backdrop-blur-lg rounded-3xl shadow-xl border border-white/20 dark:border-slate-700/50">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
          Add Your Courses
        </h2>
        <p className="text-gray-600 dark:text-gray-300">Search and select the courses you're taking this semester</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left column: Search & Results */}
        <div className="space-y-4">
          <div className="relative">
            <input
              type="text"
              className="w-full px-4 py-3 bg-white/50 dark:bg-slate-700/50 backdrop-blur-sm rounded-xl border border-gray-200 dark:border-slate-600 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-all duration-200 outline-none text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400"
              placeholder="Search course code (e.g., CSSE2310)..."
              value={input}
              onChange={handleInputChange}
              autoComplete="off"
            />
            {loading && (
              <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600"></div>
              </div>
            )}
          </div>
          
          {suggestions.length > 0 && (
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-xl border border-gray-200 dark:border-slate-600 shadow-lg overflow-hidden">
              {suggestions.map((s, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="w-full p-4 text-left hover:bg-indigo-50 dark:hover:bg-slate-700 transition-colors duration-150 border-b border-gray-100 dark:border-slate-600 last:border-b-0"
                  onClick={() => addCourse(s)}
                >
                  <div className="font-semibold text-gray-900 dark:text-gray-100">{s.name}</div>
                  <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">{s.course_title}</div>
                </button>
              ))}
            </div>
          )}
          
          {!loading && input.trim() && suggestions.length === 0 && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <svg className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              No courses found
            </div>
          )}
        </div>
        
        {/* Right column: Selected Courses */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Selected Courses ({courses.length})</h3>
          <div className="max-h-96 overflow-y-auto space-y-3 scrollbar-hide">
            {courses.length === 0 ? (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <svg className="mx-auto h-12 w-12 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
                No courses selected yet
              </div>
            ) : (
              courses.map((course, idx) => (
                <div key={idx} className="bg-white/60 dark:bg-slate-700/60 backdrop-blur-sm rounded-xl p-4 border border-gray-200 dark:border-slate-600 relative hover-lift">
                  <button
                    type="button"
                    className="absolute top-3 right-3 w-6 h-6 rounded-full bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 hover:bg-red-600 hover:text-white transition-all duration-200 flex items-center justify-center text-sm font-medium"
                    onClick={() => removeCourse(course)}
                    aria-label="Remove course"
                  >
                    ×
                  </button>
                  
                  <div className="pr-8 mb-3">
                    <div className="font-semibold text-gray-900 dark:text-gray-100">{course.name}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{course.course_title}</div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Exam Date</label>
                      <input
                        type="date"
                        className="w-full px-3 py-2 text-sm bg-white/70 dark:bg-slate-600/70 rounded-lg border border-gray-200 dark:border-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-all duration-200 outline-none text-gray-900 dark:text-gray-100"
                        value={course.examDate || ""}
                        onChange={e => {
                          const newDate = e.target.value;
                          setCourses(courses.map((c, i) => i === idx ? { ...c, examDate: newDate } : c));
                        }}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">Time</label>
                      <input
                        type="time"
                        className="w-full px-3 py-2 text-sm bg-white/70 dark:bg-slate-600/70 rounded-lg border border-gray-200 dark:border-slate-500 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-all duration-200 outline-none text-gray-900 dark:text-gray-100"
                        value={course.examTime || ""}
                        onChange={e => {
                          const newTime = e.target.value;
                          setCourses(courses.map((c, i) => i === idx ? { ...c, examTime: newTime } : c));
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
      
      <div className="mt-8 pt-6 border-t border-gray-200 dark:border-slate-600">
        <button
          className={`w-full py-4 px-6 rounded-xl font-semibold text-white transition-all duration-200 ${
            courses.length === 0
              ? 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
              : 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 transform hover:scale-[1.02] shadow-lg hover:shadow-xl'
          }`}
          disabled={courses.length === 0}
          onClick={handleConfirm}
        >
          {courses.length === 0 
            ? 'Select courses to continue' 
            : `Continue with ${courses.length} course${courses.length !== 1 ? 's' : ''}`
          }
        </button>
      </div>
    </div>
  );
}

export default AddCourses;