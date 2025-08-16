import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { listPastPapers, getPastPaperPdfUrl } from "../api";
import axios from "axios";

const MockExam = () => {
  const { courseId } = useParams();
  // Placeholder for course info, can fetch real data later
  const [loading, setLoading] = useState(false);
  const [mockExam, setMockExam] = useState(null);
  const [error, setError] = useState("");
  const [pastPapers, setPastPapers] = useState([]);
  const [pdfView, setPdfView] = useState(null); // filename to view

  const [downloading, setDownloading] = useState(false);
  const handleDownloadPdfs = async () => {
    setDownloading(true);
    setError("");
    try {
      await axios.post(`/api/v1/ai/download-pdfs/${courseId}`);
      // Refresh list after download
      const papers = await listPastPapers(courseId);
      setPastPapers(papers);
    } catch (e) {
      setError("Failed to download past papers. Try again later.");
    }
    setDownloading(false);
  };

  useEffect(() => {
    // Fetch available past papers for this course
    listPastPapers(courseId)
      .then(setPastPapers)
      .catch(() => setPastPapers([]));
  }, [courseId]);

  const handleGenerate = () => {
    setLoading(true);
    setError("");
    // TODO: Call backend to generate mock exam for courseId
    setTimeout(() => {
      setMockExam({
        questions: [
          {
            id: 1,
            type: "mcq",
            question: "What is the time complexity of binary search?",
            options: ["O(n)", "O(log n)", "O(n log n)", "O(1)"],
          },
          {
            id: 2,
            type: "short",
            question: "Explain the difference between stack and queue.",
          },
        ],
      });
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-10 px-4">
      <div className="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl shadow p-8">
        <h1 className="text-2xl font-bold mb-4">Mock Exam for {courseId}</h1>

        {/* Past Papers Section */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">Past Papers</h2>
          <button
            className="btn btn-secondary mb-3"
            onClick={handleDownloadPdfs}
            disabled={downloading}
          >
            {downloading ? "Downloading..." : "Get Past Papers"}
          </button>
          {pastPapers.length === 0 ? (
            <div className="text-gray-500">No past papers found for this course.</div>
          ) : (
            <ul className="space-y-2">
              {pastPapers.map((pdf) => (
                <li key={pdf} className="flex items-center gap-2">
                  <button
                    className="btn btn-sm btn-outline"
                    onClick={() => setPdfView(pdf)}
                  >
                    View PDF: {pdf}
                  </button>
                  <a
                    href={getPastPaperPdfUrl(courseId, pdf)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline text-sm"
                  >
                    Download
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* PDF Viewer */}
        {pdfView && (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold">Viewing: {pdfView}</span>
              <button className="btn btn-xs btn-error" onClick={() => setPdfView(null)}>
                Close
              </button>
            </div>
            <iframe
              src={getPastPaperPdfUrl(courseId, pdfView)}
              title={pdfView}
              className="w-full h-96 border rounded"
            />
          </div>
        )}

        {/* Mock Exam Section */}
        {!mockExam ? (
          <>
            <button
              className="btn btn-primary mb-4"
              onClick={handleGenerate}
              disabled={loading}
            >
              {loading ? "Generating..." : "Generate Mock Exam"}
            </button>
            {/* Only show error if not about extraction */}
            {error && !error.includes('extract') && <div className="text-red-500">{error}</div>}
          </>
        ) : (
          <div>
            <h2 className="text-xl font-semibold mb-2">Questions</h2>
            <ol className="space-y-6">
              {mockExam.questions.map((q, idx) => (
                <li key={q.id} className="bg-gray-100 dark:bg-gray-700 rounded p-4">
                  <div className="font-medium mb-2">
                    Q{idx + 1}: {q.question}
                  </div>
                  {q.type === "mcq" && (
                    <ul className="space-y-1">
                      {q.options.map((opt, i) => (
                        <li key={i}>
                          <label className="flex items-center gap-2">
                            <input type="radio" name={`q${q.id}`} /> {opt}
                          </label>
                        </li>
                      ))}
                    </ul>
                  )}
                  {q.type === "short" && (
                    <textarea
                      className="w-full mt-2 p-2 rounded border border-gray-300 dark:border-gray-600"
                      rows={3}
                      placeholder="Your answer..."
                    />
                  )}
                </li>
              ))}
            </ol>
            <button className="btn btn-success mt-6">Submit Answers</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MockExam;
