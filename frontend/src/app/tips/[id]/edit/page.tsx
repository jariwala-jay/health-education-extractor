"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { apiClient } from "@/lib/api";

interface DailyTip {
  id: string;
  tip_text: string;
  category: "Hypertension" | "Obesity" | "Diabetes" | "Prediabetes" | "Nutrition" | "General";
  tags: string[];
  source_article_id?: string;
  image_url?: string;
  processing_status: "draft" | "reviewed" | "approved" | "uploaded" | "rejected";
  app_tip_id?: string;
  reading_level_score?: number;
  created_at: string;
  updated_at: string;
  reviewed_at?: string;
  reviewer_notes?: string;
}

export default function EditTipPage() {
  const { user } = useAuth();
  const params = useParams();
  const router = useRouter();
  const tipId = params.id as string;

  const [tip, setTip] = useState<DailyTip | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    tip_text: "",
    category: "General" as string,
    tags: [] as string[],
    image_url: "",
    processing_status: "draft" as string,
    reviewer_notes: "",
  });

  const [newTag, setNewTag] = useState("");

  useEffect(() => {
    if (user && tipId) {
      fetchTip();
    }
  }, [user, tipId]);

  const fetchTip = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get(`/api/v1/tips/${tipId}`);
      const tipData = response.data;
      setTip(tipData);
      setFormData({
        tip_text: tipData.tip_text,
        category: tipData.category || "General",
        tags: tipData.tags || [],
        image_url: tipData.image_url || "",
        processing_status: tipData.processing_status,
        reviewer_notes: tipData.reviewer_notes || "",
      });
    } catch (err) {
      setError("Failed to fetch tip");
      console.error("Error fetching tip:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await apiClient.put(`/api/v1/tips/${tipId}`, formData);
      router.push("/tips");
    } catch (err) {
      setError("Failed to save tip");
      console.error("Error saving tip:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()],
      });
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove),
    });
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddTag();
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h1>
          <p className="text-gray-600">Please log in to edit tips.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <p className="mt-2 text-gray-600">Loading tip...</p>
        </div>
      </div>
    );
  }

  if (!tip) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Tip Not Found</h1>
          <p className="text-gray-600">The tip you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Edit Daily Tip</h1>
                <p className="mt-2 text-gray-600">
                  Modify tip content, tags, and processing status
                </p>
              </div>
              <button
                onClick={() => router.push("/tips")}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Back to Tips
              </button>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {/* Form */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="space-y-6">
              {/* Tip Text */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tip Text *
                </label>
                <textarea
                  value={formData.tip_text}
                  onChange={(e) => setFormData({ ...formData, tip_text: e.target.value })}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter the tip text..."
                />
                <p className="mt-1 text-sm text-gray-500">
                  {formData.tip_text.length}/200 characters
                </p>
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="General">General</option>
                  <option value="Hypertension">Hypertension</option>
                  <option value="Obesity">Obesity</option>
                  <option value="Diabetes">Diabetes</option>
                  <option value="Prediabetes">Prediabetes</option>
                  <option value="Nutrition">Nutrition</option>
                </select>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <div className="flex flex-wrap gap-2 mb-3">
                  {formData.tags.map((tag, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
                    >
                      {tag}
                      <button
                        type="button"
                        onClick={() => handleRemoveTag(tag)}
                        className="ml-2 text-blue-600 hover:text-blue-800"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Add a tag..."
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    onClick={handleAddTag}
                    className="px-4 py-2 text-sm font-medium text-blue-700 bg-blue-100 border border-blue-300 rounded-md hover:bg-blue-200"
                  >
                    Add Tag
                  </button>
                </div>
              </div>

              {/* Image URL */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Image URL
                </label>
                <input
                  type="url"
                  value={formData.image_url}
                  onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://example.com/image.jpg"
                />
                {formData.image_url && (
                  <div className="mt-3">
                    <img
                      src={formData.image_url}
                      alt="Tip preview"
                      className="w-32 h-32 object-cover rounded-lg"
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  </div>
                )}
              </div>

              {/* Processing Status */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Processing Status
                </label>
                <select
                  value={formData.processing_status}
                  onChange={(e) => setFormData({ ...formData, processing_status: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="draft">Draft</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="approved">Approved</option>
                  <option value="uploaded">Uploaded</option>
                  <option value="rejected">Rejected</option>
                </select>
              </div>

              {/* Reviewer Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Reviewer Notes
                </label>
                <textarea
                  value={formData.reviewer_notes}
                  onChange={(e) => setFormData({ ...formData, reviewer_notes: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Add any notes about this tip..."
                />
              </div>

              {/* Tip Info */}
              <div className="bg-gray-50 p-4 rounded-md">
                <h3 className="text-sm font-medium text-gray-900 mb-2">Tip Information</h3>
                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Created:</span> {new Date(tip.created_at).toLocaleDateString()}
                  </div>
                  <div>
                    <span className="font-medium">Updated:</span> {new Date(tip.updated_at).toLocaleDateString()}
                  </div>
                  {tip.reading_level_score && (
                    <div>
                      <span className="font-medium">Reading Level:</span> Grade {tip.reading_level_score.toFixed(1)}
                    </div>
                  )}
                  {tip.source_article_id && (
                    <div>
                      <span className="font-medium">Source Article:</span> {tip.source_article_id}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end space-x-4 pt-6 border-t">
                <button
                  onClick={() => router.push("/tips")}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || !formData.tip_text.trim()}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
