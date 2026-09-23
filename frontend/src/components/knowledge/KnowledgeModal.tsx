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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl bg-white border border-slate-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-white">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 border border-blue-200 flex items-center justify-center">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                Marine Knowledge Base & RAG Index
                <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                  Chroma Vector DB
                </span>
              </h3>
              <p className="text-xs text-slate-500">
                Manage unstructured marine guidelines, advisories, and regulatory documents.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 overflow-y-auto space-y-4">
          {/* Status Metrics Bar */}
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Status</span>
              <span className="text-sm font-bold text-emerald-700 flex items-center justify-center gap-1 mt-0.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                {status?.total_chunks ? "Ready" : "Unindexed"}
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Indexed Documents</span>
              <span className="text-sm font-black text-slate-900 mt-0.5 block">
                {status?.total_documents || 0} Docs
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 text-center">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">Total Chunks</span>
              <span className="text-sm font-black text-blue-700 mt-0.5 block">
                {status?.total_chunks || 0} Chunks
              </span>
            </div>
          </div>

          {/* Document Upload & Ingest Box */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <Upload className="w-3.5 h-3.5 text-blue-600" /> Upload Document (.pdf, .docx, .txt)
            </h4>

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={handleFileChange}
                disabled={isUploading || isIngesting}
                className="w-full text-xs text-slate-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-slate-200 file:text-xs file:font-semibold file:bg-white file:text-slate-700 hover:file:bg-slate-100 file:cursor-pointer cursor-pointer border border-slate-200 rounded-xl p-1 bg-white"
              />
              <button
                onClick={handleUpload}
                disabled={!selectedFile || isUploading}
                className="w-full sm:w-auto px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold whitespace-nowrap transition disabled:opacity-40 disabled:cursor-not-allowed shadow-xs flex items-center justify-center gap-1.5 cursor-pointer"
              >
                {isUploading ? (
                  <>
                    <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
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
                className={`text-xs p-2.5 rounded-xl flex items-start gap-2 ${
                  message.type === "success"
                    ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                    : "bg-rose-50 text-rose-800 border border-rose-200"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5 text-emerald-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5 text-rose-600" />
                )}
                <span>{message.text}</span>
              </div>
            )}
          </div>

          {/* Document Management Table */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-blue-600" /> Indexed Knowledge Documents
              </h4>
              <button
                onClick={handleRunIngestion}
                disabled={isIngesting}
                className="text-[11px] text-blue-600 hover:text-blue-800 font-semibold flex items-center gap-1 transition cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3 h-3 ${isIngesting ? "animate-spin" : ""}`} />
                <span>Re-scan Directory</span>
              </button>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-xs">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 text-[10px] uppercase font-mono border-b border-slate-200">
                  <tr>
                    <th className="p-2.5">Document Name</th>
                    <th className="p-2.5">Type</th>
                    <th className="p-2.5">Chunks</th>
                    <th className="p-2.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {status?.documents && status.documents.length > 0 ? (
                    status.documents.map((doc, idx) => (
                      <tr key={idx} className="hover:bg-slate-50 transition">
                        <td className="p-2.5 flex items-center gap-2 font-medium">
                          <FileText className="w-3.5 h-3.5 text-blue-600 flex-shrink-0" />
                          <span className="truncate max-w-[220px] font-semibold text-slate-900">{doc.file_name}</span>
                        </td>
                        <td className="p-2.5 uppercase font-mono text-[10px] text-slate-500">
                          {doc.doc_type}
                        </td>
                        <td className="p-2.5 font-mono text-blue-700 font-bold">
                          {doc.total_chunks}
                        </td>
                        <td className="p-2.5">
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
                            Indexed
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={4} className="p-4 text-center text-slate-500 text-xs">
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
        <div className="p-3.5 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
          <span>Provider: {status?.embedding_provider || "Deterministic Local Embeddings"}</span>
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-800 font-semibold text-xs transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeModal;
