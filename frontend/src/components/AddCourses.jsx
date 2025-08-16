
import { useState } from "react";

function AddCourses({ onConfirm, initialCourses = [] }) {
  const [input, setInput] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [courses, setCourses] = useState(initialCourses);
  const [loading, setLoading] = useState(false);

  // Fetch suggestions from API only after 4+ characters
  const fetchSuggestions = async (hint) => {
    if (!hint || hint.length < 4) {
      setSuggestions([]);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`https://corsproxy.io/?url=https://api.library.uq.edu.au/v1/learning_resources/suggestions?hint=${encodeURIComponent(hint)}`);
      const data = await res.json();
      setSuggestions(data);
    } catch (e) {
      setSuggestions([]);
    }
    setLoading(false);
  };

  // Handle input change
  const handleInputChange = (e) => {
    const value = e.target.value;
    setInput(value);
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
                  <button type="button" className="w-full text-left" onClick={() => addCourse(s)}>
                    <span className="font-bold">{s.name}</span>
                    <span className="block text-xs text-gray-500">{s.course_title}</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        {/* Right column: Selected Courses */}
        <div className="max-h-[32rem] overflow-y-auto">
          <h3 className="font-semibold mb-1">Selected Courses:</h3>
          <ul className="flex flex-col gap-2">
            {courses.map((course, idx) => (
              <li key={idx} className="badge badge-outline flex flex-col gap-2 whitespace-normal break-words h-fit w-full p-3 relative">
                <button
                  type="button"
                  className="absolute top-2 right-2 text-error"
                  style={{ zIndex: 2 }}
                  onClick={() => removeCourse(course)}
                  aria-label="Remove"
                >
                  ✕
                </button>
                <div className="flex items-center gap-2 w-full">
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
        </div>
      </div>
      <button
        className="btn btn-primary w-full mt-6"
        disabled={courses.length === 0}
        onClick={handleConfirm}
      >
        Confirm & Continue
      </button>
    </div>
  );
}

export default AddCourses;
