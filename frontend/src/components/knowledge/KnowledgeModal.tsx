"use client";

import React, { useState, useRef } from "react";
import { X, Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, Database, BookOpen } from "lucide-react";
import { RagStatus } from "@/types/marine";
import { uploadDocument, triggerIngestion, fetchRagStatus } from "@/services/api";

interface KnowledgeModalProps {
  isOpen: boolean;
  onClose: () => void;
  status: RagStatus | null;
  onStatusUpdate: (newStatus: RagStatus) => void;
}

export const KnowledgeModal: React.FC<KnowledgeModalProps> = ({
  isOpen,
  onClose,
  status,
  onStatusUpdate,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isIngesting, setIsIngesting] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setMessage(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setMessage(null);

    try {
      const res = await uploadDocument(selectedFile);
      setMessage({
        type: "success",
        text: `Uploaded "${selectedFile.name}" successfully! Ingestion indexed ${res.ingestion?.chunks_indexed || 0} chunks.`,
      });
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";

      // Refresh status
      const updatedStatus = await fetchRagStatus();
      onStatusUpdate(updatedStatus);
    } catch (err: any) {
      setMessage({
        type: "error",
        text: err.message || "Failed to upload document. Please check file format.",
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleRunIngestion = async () => {
    setIsIngesting(true);
    setMessage(null);

    try {
      const res = await triggerIngestion();
      setMessage({
        type: "success",
        text: `Ingestion scan complete: ${res.documents_processed} docs loaded, ${res.chunks_indexed} new chunks added, ${res.chunks_skipped} duplicates skipped.`,
      });
      const updatedStatus = await fetchRagStatus();
      onStatusUpdate(updatedStatus);
    } catch (err: any) {
      setMessage({
        type: "error",
        text: err.message || "Ingestion failed.",
      });
    } finally {
      setIsIngesting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-marine-900 border border-cyan-500/30 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700/60 bg-marine-850">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                Marine Knowledge Base & RAG Index
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  Chroma Vector DB
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                Manage unstructured marine guidelines, advisories, and regulatory documents.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 overflow-y-auto space-y-4">
          {/* Status Metrics Bar */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-marine-850 border border-slate-700/60 rounded-lg p-3 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Status</span>
              <span className="text-sm font-bold text-emerald-400 flex items-center justify-center gap-1 mt-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                {status?.total_chunks ? "Ready" : "Unindexed"}
              </span>
            </div>
            <div className="bg-marine-850 border border-slate-700/60 rounded-lg p-3 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Indexed Documents</span>
              <span className="text-sm font-extrabold text-white mt-0.5 block">
                {status?.total_documents || 0} Docs
              </span>
            </div>
            <div className="bg-marine-850 border border-slate-700/60 rounded-lg p-3 text-center">
              <span className="text-[10px] uppercase font-semibold text-slate-400 block">Total Chunks</span>
              <span className="text-sm font-extrabold text-cyan-300 mt-0.5 block">
                {status?.total_chunks || 0} Chunks
              </span>
            </div>
          </div>

          {/* Document Upload & Ingest Box */}
          <div className="bg-marine-850/80 border border-slate-700/60 rounded-lg p-4 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5 text-cyan-400" /> Upload Document (.pdf, .docx, .txt)
            </h4>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleFileChange}
                disabled={isUploading || isIngesting}
                className="w-full text-xs text-slate-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-cyan-500/20 file:text-cyan-300 hover:file:bg-cyan-500/30 file:cursor-pointer cursor-pointer border border-slate-700/60 rounded-lg p-1 bg-marine-900"
              />
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="w-full sm:w-auto px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-marine-950 text-xs font-bold whitespace-nowrap transition disabled:opacity-40 disabled:cursor-not-allowed shadow-marine-cyan flex items-center justify-center gap-1.5"
              >
                {isUploading ? (
                  <>
                    <div className="w-3 h-3 border-2 border-marine-950 border-t-transparent rounded-full animate-spin"></div>
                    Indexing...
                  </>
                ) : (
                  <>
                    <Upload className="w-3.5 h-3.5" /> Upload & Ingest
                  </>
                )}
              </button>
            </div>

            {/* Notification message */}
            {message && (
              <div
                className={`text-xs p-2.5 rounded-lg flex items-start gap-2 ${
                  message.type === "success"
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                    : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                )}
                <span>{message.text}</span>
              </div>
            )}
          </div>

          {/* Document Management Table */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-blue-400" /> Indexed Knowledge Documents
              </h4>
              <button
                onClick={handleRunIngestion}
                disabled={isIngesting}
                className="text-[11px] text-cyan-300 hover:text-cyan-200 flex items-center gap-1 hover:underline disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 ${isIngesting ? "animate-spin" : ""}`} />
                <span>Re-scan Directory</span>
              </button>
            </div>

            <div className="border border-slate-700/60 rounded-lg overflow-hidden bg-marine-850/60">
              <table className="w-full text-left text-xs">
                <thead className="bg-marine-800 text-slate-400 text-[10px] uppercase font-mono">
                  <tr>
                    <th className="p-2.5">Document Name</th>
                    <th className="p-2.5">Type</th>
                    <th className="p-2.5">Chunks</th>
                    <th className="p-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/40 text-slate-200">
                  {status?.documents && status.documents.length > 0 ? (
                    status.documents.map((doc, idx) => (
                      <tr key={idx} className="hover:bg-marine-800/40 transition">
                        <td className="p-2.5 flex items-center gap-2 font-medium">
                          <FileText className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
                          <span className="truncate max-w-[220px]">{doc.file_name}</span>
                        </td>
                        <td className="p-2.5 uppercase font-mono text-[10px] text-slate-400">
                          {doc.doc_type}
                        </td>
                        <td className="p-2.5 font-mono text-cyan-300">
                          {doc.total_chunks}
                        </td>
                        <td className="p-2.5">
                          <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold">
                            Indexed
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="p-4 text-center text-slate-400 text-xs">
                        No documents currently indexed. Click "Re-scan Directory" or upload a file.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-3 bg-marine-850 border-t border-slate-700/60 flex items-center justify-between text-[11px] text-slate-400">
          <span>Provider: {status?.embedding_provider || "Deterministic Local Embeddings"}</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
export default KnowledgeModal;
