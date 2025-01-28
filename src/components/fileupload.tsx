import React, { useState, useRef } from 'react';
import { FaCloudUploadAlt } from 'react-icons/fa';

interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  isLoading: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileUpload, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setErrorMessage(null);
      try {
        await onFileUpload(file);
      } catch (error) {
        setErrorMessage('Failed to upload the document. Please try again.');
      }
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="w-full p-4 bg-white rounded-lg shadow-md">
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
          accept=".pdf,.docx,.txt,.md,.doc,.pptx,.xlsx"
        />
        <button 
          onClick={triggerFileInput}
          disabled={isLoading}
          className={`w-full flex items-center justify-center p-4 border-2 border-dashed rounded-lg transition-colors duration-300 ease-in-out ${
            isLoading 
              ? 'bg-gray-300 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600 border-blue-400 text-white'
          } shadow-md hover:shadow-lg`}
        >
          <FaCloudUploadAlt className="mr-2 text-2xl" />
          <span className="font-semibold">
            {isLoading ? 'Uploading...' : 'Upload Document'}
          </span>
        </button>
        {selectedFile && (
          <div className="mt-2 text-sm text-gray-600">
            Selected: {selectedFile.name}
          </div>
        )}
        {errorMessage && (
          <div className="mt-2 text-sm text-red-600">
            {errorMessage}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;
