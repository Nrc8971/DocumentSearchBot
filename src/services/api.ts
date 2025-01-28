import axios from 'axios';

const API_URL = 'http://localhost:8000';

export interface DocumentQueryResponse {
  answer: string;
  sources: string[];
}

export const logoutUser = () => {
  // Clear any stored tokens/session data
  localStorage.removeItem('token');
  localStorage.removeItem('userRole');
};

export const loginUser = async (username: string, password: string) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  try {
    const response = await axios.post(`${API_URL}/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
  } catch (error) {
    console.error('Login failed', error);
    throw error;
  }
};

const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const uploadDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await axios.post(`${API_URL}/upload`, formData, {
      headers: { 
        'Content-Type': 'multipart/form-data',
        ...getAuthHeader()
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total!
        );
        console.log(`Upload progress: ${percentCompleted}%`);
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Upload failed', error);
    throw error;
  }
};

export const listDocuments = async () => {
  try {
    const response = await axios.get(`${API_URL}/documents`);
    return response.data;
  } catch (error) {
    console.error('Failed to list documents', error);
    throw error;
  }
};

export const deleteDocument = async (filename: string) => {
  try {
    const response = await axios.delete(`${API_URL}/documents/${filename}`);
    return response.data;
  } catch (error) {
    console.error('Failed to delete document', error);
    throw error;
  }
};

export const queryDocument = async (question: string): Promise<DocumentQueryResponse> => {
  try {
    const response = await axios.post(`${API_URL}/query`, { question });
    return response.data;
  } catch (error) {
    console.error('Query failed', error);
    throw error;
  }
};

export const checkUploadStatus = async (taskId: string) => {
  try {
    const response = await axios.get(`${API_URL}/status/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Status check failed', error);
    throw error;
  }
};