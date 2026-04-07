import { useState, useRef, useEffect } from "react";
import * as pdfjsLib from "pdfjs-dist";
import JSZip from "jszip";
import { saveAs } from "file-saver";

// Configure PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url
).toString();

interface PageImage {
  pageNum: number;
  dataUrl: string;
  blob: Blob;
  width: number;
  height: number;
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [quality, setQuality] = useState(0.82);
  const [scale, setScale] = useState(2);
  const [pages, setPages] = useState<PageImage[]>([]);
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Clean up blob URLs on unmount or when pages change
  useEffect(() => {
    return () => {
      pages.forEach((p) => URL.revokeObjectURL(p.dataUrl));
    };
  }, [pages]);

  const handleFile = (f: File) => {
    if (f.type !== "application/pdf") {
      setError("Please select a valid PDF file.");
      return;
    }
    setFile(f);
    setPages([]);
    setError(null);
    setProgress({ current: 0, total: 0 });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const convert = async () => {
    if (!file) return;
    setConverting(true);
    setError(null);

    // Clean up old blob URLs
    pages.forEach((p) => URL.revokeObjectURL(p.dataUrl));
    setPages([]);

    try {
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      const totalPages = pdf.numPages;
      setProgress({ current: 0, total: totalPages });

      const results: PageImage[] = [];

      for (let i = 1; i <= totalPages; i++) {
        const page = await pdf.getPage(i);
        const viewport = page.getViewport({ scale });

        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;

        const ctx = canvas.getContext("2d")!;
        // Fill white background (PDF pages can be transparent, JPEG is not)
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        await page.render({
          canvas,
          canvasContext: ctx,
          viewport: viewport,
        }).promise;

        const blob = await new Promise<Blob>((resolve, reject) => {
          canvas.toBlob(
            (b) => {
              if (b) resolve(b);
              else reject(new Error("Failed to create image blob"));
            },
            "image/jpeg",
            quality
          );
        });

        const dataUrl = URL.createObjectURL(blob);

        results.push({
          pageNum: i,
          dataUrl,
          blob,
          width: viewport.width,
          height: viewport.height,
        });

        setProgress({ current: i, total: totalPages });
      }

      setPages(results);
    } catch (err) {
      setError(
        `Conversion failed: ${err instanceof Error ? err.message : "Unknown error"}`
      );
    } finally {
      setConverting(false);
    }
  };

  const downloadPage = (page: PageImage) => {
    const baseName = file?.name?.replace(/\.pdf$/i, "") || "page";
    saveAs(page.blob, `${baseName}_page${page.pageNum}.jpg`);
  };

  const downloadAllAsZip = async () => {
    if (pages.length === 0) return;

    const zip = new JSZip();
    const baseName = file?.name?.replace(/\.pdf$/i, "") || "page";

    pages.forEach((page) => {
      zip.file(`${baseName}_page${page.pageNum}.jpg`, page.blob);
    });

    const zipBlob = await zip.generateAsync({ type: "blob" });
    saveAs(zipBlob, `${baseName}_images.zip`);
  };

  const reset = () => {
    pages.forEach((p) => URL.revokeObjectURL(p.dataUrl));
    setFile(null);
    setPages([]);
    setError(null);
    setProgress({ current: 0, total: 0 });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const qualityLabel = (q: number): string => {
    if (q >= 0.95) return "Maximum";
    if (q >= 0.85) return "High";
    if (q >= 0.7) return "Medium-High";
    if (q >= 0.5) return "Medium";
    return "Low";
  };

  const scaleLabel = (s: number): string => {
    const dpi = Math.round(s * 72);
    return `${dpi} DPI`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-sm">
        <div className="mx-auto max-w-5xl px-6 py-4 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 shadow-lg shadow-orange-500/20">
            <svg
              className="h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              PDF to JPEG Converter
            </h1>
            <p className="text-xs text-slate-400">
              Convert your PDF pages to optimized JPEG images
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8 space-y-8">
        {/* Upload Area */}
        {!file && (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
              dragOver
                ? "border-orange-400 bg-orange-500/10 scale-[1.02]"
                : "border-slate-600 bg-slate-800/50 hover:border-slate-500 hover:bg-slate-800"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleInputChange}
              className="hidden"
            />
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-slate-700/50">
              <svg
                className={`h-8 w-8 transition-colors ${dragOver ? "text-orange-400" : "text-slate-400"}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 16v-8m0 0l-3 3m3-3l3 3M2 12c0 5.523 4.477 10 10 10s10-4.477 10-10S17.523 2 12 2 2 6.477 2 12z"
                />
              </svg>
            </div>
            <p className="text-lg font-medium text-slate-200">
              {dragOver
                ? "Drop your PDF here"
                : "Drop a PDF file here or click to browse"}
            </p>
            <p className="mt-2 text-sm text-slate-400">
              Supports any PDF file • Processed entirely in your browser
            </p>
          </div>
        )}

        {/* File Info + Settings */}
        {file && (
          <div className="rounded-2xl bg-slate-800/80 border border-slate-700/50 overflow-hidden">
            {/* File Info Bar */}
            <div className="flex items-center justify-between px-6 py-4 bg-slate-800 border-b border-slate-700/50">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-red-500/20">
                  <svg
                    className="h-5 w-5 text-red-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-slate-100 truncate">
                    {file.name}
                  </p>
                  <p className="text-xs text-slate-400">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={reset}
                className="shrink-0 rounded-lg px-3 py-1.5 text-sm text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
              >
                Change file
              </button>
            </div>

            {/* Settings */}
            <div className="px-6 py-5 space-y-5">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {/* Quality Slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-slate-300">
                      JPEG Quality
                    </label>
                    <span className="text-sm font-mono text-orange-400">
                      {qualityLabel(quality)} ({Math.round(quality * 100)}%)
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0.1}
                    max={1}
                    step={0.01}
                    value={quality}
                    onChange={(e) => setQuality(parseFloat(e.target.value))}
                    disabled={converting}
                    className="w-full accent-orange-500"
                  />
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>Smaller file</span>
                    <span>Better quality</span>
                  </div>
                </div>

                {/* Scale Slider */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-slate-300">
                      Resolution
                    </label>
                    <span className="text-sm font-mono text-orange-400">
                      {scaleLabel(scale)} ({scale}x)
                    </span>
                  </div>
                  <input
                    type="range"
                    min={1}
                    max={4}
                    step={0.5}
                    value={scale}
                    onChange={(e) => setScale(parseFloat(e.target.value))}
                    disabled={converting}
                    className="w-full accent-orange-500"
                  />
                  <div className="flex justify-between text-xs text-slate-500 mt-1">
                    <span>Faster</span>
                    <span>More detail</span>
                  </div>
                </div>
              </div>

              {/* Convert Button */}
              <button
                onClick={convert}
                disabled={converting}
                className={`w-full rounded-xl py-3 px-6 font-semibold text-white transition-all duration-200 ${
                  converting
                    ? "bg-slate-600 cursor-not-allowed"
                    : "bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 shadow-lg shadow-orange-500/25 hover:shadow-orange-500/40 active:scale-[0.98]"
                }`}
              >
                {converting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="h-5 w-5 animate-spin"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                      />
                    </svg>
                    Converting... {progress.current}/{progress.total} pages
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <svg
                      className="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                      />
                    </svg>
                    Convert to JPEG
                  </span>
                )}
              </button>

              {/* Progress Bar */}
              {converting && progress.total > 0 && (
                <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-orange-500 to-amber-400 h-full rounded-full transition-all duration-300"
                    style={{
                      width: `${(progress.current / progress.total) * 100}%`,
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-6 py-4 text-red-300 flex items-start gap-3">
            <svg
              className="h-5 w-5 shrink-0 mt-0.5 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
            <div>
              <p className="font-medium">Conversion Error</p>
              <p className="text-sm text-red-400 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {pages.length > 0 && (
          <div className="space-y-4">
            {/* Results Header */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-100">
                  Converted Images
                </h2>
                <p className="text-sm text-slate-400">
                  {pages.length} page{pages.length !== 1 ? "s" : ""} converted
                  to JPEG
                </p>
              </div>
              <button
                onClick={downloadAllAsZip}
                className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-sm font-medium text-white transition-colors shadow-lg shadow-emerald-600/20"
              >
                <svg
                  className="h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                Download All (ZIP)
              </button>
            </div>

            {/* Page Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {pages.map((page) => (
                <div
                  key={page.pageNum}
                  className="group rounded-xl bg-slate-800/80 border border-slate-700/50 overflow-hidden hover:border-slate-600 transition-colors"
                >
                  {/* Preview */}
                  <div className="relative aspect-[8.5/11] bg-slate-900 overflow-hidden">
                    <img
                      src={page.dataUrl}
                      alt={`Page ${page.pageNum}`}
                      className="w-full h-full object-contain"
                    />
                    {/* Hover overlay */}
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                      <button
                        onClick={() => downloadPage(page)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity bg-white text-slate-900 rounded-lg px-4 py-2 text-sm font-medium hover:bg-slate-100 flex items-center gap-2"
                      >
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth={2}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                          />
                        </svg>
                        Download
                      </button>
                    </div>
                  </div>
                  {/* Info */}
                  <div className="px-4 py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-200">
                        Page {page.pageNum}
                      </p>
                      <p className="text-xs text-slate-400">
                        {page.width} × {page.height}px •{" "}
                        {formatFileSize(page.blob.size)}
                      </p>
                    </div>
                    <button
                      onClick={() => downloadPage(page)}
                      className="rounded-lg p-2 text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
                      title="Download"
                    >
                      <svg
                        className="h-4 w-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        strokeWidth={2}
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-700/50 py-6">
        <p className="text-center text-xs text-slate-500">
          All processing happens in your browser. No files are uploaded to any
          server.
        </p>
      </footer>
    </div>
  );
}
