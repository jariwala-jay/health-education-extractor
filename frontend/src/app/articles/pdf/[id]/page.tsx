"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { formatDistanceToNow } from "date-fns";
import {
  ChevronLeftIcon,
  EyeIcon,
  PencilIcon,
  CheckIcon,
  XMarkIcon,
  DocumentTextIcon,
  ArrowDownTrayIcon,
} from "@heroicons/react/24/outline";
import {
  getArticlesByPdf,
  getPDFStatus,
  approveArticle,
  rejectArticle,
  type HealthArticle,
  type PDFDocument,
} from "@/lib/api";
import { getCategoryColor, getStatusColor } from "@/lib/constants";
import toast from "react-hot-toast";
import { parseUTCTimestamp } from "@/lib/utils";

export default function PDFArticlesPage() {
  const params = useParams();
  const router = useRouter();
  const pdfId = params.id as string;

  const [articles, setArticles] = useState<HealthArticle[]>([]);
  const [pdf, setPdf] = useState<PDFDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [processingActions, setProcessingActions] = useState<Set<string>>(
    new Set()
  );
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    if (pdfId) {
      loadPDFInfo();
      loadArticles();
    }
  }, [pdfId, page]);

  const loadPDFInfo = async () => {
    try {
      const pdfData = await getPDFStatus(pdfId);
      setPdf(pdfData);
    } catch (error) {
      console.error("Error loading PDF info:", error);
      toast.error("Failed to load PDF information");
    }
  };

  const loadArticles = async () => {
    try {
      setLoading(true);
      const data = await getArticlesByPdf(pdfId, page, 20);
      setArticles(data.articles);
      setTotalPages(data.pagination.pages);
    } catch (error) {
      console.error("Error loading articles:", error);
      toast.error("Failed to load articles");
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (articleId: string) => {
    if (processingActions.has(articleId)) return;

    try {
      setProcessingActions((prev) => new Set(prev).add(articleId));
      await approveArticle(articleId);

      // Update local state
      setArticles((prev) =>
        prev.map((article) =>
          article.id === articleId
            ? { ...article, processing_status: "approved" }
            : article
        )
      );

      toast.success("Article approved");
    } catch (error) {
      console.error("Error approving article:", error);
      toast.error("Failed to approve article");
    } finally {
      setProcessingActions((prev) => {
        const newSet = new Set(prev);
        newSet.delete(articleId);
        return newSet;
      });
    }
  };

  const handleReject = async (articleId: string) => {
    if (processingActions.has(articleId)) return;

    try {
      setProcessingActions((prev) => new Set(prev).add(articleId));
      await rejectArticle(articleId);

      // Update local state
      setArticles((prev) =>
        prev.map((article) =>
          article.id === articleId
            ? { ...article, processing_status: "rejected" }
            : article
        )
      );

      toast.success("Article rejected");
    } catch (error) {
      console.error("Error rejecting article:", error);
      toast.error("Failed to reject article");
    } finally {
      setProcessingActions((prev) => {
        const newSet = new Set(prev);
        newSet.delete(articleId);
        return newSet;
      });
    }
  };

  // Export functionality removed - articles are now uploaded directly to app database

  if (loading && articles.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-900"
          >
            <ChevronLeftIcon className="h-5 w-5 mr-1" />
            Back
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Articles from PDF
            </h1>
            {pdf && (
              <p className="text-gray-600">
                {pdf.filename} • {articles.length} articles
              </p>
            )}
          </div>
        </div>

        {/* Export button removed - articles are now uploaded directly to app database when approved */}
      </div>

      {/* PDF Info */}
      {pdf && (
        <div className="bg-white shadow rounded-lg p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-3">
              <DocumentTextIcon className="h-8 w-8 text-gray-400" />
              <div>
                <h3 className="text-lg font-medium text-gray-900">
                  {pdf.filename}
                </h3>
                <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                  <span>
                    Uploaded{" "}
                    {formatDistanceToNow(new Date(pdf.uploaded_at), {
                      addSuffix: true,
                    })}
                  </span>
                  {pdf.total_pages && <span>• {pdf.total_pages} pages</span>}
                  {pdf.total_chunks && <span>• {pdf.total_chunks} chunks</span>}
                </div>
              </div>
            </div>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                pdf.processing_status
              )}`}
            >
              {pdf.processing_status}
            </span>
          </div>
        </div>
      )}

      {/* Articles Grid */}
      {articles.length === 0 ? (
        <div className="text-center py-12">
          <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No articles found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            This PDF hasn&apos;t generated any articles yet.
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <div
              key={article.id}
              className="bg-white overflow-hidden shadow rounded-lg"
            >
              {article.image_url && (
                <div className="h-48 bg-gray-200">
                  <img
                    src={article.image_url}
                    alt={article.title}
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              <div className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getCategoryColor(
                      article.category
                    )}`}
                  >
                    {article.category}
                  </span>
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
                      article.processing_status
                    )}`}
                  >
                    {article.processing_status}
                  </span>
                </div>

                <h3 className="text-lg font-medium text-gray-900 mb-2 line-clamp-2">
                  {article.title}
                </h3>

                <p className="text-sm text-gray-600 mb-4 line-clamp-3">
                  {article.content}
                </p>

                <div className="flex items-center justify-between text-xs text-gray-500 mb-4">
                  <span>
                    {article.created_at &&
                      formatDistanceToNow(
                        parseUTCTimestamp(article.created_at),
                        { addSuffix: true }
                      )}
                  </span>
                  {article.reading_level_score && (
                    <span>Grade {article.reading_level_score.toFixed(1)}</span>
                  )}
                </div>

                {article.medical_condition_tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {article.medical_condition_tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {tag}
                      </span>
                    ))}
                    {article.medical_condition_tags.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{article.medical_condition_tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between">
                  <div className="flex space-x-2">
                    <Link
                      href={`/articles/${article.id}`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <EyeIcon className="h-3 w-3 mr-1" />
                      View
                    </Link>
                    <Link
                      href={`/articles/${article.id}/edit`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                    >
                      <PencilIcon className="h-3 w-3 mr-1" />
                      Edit
                    </Link>
                  </div>

                  {article.processing_status !== "approved" &&
                    article.processing_status !== "rejected" && (
                      <div className="flex space-x-1">
                        <button
                          onClick={() => handleApprove(article.id)}
                          disabled={processingActions.has(article.id)}
                          className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                        >
                          <CheckIcon className="h-3 w-3" />
                        </button>
                        <button
                          onClick={() => handleReject(article.id)}
                          disabled={processingActions.has(article.id)}
                          className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                        >
                          <XMarkIcon className="h-3 w-3" />
                        </button>
                      </div>
                    )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
          <div className="flex flex-1 justify-between sm:hidden">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Page <span className="font-medium">{page}</span> of{" "}
                <span className="font-medium">{totalPages}</span>
              </p>
            </div>
            <div>
              <nav
                className="isolate inline-flex -space-x-px rounded-md shadow-sm"
                aria-label="Pagination"
              >
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                >
                  <ChevronLeftIcon className="h-5 w-5 rotate-180" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
