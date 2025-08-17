import React, { useEffect, useRef, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import 'pdfjs-dist/web/pdf_viewer.css';

// IMPORTANT: pdfjs-dist 5.x bundles an ESM worker at build/pdf.worker.mjs
// Vite can inline a worker script via ?worker, but for portability we fall back to using url string.
// We try multiple patterns for robustness. Adjust if your bundler complains.
let workerSrcCandidate;
try {
  // eslint-disable-next-line import/no-unresolved
  workerSrcCandidate = new URL('pdfjs-dist/build/pdf.worker.min.mjs', import.meta.url).toString();
} catch (e) {
  try {
    workerSrcCandidate = new URL('pdfjs-dist/build/pdf.worker.mjs', import.meta.url).toString();
  } catch (e2) {
    workerSrcCandidate = null;
  }
}
if (workerSrcCandidate) {
  // @ts-ignore
  pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrcCandidate;
}

/**
 * PDFWithAI
 * Renders a single page of a PDF and allows sending the visible text to the backend LLM endpoint.
 * Props:
 *  - url: string (PDF URL)
 */
export default function PDFWithAI({ url }) {
  const canvasRef = useRef(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [numPages, setNumPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiAnswer, setAiAnswer] = useState('');
  const [error, setError] = useState('');
  const [scale, setScale] = useState(1.0);
  const [viewerHeight, setViewerHeight] = useState(null); // CSS pixel height of rendered PDF page

  // Load + render page
  useEffect(() => {
    let cancelled = false;
    if (!url) return;
    setLoading(true);
    setError('');

    (async () => {
      try {
        const loadingTask = pdfjsLib.getDocument({ url });
        const pdf = await loadingTask.promise;
        if (cancelled) return;
        setNumPages(pdf.numPages);
        const page = await pdf.getPage(pageNumber);
        if (cancelled) return;
        const viewport = page.getViewport({ scale });
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const renderTask = page.render({ canvasContext: ctx, viewport });
        await renderTask.promise;
        // Measure displayed (CSS) height after render (accounts for scaling via style)
        if (canvas) {
          const rect = canvas.getBoundingClientRect();
            setViewerHeight(rect.height);
        }
      } catch (e) {
        if (!cancelled) setError('Failed to load PDF');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [url, pageNumber, scale]);

  async function extractVisibleText() {
    setExtracting(true);
    setError('');
    try {
      const loadingTask = pdfjsLib.getDocument({ url });
      const pdf = await loadingTask.promise;
      const page = await pdf.getPage(pageNumber);
      const textContent = await page.getTextContent();
      const text = textContent.items.map(i => i.str).join('\n');
      return text;
    } catch (e) {
      setError('Failed to extract text');
      return '';
    } finally {
      setExtracting(false);
    }
  }

  async function handleAskAI() {
    setAiLoading(true);
    setAiAnswer('');
    setError('');
    try {
      const text = await extractVisibleText();
      if (!text) {
        setError('No text extracted to send');
        return;
      }
      // Capture canvas screenshot (PNG) - always included
      let image_base64 = null;
      if (canvasRef.current) {
        try {
          const canvas = canvasRef.current;
          let srcCanvas = canvas;
          // Downscale if very large (>1600px width) to reduce payload size
          if (canvas.width > 1600) {
            const ratio = 1600 / canvas.width;
            const off = document.createElement('canvas');
            off.width = 1600;
            off.height = Math.round(canvas.height * ratio);
            const octx = off.getContext('2d');
            octx.drawImage(canvas, 0, 0, off.width, off.height);
            srcCanvas = off;
          }
            const dataUrl = srcCanvas.toDataURL('image/png');
            image_base64 = dataUrl.split(',')[1]; // strip header
        } catch (e) {
          // Non-fatal; we can still send text
          console.warn('Failed to capture canvas image', e);
        }
      }

      const body = { text, page_number: pageNumber };
      if (image_base64) body.image_base64 = image_base64;

      const res = await fetch('http://localhost:8000/api/v1/ai/solve-paper', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || 'AI request failed');
      }
      const data = await res.json();
      setAiAnswer(data.answer || 'No answer');
    } catch (e) {
      setError(e.message || 'Failed sending to AI');
    } finally {
      setAiLoading(false);
    }
  }

  const disablePrev = pageNumber <= 1 || loading;
  const disableNext = pageNumber >= numPages || loading;

  return (
    <div className="flex w-full h-full bg-gray-100 dark:bg-gray-900">
      {/* Main Container */}
      <div className="flex flex-row gap-4 w-full h-full">
        {/* PDF Viewer Section */}
        <div className="flex flex-col flex-grow min-w-0">
          {/* Controls */}
          <div className="flex items-center justify-between gap-4 mb-2 p-3 bg-white dark:bg-gray-800 rounded-lg shadow-sm">
            <div className="flex items-center gap-3">
              <button className="btn btn-primary btn-sm" disabled={disablePrev} onClick={() => setPageNumber(p => Math.max(1, p - 1))}>
                Previous
              </button>
              <span className="text-sm font-medium">Page {pageNumber}{numPages ? ` of ${numPages}` : ''}</span>
              <button className="btn btn-primary btn-sm" disabled={disableNext} onClick={() => setPageNumber(p => Math.min(numPages, p + 1))}>
                Next
              </button>
            </div>
            <div className="flex items-center gap-2 bg-gray-50 dark:bg-gray-700 px-3 py-1 rounded-md">
              <button className="btn btn-circle btn-sm btn-ghost" onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>-</button>
              <span className="text-sm font-medium min-w-[3rem] text-center">{(scale*100).toFixed(0)}%</span>
              <button className="btn btn-circle btn-sm btn-ghost" onClick={() => setScale(s => Math.min(2.0, s + 0.1))}>+</button>
            </div>
          </div>
          {/* PDF Viewer */}
          <div className="flex-1 relative bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-auto">
            <div className="absolute inset-0 flex items-start justify-center p-4">
              {loading && <div className="p-10 text-lg">Loading PDF...</div>}
              {error && !loading && <div className="p-4 text-red-500">{error}</div>}
              <canvas 
                ref={canvasRef} 
                className="max-w-full"
                style={{ 
                  display: loading ? 'none' : 'block',
                  margin: '0 auto',
                  height: 'auto'
                }} 
              />
            </div>
          </div>
        </div>

        {/* AI Assistant Panel */}
        <div className="w-[380px] flex flex-col bg-white dark:bg-gray-800 rounded-lg shadow-lg">
          <div className="p-3 border-b border-gray-200 dark:border-gray-700">
            <button 
              className="btn btn-primary w-full h-10 text-base font-medium" 
              onClick={handleAskAI} 
              disabled={aiLoading || extracting || loading}
            >
              {aiLoading ? (
                <span className="flex items-center gap-2">
                  <span className="loading loading-spinner loading-sm"></span>
                  Thinking...
                </span>
              ) : 'Ask AI Assistant'}
            </button>
          </div>
          <div className="flex-1 p-4 overflow-y-auto">
            {aiLoading ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <span className="loading loading-bars loading-lg mb-4"></span>
                <div className="text-gray-600 dark:text-gray-300">
                  <p className="text-lg mb-2">Analyzing the content...</p>
                  <p className="text-sm opacity-75">Have you tried solving it yourself? 🤔</p>
                </div>
              </div>
            ) : (
              <div className="prose dark:prose-invert max-w-none">
                {aiAnswer || (
                  <div className="text-gray-500 dark:text-gray-400">
                    <p className="text-lg">Welcome to AI Assistant! 👋</p>
                    <p>Click the button above to get help understanding this page.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
