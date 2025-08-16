import { useRef } from "react";
import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { getPapers, listPastPapers, getPastPaperPdfUrl, fetchEnrollmentDetails } from "../api";

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

function useCountdown(exam_date, exam_time) {
  const [timeLeft, setTimeLeft] = useState(null);

  useEffect(() => {
    if (!exam_date) {
      setTimeLeft(null);
      return;
    }

    function calculateTimeLeft() {
      const examDateTime = new Date(
        exam_time ? `${exam_date}T${exam_time}` : `${exam_date}T00:00:00`
      );
      const now = new Date();

      if (!exam_time) {
        now.setHours(0, 0, 0, 0);
        examDateTime.setHours(0, 0, 0, 0);
      }

      const diff = examDateTime.getTime() - now.getTime();

      if (diff <= 0) return null;

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));

      if (!exam_time) {
        // only show days if no exam_time
        return { days };
      }

      return {
        days,
        hours: Math.floor((diff / (1000 * 60 * 60)) % 24),
        minutes: Math.floor((diff / (1000 * 60)) % 60),
      };
    }

    setTimeLeft(calculateTimeLeft());

    // update every minute
    const interval = setInterval(() => setTimeLeft(calculateTimeLeft()), 60000);

    return () => clearInterval(interval);
  }, [exam_date, exam_time]);

  return timeLeft;
}

