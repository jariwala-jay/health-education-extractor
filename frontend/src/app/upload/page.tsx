'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { uploadPDF, getPDFStatus, type PDFDocument } from '@/lib/api';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<PDFDocument[]>([]);
  const router = useRouter();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const pdfFiles = acceptedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== acceptedFiles.length) {
      toast.error('Only PDF files are allowed');
    }

    if (pdfFiles.length === 0) return;

    setUploading(true);

    for (const file of pdfFiles) {
      try {
        toast.loading(`Uploading ${file.name}...`, { id: file.name });
        
        const uploadedPdf = await uploadPDF(file);
        setUploadedFiles(prev => [...prev, uploadedPdf]);
        
        toast.success(`${file.name} uploaded successfully!`, { id: file.name });
        
        // Start polling for status updates
        pollPDFStatus(uploadedPdf.id);
        
      } catch (error) {
        console.error('Upload error:', error);
        toast.error(`Failed to upload ${file.name}`, { id: file.name });
      }
    }

    setUploading(false);
  }, []);

  const pollPDFStatus = async (pdfId: string) => {
    const maxAttempts = 60; // Poll for up to 5 minutes
    let attempts = 0;

    const poll = async () => {
      try {
        const status = await getPDFStatus(pdfId);
        
        // Update the file in our state
        setUploadedFiles(prev => 
          prev.map(file => file.id === pdfId ? status : file)
        );

        // Continue polling if still processing
        if (['uploaded', 'parsing', 'chunking', 'processing'].includes(status.processing_status) && attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000); // Poll every 5 seconds
        } else if (status.processing_status === 'completed') {
          toast.success(`Processing completed for ${status.filename}! Generated ${status.total_articles_generated || 0} articles.`);
        } else if (status.processing_status === 'failed') {
          toast.error(`Processing failed for ${status.filename}: ${status.error_message || 'Unknown error'}`);
        }
      } catch (error) {
        console.error('Error polling PDF status:', error);
        if (attempts < maxAttempts) {
          attempts++;
          setTimeout(poll, 5000);
        }
      }
    };

    // Start polling after a short delay
    setTimeout(poll, 2000);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: true,
    disabled: uploading
  });

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId));
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'processing':
      case 'parsing':
      case 'chunking':
        return 'text-yellow-600 bg-yellow-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
          Upload PDF
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Upload health education PDFs to extract and process content into simplified articles.
        </p>
      </div>

      {/* Upload Area */}
      <div className="mb-8">
        <div
          {...getRootProps()}
          className={`relative border-2 border-dashed rounded-lg p-6 ${
            isDragActive
              ? 'border-indigo-400 bg-indigo-50'
              : uploading
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed'
              : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50 cursor-pointer'
          } transition-colors`}
        >
          <input {...getInputProps()} />
          <div className="text-center">
            <CloudArrowUpIcon className={`mx-auto h-12 w-12 ${
              isDragActive ? 'text-indigo-400' : 'text-gray-400'
            }`} />
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-900">
                {isDragActive
                  ? 'Drop PDF files here'
                  : uploading
                  ? 'Uploading...'
                  : 'Drop PDF files here, or click to select'}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                PDF files up to 50MB each
              </p>
            </div>
          </div>
          {uploading && (
            <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-lg">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          )}
        </div>
      </div>

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Uploaded Files ({uploadedFiles.length})
            </h3>
            <div className="space-y-4">
              {uploadedFiles.map((file) => (
                <div key={file.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className="flex-shrink-0">
                      <DocumentIcon className="h-8 w-8 text-gray-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {file.filename}
                      </p>
                      <p className="text-xs text-gray-500">
                        {formatFileSize(file.file_size_bytes)}
                        {file.total_pages && (
                          <span> • {file.total_pages} pages</span>
                        )}
                        {file.total_articles_generated !== undefined && (
                          <span> • {file.total_articles_generated} articles</span>
                        )}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${getStatusColor(file.processing_status)}`}>
                      {file.processing_status.replace('_', ' ')}
                    </span>
                    
                    {file.processing_status === 'completed' && (
                      <Link
                        href="/articles"
                        className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
                      >
                        View Articles
                      </Link>
                    )}
                    
                    <button
                      onClick={() => removeFile(file.id)}
                      className="text-gray-400 hover:text-red-500"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Help Text */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="text-sm font-medium text-blue-900 mb-2">
          Processing Pipeline
        </h4>
        <ol className="text-sm text-blue-800 space-y-1 list-decimal list-inside">
          <li>PDF content is extracted and parsed</li>
          <li>Content is chunked into logical sections</li>
          <li>Health-relevant content is identified</li>
          <li>Articles are generated using AI summarization</li>
          <li>Relevant images are automatically matched</li>
          <li>Duplicate content is detected and filtered</li>
        </ol>
        <p className="text-xs text-blue-700 mt-3">
          Processing typically takes 1-3 minutes per PDF depending on size and complexity.
        </p>
      </div>
    </div>
  );
} 