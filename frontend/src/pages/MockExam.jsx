import React, { useState, useEffect } from "react";

import { useParams } from "react-router-dom";
import { getPapers, listPastPapers, getPastPaperPdfUrl } from "../api";

const MockExam = () => {
  const { courseId } = useParams();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [pastPapers, setPastPapers] = useState([]);
  const [pdfView, setPdfView] = useState(null);

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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-10 px-4">
      <div className="max-w-2xl mx-auto bg-white dark:bg-gray-800 rounded-xl shadow p-8">
        <h1 className="text-2xl font-bold mb-4">Mock Exam for {courseId}</h1>
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-2">Past Papers</h2>
          <button
            className="btn btn-secondary mb-3"
            onClick={fetchPapers}
            disabled={downloading}
          >
            {downloading ? "Downloading..." : "Get Past Papers"}
          </button>
          {error && <div className="text-red-500 mb-2">{error}</div>}
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
        {pdfView && (
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold">Viewing: {pdfView}</span>
              <button
                className="btn btn-xs btn-error"
                onClick={() => setPdfView(null)}
              >
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
      </div>
    </div>
  );
};

export default MockExam;
