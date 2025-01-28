import React, { useState, useEffect } from 'react';
import './index.css';
import './App.css';
import FileUpload from './components/fileupload.tsx';
import FileList from './components/filelist.tsx';
import DocumentSearch from './components/DocumentSearch.tsx';
import Login from './components/Login.tsx';
import { loginUser, uploadDocument, listDocuments, deleteDocument, queryDocument, checkUploadStatus, logoutUser } from './services/api.ts';

const App: React.FC = () => {
  const [documents, setDocuments] = useState<{ filename: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);

  const handleLogout = () => {
    logoutUser();
    setIsAuthenticated(false);
    setUserRole(null);
  };
  
  const handleLogin = async (username: string, password: string) => {
    try {
      const data = await loginUser(username, password);
      setIsAuthenticated(true);
      setUserRole(data.role);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('userRole', data.role);
    } catch (err) {
      setError('Login failed');
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedRole = localStorage.getItem('userRole');
    if (token && storedRole) {
      setIsAuthenticated(true);
      setUserRole(storedRole);
    }
  }, []);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await listDocuments();
        setDocuments(data.documents.map((filename: string) => ({ filename })));
      } catch (err) {
        setError('Failed to load documents');
      }
    };

    fetchDocuments();
  }, []);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const uploadResponse = await uploadDocument(file);
      
      const checkStatus = async (taskId: string) => {
        try {
          const status = await checkUploadStatus(taskId);
          if (status.status === 'processing') {
            setTimeout(() => checkStatus(taskId), 1000);
          } else if (status.status === 'completed') {
            const updatedDocuments = await listDocuments();
            setDocuments(updatedDocuments.documents.map((filename: string) => ({ filename })));
            setIsLoading(false);
          } else {
            setError('Document processing failed');
            setIsLoading(false);
          }
        } catch (err) {
          setError('Failed to check upload status');
          setIsLoading(false);
        }
      };

      checkStatus(uploadResponse.task_id);
    } catch (err) {
      setError('Failed to upload document');
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (filename: string) => {
    if (userRole !== 'admin') {
      setError('Only administrators can delete documents');
      return;
    }
    
    try {
      await deleteDocument(filename);
      const updatedDocuments = await listDocuments();
      setDocuments(updatedDocuments.documents.map((filename: string) => ({ filename })));
    } catch (err) {
      setError('Failed to delete document');
    }
  };

  const handleDocumentQuery = async (question: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await queryDocument(question);
      setIsLoading(false);
      return result.answer;
    } catch (err) {
      setError('Failed to query document');
      setIsLoading(false);
      return 'Error occurred while querying.';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="container mx-auto max-w-xl px-4">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-center">Doc'S' Bot</h1>
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
            >
              Logout
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {!isAuthenticated ? (
          <Login onLogin={handleLogin} />
        ) : (
          <>
            {userRole === 'admin' && (
              <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading} />
            )}
            <FileList 
              documents={documents} 
              onDeleteDocument={handleDeleteDocument} 
              isAdmin={userRole === 'admin'}
            />
            <DocumentSearch onQuery={handleDocumentQuery} isLoading={isLoading} />
          </>
        )}      
      </div>
    </div>
  );
};

export default App;
/**import React, { useState, useEffect } from 'react';
import './index.css';
import './App.css';
import FileUpload from './components/fileupload.tsx';
import FileList from './components/filelist.tsx';
import DocumentSearch from './components/DocumentSearch.tsx';
import Login from './components/Login.tsx'; // Import the new Login component
import { loginUser, uploadDocument, listDocuments, deleteDocument, queryDocument, checkUploadStatus, logoutUser } from './services/api.ts';

const App: React.FC = () => {
  const [documents, setDocuments] = useState<{ filename: string }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userRole, setUserRole] = useState<string | null>(null);

  const handleLogout = () => {
    logoutUser();
    setIsAuthenticated(false);
    setUserRole(null);
  };
  
  const handleLogin = async (username: string, password: string) => {
    try {
      const data = await loginUser(username, password);
      setIsAuthenticated(true);
      setUserRole(data.role);
      // Store authentication data
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('userRole', data.role);
    } catch (err) {
      setError('Login failed');
    }
  };
  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('token');
    const storedRole = localStorage.getItem('userRole');
    if (token && storedRole) {
      setIsAuthenticated(true);
      setUserRole(storedRole);
    }
  }, []);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const data = await listDocuments();
        setDocuments(data.documents.map((filename: string) => ({ filename })));
      } catch (err) {
        setError('Failed to load documents');
      }
    };

    fetchDocuments();
  }, []);

  const handleFileUpload = async (file: File) => {
    setIsLoading(true);
    setError(null);
    try {
      const uploadResponse = await uploadDocument(file);
      
      // Poll for status
      const checkStatus = async (taskId: string) => {
        try {
          const status = await checkUploadStatus(taskId);
          if (status.status === 'processing') {
            setTimeout(() => checkStatus(taskId), 1000);
          } else if (status.status === 'completed') {
            const updatedDocuments = await listDocuments();
            setDocuments(updatedDocuments.documents.map((filename: string) => ({ filename })));
            setIsLoading(false);
          } else {
            setError('Document processing failed');
            setIsLoading(false);
          }
        } catch (err) {
          setError('Failed to check upload status');
          setIsLoading(false);
        }
      };

      checkStatus(uploadResponse.task_id);
    } catch (err) {
      setError('Failed to upload document');
      setIsLoading(false);
    }
  };

  const handleDeleteDocument = async (filename: string) => {
    try {
      await deleteDocument(filename);
      const updatedDocuments = await listDocuments();
      setDocuments(updatedDocuments.documents.map((filename: string) => ({ filename })));
    } catch (err) {
      setError('Failed to delete document');
    }
  };

  const handleDocumentQuery = async (question: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await queryDocument(question);
      setIsLoading(false);
      return result.answer; // Return the answer for the chatbot
    } catch (err) {
      setError('Failed to query document');
      setIsLoading(false);
      return 'Error occurred while querying.';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10">
      <div className="container mx-auto max-w-xl px-4">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-center">Doc'S' Bot</h1>
          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
            >
              Logout
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {!isAuthenticated ? (
          <Login onLogin={handleLogin} /> // Render the login component
        ) : (
          <>
            {userRole === 'admin' && (
              <FileUpload onFileUpload={handleFileUpload} isLoading={isLoading} />
            )}
            <FileList documents={documents} onDeleteDocument={handleDeleteDocument} />
            <DocumentSearch onQuery={handleDocumentQuery} isLoading={isLoading} />
          </>
        )}      
      </div>
    </div>
  );
};

export default App;**/
