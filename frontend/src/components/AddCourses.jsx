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
    <div className="w-full max-w-5xl mx-auto p-6 bg-base-100 rounded-xl shadow">
      <h2 className="text-xl font-bold mb-4">Add your courses</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left column: Search & Results */}
        <div>
          <input
            type="text"
            className="input input-bordered w-full mb-2"
            placeholder="Type course code..."
            value={input}
            onChange={handleInputChange}
            autoComplete="off"
          />
          {loading && <div className="text-sm text-gray-500">Loading...</div>}
          {suggestions.length > 0 && (
            <ul className="menu bg-base-200 rounded-box mb-2">
              {suggestions.map((s, idx) => (
                <li key={idx}>
                  <button 
                    type="button" 
                    className="w-full text-left" 
                    onClick={() => addCourse(s)}
                  >
                    <div>
                      <span className="font-bold">{s.name}</span>
                      <span className="block text-xs text-gray-500">{s.course_title}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {!loading && input.trim() && suggestions.length === 0 && (
            <div className="text-sm text-gray-500">No courses found</div>
          )}
        </div>
        
        {/* Right column: Selected Courses */}
        <div className="max-h-[32rem] overflow-y-auto">
          <h3 className="font-semibold mb-1">Selected Courses:</h3>
          {courses.length === 0 ? (
            <div className="text-gray-500 text-sm">No courses selected yet</div>
          ) : (
            <ul className="flex flex-col gap-2">
              {courses.map((course, idx) => (
                <li key={idx} className="badge badge-outline flex flex-col gap-2 whitespace-normal break-words h-fit w-full p-3 relative">
                  <button
                    type="button"
                    className="absolute top-2 right-2 text-error hover:bg-error hover:text-white rounded-full w-6 h-6 flex items-center justify-center text-sm"
                    style={{ zIndex: 2 }}
                    onClick={() => removeCourse(course)}
                    aria-label="Remove course"
                  >
                    ✕
                  </button>
                  <div className="flex items-center gap-2 w-full pr-8">
                    <span className="font-bold break-words whitespace-normal">{course.name}</span>
                    <span className="text-xs break-words whitespace-normal">{course.course_title}</span>
                  </div>
                  <div className="w-full mt-2 flex gap-2 items-center">
                    <label className="label text-xs">Exam Date:</label>
                    <input
                      type="date"
                      className="input input-bordered input-sm w-1/2"
                      value={course.examDate || ""}
                      onChange={e => {
                        const newDate = e.target.value;
                        setCourses(courses.map((c, i) => i === idx ? { ...c, examDate: newDate } : c));
                      }}
                    />
                    <label className="label text-xs">Time:</label>
                    <input
                      type="time"
                      className="input input-bordered input-sm w-1/2"
                      value={course.examTime || ""}
                      onChange={e => {
                        const newTime = e.target.value;
                        setCourses(courses.map((c, i) => i === idx ? { ...c, examTime: newTime } : c));
                      }}
                    />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      <button
        className="btn btn-primary w-full mt-6"
        disabled={courses.length === 0}
        onClick={handleConfirm}
      >
        Confirm & Continue ({courses.length} course{courses.length !== 1 ? 's' : ''})
      </button>
    </div>
  );
}

export default AddCourses;