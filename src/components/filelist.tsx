import React from 'react';
import { FaTrash } from 'react-icons/fa';

interface Document {
  filename: string;
}

interface FileListProps {
  documents: Document[];
  onDeleteDocument: (filename: string) => Promise<void>;
  isAdmin: boolean;
}

const FileList: React.FC<FileListProps> = ({ documents, onDeleteDocument, isAdmin }) => {
  if (documents.length === 0) {
    return (
      <div className="mt-4 bg-white rounded-lg shadow-md p-4 text-gray-600">
        No documents uploaded yet.
      </div>
    );
  }

  return (
    <div className="mt-4 bg-white rounded-lg shadow-md">
      <div className="p-4 border-b font-semibold text-gray-700">
        Uploaded Documents
      </div>
      {documents.map((doc) => (
        <div 
          key={doc.filename} 
          className="flex justify-between items-center p-4 border-b last:border-b-0 hover:bg-gray-50"
        >
          <span className="text-gray-700">{doc.filename}</span>
          {isAdmin && (
            <button 
              onClick={() => onDeleteDocument(doc.filename)}
              className="text-red-500 hover:text-red-700 transition-colors"
              aria-label="Delete document"
            >
              <FaTrash />
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

export default FileList;
/**import React from 'react';
import { FaTrash } from 'react-icons/fa';

interface Document {
  filename: string;
}

interface FileListProps {
  documents: Document[];
  onDeleteDocument: (filename: string) => Promise<void>;
}

const FileList: React.FC<FileListProps> = ({ documents, onDeleteDocument }) => {
  if (documents.length === 0) {
    return (
      <div className="mt-4 bg-white rounded-lg shadow-md p-4 text-gray-600">
        No documents uploaded yet.
      </div>
    );
  }

  return (
    <div className="mt-4 bg-white rounded-lg shadow-md">
      <div className="p-4 border-b font-semibold text-gray-700">
        Uploaded Documents
      </div>
      {documents.map((doc) => (
        <div 
          key={doc.filename} 
          className="flex justify-between items-center p-4 border-b last:border-b-0 hover:bg-gray-50"
        >
          <span className="text-gray-700">{doc.filename}</span>
          <button 
            onClick={() => onDeleteDocument(doc.filename)}
            className="text-red-500 hover:text-red-700 transition-colors"
          >
            <FaTrash />
          </button>
        </div>
      ))}
    </div>
  );
};

export default FileList;**/
