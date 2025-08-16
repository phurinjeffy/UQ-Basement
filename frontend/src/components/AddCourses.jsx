
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
    <div className="w-full max-w-md mx-auto p-4 bg-base-100 rounded-xl shadow">
      <h2 className="text-xl font-bold mb-2">Add your courses</h2>
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
      {courses.length > 0 && (
        <div className="mb-2">
          <h3 className="font-semibold mb-1">Selected Courses:</h3>
          <ul className="flex flex-wrap gap-2">
            {courses.map((course, idx) => (
              <li key={idx} className="badge badge-outline flex items-center gap-2 whitespace-normal break-words h-fit">
                <span className="font-bold break-words whitespace-normal">{course.name}</span>
                <span className="text-xs break-words whitespace-normal">{course.course_title}</span>
                <button type="button" className="ml-2 text-error" onClick={() => removeCourse(course)}>
                  ✕
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <button
        className="btn btn-primary w-full mt-2"
        disabled={courses.length === 0}
        onClick={handleConfirm}
      >
        Confirm & Continue
      </button>
    </div>
  );
}

export default AddCourses;
