import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getPapers, listPastPapers, getPastPaperPdfUrl } from "../api";

const getPaperMeta = (filename) => {
  // Example: Semester_One_Final_Examinations_2021_DECO2500.pdf
  const match = filename.match(/Semester[_ ](One|Two).*?(\d{4})/i);
  return {
    semester: match
      ? match[1].toLowerCase() === "one"
        ? "Semester 1"
        : "Semester 2"
      : "",
    year: match ? match[2] : "",
    name: filename.replace(/_/g, " ").replace(/\.pdf$/, ""),
  };
};

const MockExam = () => {
  const { courseId } = useParams();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [pastPapers, setPastPapers] = useState([]);
  const [pdfView, setPdfView] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const fetchPapers = async () => {
    setDownloading(true);
    setError("");
    try {
      await getPapers(courseId);
      const papers = await listPastPapers(courseId);
      setPastPapers(papers);
    } catch (e) {
      setError("Failed to download past papers. Try again later.");
    }
    setDownloading(false);
  };

  useEffect(() => {
    listPastPapers(courseId)
      .then(setPastPapers)
      .catch(() => setPastPapers([]));
  }, [courseId]);

  // Dummy course info (replace with real API if available)
  const courseInfo = {
    code: courseId,
    name: "Course Name Placeholder",
    description:
      "This is a short description of the course. It covers the main topics and exam structure. Replace with real data if available.",
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 py-10 px-4">
      <div className="max-w-3xl mx-auto">
        {/* Course Info Card */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-6 mb-8 flex flex-col md:flex-row items-center gap-6">
          <div className="flex-shrink-0 bg-indigo-100 dark:bg-indigo-900 rounded-full w-20 h-20 flex items-center justify-center">
            <span className="text-3xl text-indigo-600 dark:text-indigo-300 font-bold">
              {courseInfo.code.slice(0, 4)}
            </span>
          </div>
          <div className="flex-1">
            <h1 className="text-2xl font-bold mb-1">
              {courseInfo.code}{" "}
              <span className="text-lg font-normal text-gray-500">
                {courseInfo.name}
              </span>
            </h1>
            <p className="text-gray-600 dark:text-gray-300 text-sm">
              {courseInfo.description}
            </p>
          </div>
        </div>

        {/* Past Papers Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Past Papers</h2>
            <button
              className="btn btn-secondary"
              onClick={fetchPapers}
              disabled={downloading}
            >
              {downloading ? (
                <span className="flex items-center gap-2">
                  <svg
                    className="animate-spin h-4 w-4 mr-1"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v8z"
                    />
                  </svg>{" "}
                  Downloading...
                </span>
              ) : (
                "Get Past Papers"
              )}
            </button>
          </div>
          {error && <div className="text-red-500 mb-2">{error}</div>}
          {pastPapers.length === 0 ? (
            <div className="text-gray-500">
              No past papers found for this course.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {pastPapers.map((pdf) => {
                const meta = getPaperMeta(pdf);
                return (
                  <div
                    key={pdf}
                    className="bg-white dark:bg-gray-700 rounded-lg shadow p-4 flex flex-col gap-2 border border-gray-100 dark:border-gray-600"
                  >
                    <div className="flex items-center gap-2">
                      <svg
                        className="w-6 h-6 text-red-500"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M12 4v16m8-8H4"
                        />
                      </svg>
                      <span className="font-semibold">
                        {meta.year} {meta.semester}
                      </span>
                    </div>
                    <div className="truncate text-gray-700 dark:text-gray-200 text-sm mb-2">
                      {meta.name}
                    </div>
                    <button
                      className="btn btn-sm btn-outline mt-auto"
                      onClick={() => {
                        setPdfView(pdf);
                        setShowModal(true);
                      }}
                    >
                      View PDF
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal PDF Viewer - Full Screen */}
        {showModal && pdfView && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80">
            <div className="absolute inset-0 flex flex-col">
              <div className="flex justify-end p-4">
                <button
                  className="btn btn-error btn-lg text-lg px-6 py-2 rounded shadow-lg"
                  onClick={() => { setShowModal(false); setPdfView(null); }}
                  aria-label="Close PDF Viewer"
                >
                  ✕ Close
                </button>
              </div>
              <div className="flex-1 flex flex-col items-center justify-center">
                <div className="mb-2 font-semibold text-center text-white text-lg bg-black bg-opacity-40 px-4 py-2 rounded">
                  {pdfView}
                </div>
                <iframe
                  src={getPastPaperPdfUrl(courseId, pdfView)}
                  title={pdfView}
                  className="w-full h-full flex-1 border-none rounded-b-lg bg-white dark:bg-gray-900"
                  style={{ minHeight: '80vh' }}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MockExam;
