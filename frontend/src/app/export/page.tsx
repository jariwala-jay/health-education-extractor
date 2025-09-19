"use client";

import { useState, useEffect } from "react";
import { ArrowDownTrayIcon } from "@heroicons/react/24/outline";
import {
  uploadArticlesToAppDatabase,
  uploadTipsToAppDatabase,
  getExportSummary,
  getCombinedExportSummary,
  listPDFs,
  type ExportSummary,
  type CombinedExportSummary,
  type PDFDocument,
  type UploadResult,
  type TipsUploadResult,
} from "@/lib/api";
import { HEALTH_CATEGORIES } from "@/lib/constants";
import toast from "react-hot-toast";

const TIP_CATEGORIES = [
  "Hypertension",
  "Obesity", 
  "Diabetes",
  "Prediabetes",
  "Nutrition",
  "General"
];

export default function ExportPage() {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<CombinedExportSummary | null>(null);
  const [pdfs, setPdfs] = useState<PDFDocument[]>([]);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [tipsUploadResult, setTipsUploadResult] = useState<TipsUploadResult | null>(null);

  // Upload filters
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTipCategories, setSelectedTipCategories] = useState<string[]>([]);
  const [selectedPdfId, setSelectedPdfId] = useState<string>("");
  const [exportType, setExportType] = useState<"articles" | "tips" | "both">("both");

  useEffect(() => {
    loadSummary();
    loadPDFs();
  }, [selectedPdfId]); // Reload summary when PDF filter changes

  const loadPDFs = async () => {
    try {
      const pdfData = await listPDFs(1, 100); // Get up to 100 PDFs
      setPdfs(pdfData.documents);
    } catch (error) {
      console.error("Error loading PDFs:", error);
      toast.error("Failed to load PDFs");
    }
  };

  const loadSummary = async () => {
    try {
      const summaryData = await getCombinedExportSummary(selectedPdfId || undefined);
      setSummary(summaryData);
    } catch (error) {
      console.error("Error loading summary:", error);
      toast.error("Failed to load export summary");
    }
  };

  const handleUpload = async () => {
    try {
      setLoading(true);
      setUploadResult(null);
      setTipsUploadResult(null);

      const pdfFilter = selectedPdfId || undefined;
      let articlesResult: UploadResult | null = null;
      let tipsResult: TipsUploadResult | null = null;

      // Upload articles if selected
      if (exportType === "articles" || exportType === "both") {
        const categoryFilter = selectedCategories.length > 0 ? selectedCategories[0] : undefined;
        articlesResult = await uploadArticlesToAppDatabase(
          categoryFilter,
          undefined, // tags - not implemented in UI yet
          pdfFilter
        );
        setUploadResult(articlesResult);
      }

      // Upload tips if selected
      if (exportType === "tips" || exportType === "both") {
        const tipCategoryFilter = selectedTipCategories.length > 0 ? selectedTipCategories[0] : undefined;
        tipsResult = await uploadTipsToAppDatabase(
          tipCategoryFilter,
          undefined, // tags - not implemented in UI yet
          pdfFilter
        );
        setTipsUploadResult(tipsResult);
      }

      // Show success messages
      if (articlesResult && articlesResult.uploaded_articles > 0) {
        toast.success(
          `Successfully uploaded ${articlesResult.uploaded_articles} articles to app database`
        );
      }
      
      if (tipsResult && tipsResult.uploaded_tips > 0) {
        toast.success(
          `Successfully uploaded ${tipsResult.uploaded_tips} tips to app database`
        );
      }

      if ((!articlesResult || articlesResult.uploaded_articles === 0) && 
          (!tipsResult || tipsResult.uploaded_tips === 0)) {
        toast("No items to upload");
      }

      // Refresh summary to show updated counts
      await loadSummary();
    } catch (error) {
      console.error("Error uploading items:", error);
      toast.error("Failed to upload items to app database");
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryToggle = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  const handleTipCategoryToggle = (category: string) => {
    setSelectedTipCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:tracking-tight">
          Upload to App Database
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Upload approved health education articles and daily tips directly to the app database
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Configuration */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Upload Configuration
              </h3>

              <div className="space-y-6">
                {/* Export Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Export Type
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: "both", label: "Both Articles & Tips" },
                      { value: "articles", label: "Articles Only" },
                      { value: "tips", label: "Tips Only" }
                    ].map((option) => (
                      <label key={option.value} className="inline-flex items-center">
                        <input
                          type="radio"
                          name="exportType"
                          value={option.value}
                          checked={exportType === option.value}
                          onChange={(e) => setExportType(e.target.value as "articles" | "tips" | "both")}
                          className="form-radio h-4 w-4 text-indigo-600"
                        />
                        <span className="ml-2 text-sm">{option.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Info about what gets uploaded */}
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                  <div className="flex">
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-blue-800">
                        Upload Information
                      </h3>
                      <div className="mt-2 text-sm text-blue-700">
                        <p>
                          Only approved {exportType === "both" ? "articles and tips" : exportType === "articles" ? "articles" : "tips"} that haven&apos;t been uploaded
                          yet will be processed.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Article Category Filter */}
                {(exportType === "articles" || exportType === "both") && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Article Categories (optional)
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {HEALTH_CATEGORIES.map((category) => (
                        <label
                          key={category}
                          className="inline-flex items-center"
                        >
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(category)}
                            onChange={() => handleCategoryToggle(category)}
                            className="form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out"
                          />
                          <span className="ml-2 text-sm">{category}</span>
                        </label>
                      ))}
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      Leave unchecked to include all article categories
                    </p>
                  </div>
                )}

                {/* Tip Category Filter */}
                {(exportType === "tips" || exportType === "both") && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Tip Categories (optional)
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {TIP_CATEGORIES.map((category) => (
                        <label
                          key={category}
                          className="inline-flex items-center"
                        >
                          <input
                            type="checkbox"
                            checked={selectedTipCategories.includes(category)}
                            onChange={() => handleTipCategoryToggle(category)}
                            className="form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out"
                          />
                          <span className="ml-2 text-sm">{category}</span>
                        </label>
                      ))}
                    </div>
                    <p className="mt-1 text-xs text-gray-500">
                      Leave unchecked to include all tip categories
                    </p>
                  </div>
                )}

                {/* PDF Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    PDF (optional)
                  </label>
                  <select
                    value={selectedPdfId}
                    onChange={(e) => setSelectedPdfId(e.target.value)}
                    className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="">All PDFs</option>
                    {pdfs.map((pdf) => (
                      <option key={pdf.id} value={pdf.id}>
                        {pdf.filename}
                      </option>
                    ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">
                    Select a PDF to filter articles by its content
                  </p>
                </div>

                {/* Upload Button */}
                <div className="pt-4 border-t border-gray-200">
                  <button
                    onClick={handleUpload}
                    disabled={loading}
                    className="w-full inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
                    {loading ? "Uploading..." : `Upload ${exportType === "both" ? "Articles & Tips" : exportType === "articles" ? "Articles" : "Tips"} to App Database`}
                  </button>
                </div>

                {/* Upload Results */}
                {(uploadResult || tipsUploadResult) && (
                  <div className="mt-6 space-y-4">
                    {uploadResult && (
                      <div className="p-4 bg-gray-50 rounded-md">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Articles Upload Result:
                        </h4>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>
                            • Total articles processed:{" "}
                            {uploadResult.total_articles}
                          </p>
                          <p>
                            • Successfully uploaded:{" "}
                            {uploadResult.uploaded_articles}
                          </p>
                          <p>• Failed: {uploadResult.failed_articles}</p>
                          {uploadResult.failed_details &&
                            uploadResult.failed_details.length > 0 && (
                              <div className="mt-2">
                                <p className="font-medium">Failed articles:</p>
                                {uploadResult.failed_details.map(
                                  (failed, index) => (
                                    <p key={index} className="ml-2 text-red-600">
                                      • {failed.title}: {failed.reason}
                                    </p>
                                  )
                                )}
                              </div>
                            )}
                        </div>
                      </div>
                    )}

                    {tipsUploadResult && (
                      <div className="p-4 bg-gray-50 rounded-md">
                        <h4 className="text-sm font-medium text-gray-900 mb-2">
                          Tips Upload Result:
                        </h4>
                        <div className="text-sm text-gray-600 space-y-1">
                          <p>
                            • Total tips processed:{" "}
                            {tipsUploadResult.total_tips}
                          </p>
                          <p>
                            • Successfully uploaded:{" "}
                            {tipsUploadResult.uploaded_tips}
                          </p>
                          <p>• Failed: {tipsUploadResult.failed_tips}</p>
                          {tipsUploadResult.failed_details &&
                            tipsUploadResult.failed_details.length > 0 && (
                              <div className="mt-2">
                                <p className="font-medium">Failed tips:</p>
                                {tipsUploadResult.failed_details.map(
                                  (failed, index) => (
                                    <p key={index} className="ml-2 text-red-600">
                                      • {failed.tip_text}: {failed.reason}
                                    </p>
                                  )
                                )}
                              </div>
                            )}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Upload Summary */}
        <div>
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Upload Summary
                </h3>
                <button
                  onClick={loadSummary}
                  className="text-sm text-indigo-600 hover:text-indigo-500"
                >
                  Refresh
                </button>
              </div>

              {summary ? (
                <div className="space-y-4">
                  {/* Combined Summary */}
                  <div className="bg-gray-50 p-3 rounded-md">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Combined</h4>
                    <div className="space-y-1">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Total Items:</span>
                        <span className="text-sm font-medium">{summary.combined.total_items}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-500">Ready to Upload:</span>
                        <span className="text-sm font-medium text-blue-600">{summary.combined.ready_to_upload}</span>
                      </div>
                    </div>
                  </div>

                  {/* Articles Summary */}
                  {(exportType === "articles" || exportType === "both") && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Articles</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Total:</span>
                          <span className="text-sm font-medium">{summary.articles.total}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Ready:</span>
                          <span className="text-sm font-medium text-blue-600">{summary.articles.ready_to_upload}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Uploaded:</span>
                          <span className="text-sm font-medium text-green-600">{summary.articles.status_breakdown.uploaded || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Approved:</span>
                          <span className="text-sm font-medium text-yellow-600">{summary.articles.status_breakdown.approved || 0}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Tips Summary */}
                  {(exportType === "tips" || exportType === "both") && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 mb-2">Tips</h4>
                      <div className="space-y-1">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Total:</span>
                          <span className="text-sm font-medium">{summary.tips.total}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Ready:</span>
                          <span className="text-sm font-medium text-blue-600">{summary.tips.ready_to_upload}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Uploaded:</span>
                          <span className="text-sm font-medium text-green-600">{summary.tips.status_breakdown.uploaded || 0}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">Approved:</span>
                          <span className="text-sm font-medium text-yellow-600">{summary.tips.status_breakdown.approved || 0}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-4">
                  <button
                    onClick={loadSummary}
                    className="text-sm text-indigo-600 hover:text-indigo-500"
                  >
                    Load Summary
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