const MockExam = () => {
  const { courseId } = useParams();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [pastPapers, setPastPapers] = useState([]);
  const [pdfView, setPdfView] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showQuizModal, setShowQuizModal] = useState(false);
  const [selectedMockExamIndex, setSelectedMockExamIndex] = useState(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [tab, setTab] = useState("pastPapers");
  const [mockExams, setMockExams] = useState([]); // Placeholder for generated exams
  const [generating, setGenerating] = useState(false);
  const [mockError, setMockError] = useState("");
  const [enrollmentDetails, setEnrollmentDetails] = useState(null);
  const timeLeft = useCountdown(enrollmentDetails?.exam_date, enrollmentDetails?.exam_time) || null;

  let userId = "";
      try {
        // Extract userId from JWT token in localStorage
        const token = localStorage.getItem("token");
        if (token) {
          // Decode JWT (base64 decode payload)
          const payload = JSON.parse(atob(token.split('.')[1]));
          userId = payload.user_id;
        }
        if (!userId) return;
      } catch (error) {
        console.error("Failed to extract user ID from token:", error);
      }

  // Prevent background scroll when any modal is open
  useEffect(() => {
    if (showModal || showQuizModal) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [showModal, showQuizModal]);

  const [noPapers, setNoPapers] = useState(false);
  // Use a ref to track if a download is in progress, so tab switches don't reset the state
  const downloadingRef = useRef(false);
  const fetchPapers = async () => {
    setDownloading(true);
    downloadingRef.current = true;
    setError("");
    setNoPapers(false);
    try {
      const res = await getPapers(courseId);
      if (res?.no_papers) {
        setNoPapers(true);
        setPastPapers([]);
        setError(`No past papers found for this course.`);
        setDownloading(false);
        downloadingRef.current = false;
        return;
      }
      const papers = await listPastPapers(courseId);
      setPastPapers(papers);
    } catch (e) {
      setError("Failed to download past papers. Try again later.");
    }
    setDownloading(false);
    downloadingRef.current = false;
  };

  useEffect(() => {
    setNoPapers(false); // Only reset on course change
    setDownloading(true); // Set downloading state immediately when fetching papers
    downloadingRef.current = true;
    listPastPapers(courseId)
      .then((papers) => {
        setPastPapers(papers);
        setDownloading(false);
        downloadingRef.current = false;
      })
      .catch(() => {
        setPastPapers([]);
        setDownloading(false);
        downloadingRef.current = false;
      });
  }, [courseId]);

  useEffect(() => {
    if (courseId) {
      fetchEnrollmentDetails(userId, courseId)
        .then(setEnrollmentDetails)
        .catch(() => setEnrollmentDetails(null));
    }
  }, [courseId]);

  // Dummy course info (replace with real API if available)
  const courseInfo = {
    code: courseId,
    title: enrollmentDetails?.course_title || "",
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
            {!enrollmentDetails ? (
              <>
                <h1 className="text-2xl font-bold mb-1">{courseInfo.code}</h1>
                <div className="skeleton h-4 w-48 bg-gray-200 dark:bg-gray-600"></div>
              </>
            ) : (
              <>
                <h1 className="text-2xl font-bold mb-1">{courseInfo.code}</h1>
                <p className="text-gray-600 dark:text-gray-300 text-sm">
                  {courseInfo.title}
                </p>
              </>
            )}
          </div>
          {!enrollmentDetails ? (
            <div className="grid grid-flow-col gap-5 text-center auto-cols-max">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="flex flex-col w-16 h-22 p-2 bg-neutral rounded-box text-neutral-content">
                  <div className="skeleton h-12 w-12 bg-gray-500"></div>
                  <div className="skeleton h-4 w-8 bg-gray-500 mt-3"></div>
                </div>
              ))}
            </div>
          ) : timeLeft && (
            <div className="grid grid-flow-col gap-5 text-center auto-cols-max">
            <div className="flex flex-col p-2 bg-neutral rounded-box text-neutral-content">
              <span className="countdown font-mono text-5xl">
                <span style={{"--value":timeLeft.days} /* as React.CSSProperties */ } aria-live="polite">{timeLeft.days}</span>
              </span>
              days
            </div>
            {(timeLeft.hours != null && timeLeft.minutes != null) && (
              <>
            <div className="flex flex-col p-2 bg-neutral rounded-box text-neutral-content">
              <span className="countdown font-mono text-5xl">
                <span style={{"--value":timeLeft.hours} /* as React.CSSProperties */ } aria-live="polite">{timeLeft.hours}</span>
              </span>
              hours
            </div>
            <div className="flex flex-col p-2 bg-neutral rounded-box text-neutral-content">
              <span className="countdown font-mono text-5xl">
                <span style={{"--value":timeLeft.minutes} /* as React.CSSProperties */ } aria-live="polite">{timeLeft.minutes}</span>
              </span>
              min
            </div>
            </>
            )}
          </div>
          )}
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
                  <div className="tooltip tooltip-left" data-tip="You may be redirected to UQ Authenticate">
                    <span>Get Past Papers</span>
                  </div>
                )}
              </button>
            </div>
            {error && !noPapers && (
              <div className="text-red-500 mb-2">{error}</div>
            )}
            {downloading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {[...Array(4)].map((_, index) => (
                  <div
                    key={index}
                    className="bg-white dark:bg-gray-700 rounded-lg shadow p-4 flex flex-col gap-2 border border-gray-100 dark:border-gray-600"
                  >
                    <div className="flex items-center gap-2">
                      <div className="skeleton w-6 h-6 bg-gray-300 dark:bg-gray-600 rounded"></div>
                      <div className="skeleton w-32 h-6 bg-gray-300 dark:bg-gray-600"></div>
                    </div>
                    <div className="skeleton w-full h-4 bg-gray-200 dark:bg-gray-500 mb-2"></div>
                    <div className="skeleton w-24 h-8 bg-gray-300 dark:bg-gray-600 mt-auto"></div>
                  </div>
                ))}
              </div>
            ) : noPapers ? (
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
        {/* Quiz Modal - Single question view with pagination */}
        {showQuizModal && selectedMockExamIndex != null && mockExams[selectedMockExamIndex] && (
          <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" />
            <div className="relative z-10 w-full max-w-2xl mx-auto rounded-2xl shadow-2xl bg-white dark:bg-gray-900 flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between px-6 py-3 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-3">
                  <svg className="w-6 h-6 text-indigo-500" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                  </svg>
                  <div>
                    <div className="font-semibold text-gray-800 dark:text-gray-100 truncate">{mockExams[selectedMockExamIndex].name}</div>
                    <div className="text-xs text-gray-500">{mockExams[selectedMockExamIndex].date}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <div className="text-sm text-gray-600 dark:text-gray-300">Question {currentQuestionIndex + 1} / {mockExams[selectedMockExamIndex].questions.length}</div>
                  <button
                    className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-200/80 dark:bg-gray-700/80 hover:bg-red-500 hover:text-white transition-colors text-gray-700 dark:text-gray-200 shadow"
                    onClick={() => {
                      setShowQuizModal(false);
                      setSelectedMockExamIndex(null);
                      setCurrentQuestionIndex(0);
                      setAnswers([]);
                    }}
                    aria-label="Close Quiz"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="p-6 flex-1 flex flex-col gap-4">
                <div className="text-gray-800 dark:text-gray-100 text-lg">
                  {mockExams[selectedMockExamIndex].questions[currentQuestionIndex].text}
                </div>
                {/* Render by question type */}
                {mockExams[selectedMockExamIndex].questions[currentQuestionIndex].type === 'mcq' ? (
                  <div className="flex flex-col gap-2">
                    {mockExams[selectedMockExamIndex].questions[currentQuestionIndex].choices.map((choice, ci) => (
                      <label key={ci} className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 ${answers[currentQuestionIndex] === choice ? 'bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-200 dark:border-indigo-800' : 'border border-transparent'}`}>
                        <input
                          type="radio"
                          name={`q-${selectedMockExamIndex}-${currentQuestionIndex}`}
                          checked={answers[currentQuestionIndex] === choice}
                          onChange={() => {
                            const copy = [...answers];
                            copy[currentQuestionIndex] = choice;
                            setAnswers(copy);
                          }}
                          className="radio radio-sm"
                        />
                        <span className="text-sm text-gray-800 dark:text-gray-100">{choice}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea
                    value={answers[currentQuestionIndex] || ''}
                    onChange={(e) => {
                      const copy = [...answers];
                      copy[currentQuestionIndex] = e.target.value;
                      setAnswers(copy);
                    }}
                    placeholder="Type your answer here..."
                    className="w-full h-40 p-3 border rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 resize-none focus:outline-none"
                  />
                )}

                <div className="flex items-center justify-between mt-auto">
                  <div className="flex gap-2">
                    <button
                      className={`btn btn-sm ${currentQuestionIndex === 0 ? 'btn-disabled' : 'btn-outline'}`}
                      onClick={() => setCurrentQuestionIndex((i) => Math.max(0, i - 1))}
                      disabled={currentQuestionIndex === 0}
                    >
                      Previous
                    </button>
                    <button
                      className={`btn btn-sm ${currentQuestionIndex === mockExams[selectedMockExamIndex].questions.length - 1 ? 'btn-disabled' : 'btn-outline'}`}
                      onClick={() => setCurrentQuestionIndex((i) => Math.min(mockExams[selectedMockExamIndex].questions.length - 1, i + 1))}
                      disabled={currentQuestionIndex === mockExams[selectedMockExamIndex].questions.length - 1}
                    >
                      Next
                    </button>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => {
                        // Save answer locally and keep modal open
                        const copy = [...mockExams];
                        copy[selectedMockExamIndex] = { ...copy[selectedMockExamIndex], lastSaved: new Date().toISOString() };
                        setMockExams(copy);
                      }}
                    >
                      Save
                    </button>
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => {
                        // Simple submit flow: mark exam as submitted and close modal
                        const copy = [...mockExams];
                        copy[selectedMockExamIndex] = { ...copy[selectedMockExamIndex], submitted: true, answers };
                        setMockExams(copy);
                        setShowQuizModal(false);
                        setSelectedMockExamIndex(null);
                        setCurrentQuestionIndex(0);
                        setAnswers([]);
                      }}
                    >
                      Submit Exam
                    </button>
                  </div>
                </div>
              </div>
            </div>
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
                    // Create a small sample of questions for the mock exam (mix of text and MCQ)
                    const sampleQuestions = [
                      { id: 1, type: 'text', text: 'Explain the main purpose of the module covered in Week 1.' },
                      { id: 2, type: 'mcq', text: 'Which data structure gives O(1) average lookups?', choices: ['Array', 'Hash Table', 'Linked List', 'Binary Tree'] },
                      { id: 3, type: 'text', text: 'Write a short algorithm to perform Y and explain its complexity.' },
                      { id: 4, type: 'mcq', text: 'Which sorting algorithm is stable?', choices: ['QuickSort', 'MergeSort', 'HeapSort', 'SelectionSort'] },
                      { id: 5, type: 'text', text: 'Summarise the key limitations of approach A.' },
                    ];
                    setMockExams([
                      ...(mockExams || []),
                      {
                        name: `Mock Exam ${mockExams.length + 1}`,
                        date: new Date().toLocaleString(),
                        questions: sampleQuestions,
                        submitted: false,
                      },
                    ]);
                    setGenerating(false);
                  }, 800);
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
                    <div className="mt-auto flex gap-2">
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={() => {
                          // Open quiz modal for this exam
                          setSelectedMockExamIndex(idx);
                          setCurrentQuestionIndex(0);
                          // initialize answers array with nulls for unanswered
                          const qlen = exam.questions?.length || 0;
                          setAnswers(Array(qlen).fill(null));
                          setShowQuizModal(true);
                        }}
                      >
                        View
                      </button>
                      <button
                        className={`btn btn-sm ${exam.submitted ? 'btn-success' : 'btn-ghost'}`}
                        onClick={() => {
                          // quick toggle mark as complete locally
                          const copy = [...mockExams];
                          copy[idx] = { ...copy[idx], submitted: !copy[idx].submitted };
                          setMockExams(copy);
                        }}
                      >
                        {exam.submitted ? 'Submitted' : 'Mark'}
                      </button>
                    </div>
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
