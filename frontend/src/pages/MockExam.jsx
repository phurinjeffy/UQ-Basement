import { useRef } from "react";
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
  const [tab, setTab] = useState("pastPapers");
  const [mockExams, setMockExams] = useState([]); // Placeholder for generated exams
  const [generating, setGenerating] = useState(false);
  const [mockError, setMockError] = useState("");

  // Prevent background scroll when modal is open
  useEffect(() => {
    if (showModal) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [showModal]);

  const [noPapers, setNoPapers] = useState(false);
  const fetchPapers = async () => {
    setDownloading(true);
    setError("");
    setNoPapers(false);
    try {
      const res = await getPapers(courseId);
      if (res?.no_papers) {
        setNoPapers(true);
        setPastPapers([]);
        setError(`No past papers found for this course.`);
        setDownloading(false);
        return;
      }
      const papers = await listPastPapers(courseId);
      setPastPapers(papers);
    } catch (e) {
      setError("Failed to download past papers. Try again later.");
    }
    setDownloading(false);
  };

  useEffect(() => {
    setNoPapers(false); // Only reset on course change
    listPastPapers(courseId)
      .then((papers) => {
        setPastPapers(papers);
      })
      .catch(() => {
        setPastPapers([]);
      });
  }, [courseId]);

  // Dummy course info (replace with real API if available)
  const courseInfo = {
    code: courseId,
    name: "Course Name Placeholder",
    description:
      "This is a short description of the course. It covers the main topics and exam structure. Replace with real data if available.",
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto py-10 px-4 lg:px-8">
        {/* Breadcrumbs (only for course pages) */}
        <div className="breadcrumbs text-sm mb-6">
          <ul>
            <li>
              <a href="/dashboard">
                {/* Dashboard Icon */}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  className="h-4 w-4 stroke-current"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z"
                  />
                </svg>{" "}
                Dashboard
              </a>
            </li>
            <li>
              <span className="inline-flex items-center gap-2">
                {/* Course Icon (Book) */}
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  className="h-4 w-4 stroke-current"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 5a2 2 0 012-2h12a2 2 0 012 2v14l-4-2-4 2-4-2-4 2V5z"
                  />
                </svg>{" "}
                {courseInfo.code}
              </span>
            </li>
          </ul>
        </div>

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

        {/* Tabs */}
        <div className="flex gap-4 mb-8 border-b border-gray-200 dark:border-gray-700">
          <button
            className={`px-4 py-2 font-semibold focus:outline-none border-b-2 transition-all ${
              tab === "pastPapers"
                ? "border-indigo-500 text-indigo-700 dark:text-indigo-300"
                : "border-transparent text-gray-500 dark:text-gray-400"
            }`}
            onClick={() => setTab("pastPapers")}
            disabled={false}
          >
            Past Papers
          </button>
          <button
            className={`px-4 py-2 font-semibold focus:outline-none border-b-2 transition-all ${
              tab === "mockExams"
                ? "border-indigo-500 text-indigo-700 dark:text-indigo-300"
                : "border-transparent text-gray-500 dark:text-gray-400"
            } ${
              pastPapers.length === 0 ? "opacity-50 cursor-not-allowed" : ""
            }`}
            onClick={() => pastPapers.length > 0 && setTab("mockExams")}
            disabled={pastPapers.length === 0}
          >
            Mock Exams
          </button>
        </div>

        {/* Tab Content */}
        {tab === "pastPapers" && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Past Papers</h2>
              <button
                className="btn btn-secondary"
                onClick={fetchPapers}
                disabled={downloading || noPapers}
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
                    </svg>
                    Downloading...
                  </span>
                ) : noPapers ? (
                  <span>No Past Papers</span>
                ) : (
                  <span>Get Past Papers</span>
                )}
              </button>
            </div>
            {error && !noPapers && (
              <div className="text-red-500 mb-2">{error}</div>
            )}
            {noPapers ? (
              <div className="text-gray-500">
                No past papers found for this course.
              </div>
            ) : pastPapers.length === 0 ? (
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
        )}

        {tab === "mockExams" && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Mock Exams</h2>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setGenerating(true);
                  setMockError("");
                  setTimeout(() => {
                    setMockExams([
                      ...(mockExams || []),
                      {
                        name: `Mock Exam ${mockExams.length + 1}`,
                        date: new Date().toLocaleString(),
                      },
                    ]);
                    setGenerating(false);
                  }, 1500);
                }}
                disabled={generating}
              >
                {generating ? (
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
                    </svg>
                    Generating...
                  </span>
                ) : (
                  "Generate Mock Exam"
                )}
              </button>
            </div>
            {mockError && <div className="text-red-500 mb-2">{mockError}</div>}
            {!mockExams || mockExams.length === 0 ? (
              <div className="text-gray-500">No mock exams generated yet.</div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {mockExams.map((exam, idx) => (
                  <div
                    key={idx}
                    className="bg-white dark:bg-gray-700 rounded-lg shadow p-4 flex flex-col gap-2 border border-gray-100 dark:border-gray-600"
                  >
                    <div className="flex items-center gap-2">
                      <svg
                        className="w-6 h-6 text-indigo-500"
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
                      <span className="font-semibold">{exam.name}</span>
                    </div>
                    <div className="truncate text-gray-700 dark:text-gray-200 text-sm mb-2">
                      Generated: {exam.date}
                    </div>
                    <button className="btn btn-sm btn-outline mt-auto" disabled>
                      View (Coming Soon)
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Modal PDF Viewer - Full Screen */}
        {showModal && pdfView && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Blurred background */}
            <div className="absolute inset-0 bg-black/10 backdrop-blur-md transition-all duration-200" />
            {/* Modal box */}
            <div className="relative z-10 w-full max-w-4xl mx-auto rounded-2xl shadow-2xl bg-white dark:bg-gray-900 flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700">
              {/* Modern Top Bar */}
              <div className="flex items-center justify-between px-6 py-3 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <svg
                    className="w-6 h-6 text-indigo-500"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M7 7V3a1 1 0 011-1h8a1 1 0 011 1v18a1 1 0 01-1 1H8a1 1 0 01-1-1v-4"
                    />
                    <rect
                      x="3"
                      y="7"
                      width="8"
                      height="13"
                      rx="2"
                      fill="currentColor"
                      className="text-indigo-100 dark:text-gray-800"
                    />
                  </svg>
                  <span
                    className="font-semibold text-gray-800 dark:text-gray-100 truncate max-w-xs sm:max-w-md"
                    title={pdfView}
                  >
                    {pdfView}
                  </span>
                </div>
                <button
                  className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-200/80 dark:bg-gray-700/80 hover:bg-red-500 hover:text-white transition-colors text-gray-700 dark:text-gray-200 shadow"
                  onClick={() => {
                    setShowModal(false);
                    setPdfView(null);
                  }}
                  aria-label="Close PDF Viewer"
                >
                  <svg
                    className="w-6 h-6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
              <div className="flex-1 flex flex-col items-center justify-center">
                <iframe
                  src={getPastPaperPdfUrl(courseId, pdfView)}
                  title={pdfView}
                  className="w-full h-full flex-1 border-none bg-white dark:bg-gray-900"
                  style={{ minHeight: "80vh" }}
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
