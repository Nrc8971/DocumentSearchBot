**Doc'S' Bot - Document Search and Query System**
A modern web application that enables intelligent document searching and querying using AI embeddings. The system allows users to upload documents, process them for semantic search, and query them using natural language.
Features
Authentication & Authorization

Role-based access control (Admin/User)
Secure login system
Protected API endpoints
Token-based authentication

Document Management

Document upload with progress tracking
Support for multiple file formats
Background processing of documents
Document deletion (admin only)
File size validation (max 10MB)

Search Capabilities

Semantic search using AI embeddings
Natural language querying
Context-aware responses
Source citation in answers
Real-time search results

User Interface

Modern, responsive design
Clean and intuitive interface
Progress indicators for uploads
Error handling and user feedback
Mobile-friendly layout

Technology Stack
Backend

FastAPI (Python web framework)
Google's Generative AI for embeddings
Vector database for semantic search
AsyncIO for concurrent processing
OAuth2 for authentication

Frontend

React with TypeScript
Tailwind CSS for styling
React Hooks for state management
Axios for API communication

Installation
Prerequisites

Python 3.8+
Node.js 14+
npm or yarn
Google AI API key

Backend Setup

Clone the repository:

bashCopygit clone https://github.com/yourusername/docs-bot.git
cd docs-bot

Create and activate a virtual environment:

bashCopypython -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate

Install Python dependencies:

bashCopypip install -r requirements.txt

Set up environment variables:

bashCopy# Create .env file
touch .env

# Add the following variables
GOOGLE_API_KEY=your_google_api_key
MAX_FILE_SIZE=10485760  # 10MB in bytes
Frontend Setup

Navigate to the frontend directory:

bashCopycd frontend

Install dependencies:

bashCopynpm install
# or
yarn install

Create environment configuration:

bashCopy# Create .env file
touch .env

# Add the following variables
REACT_APP_API_URL=http://localhost:8000
Running the Application
Start the Backend Server
bashCopy# From the root directory
uvicorn main:app --reload
Start the Frontend Development Server
bashCopy# From the frontend directory
npm start
# or
yarn start
The application will be available at:

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Documentation: http://localhost:8000/docs

API Documentation
Authentication Endpoints

POST /login: User login
GET /logout: User logout

Document Endpoints

POST /upload: Upload new document
GET /documents: List all documents
DELETE /documents/{filename}: Delete a document
GET /status/{task_id}: Check document processing status

Search Endpoints

POST /query: Query documents with natural language

Development
Project Structure
Copy.
├── backend/
│   ├── main.py
│   ├── document_processing.py
│   ├── embedding.py
│   └── chunking.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── App.tsx
│   └── package.json
└── README.md
Contributing

Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

Security Considerations

Change default user credentials
Use proper environment variables
Implement rate limiting
Add proper input validation
Use HTTPS in production
Implement proper session management

License
This project is licensed under the MIT License - see the LICENSE.md file for details
Acknowledgments

Google Generative AI for embeddings
FastAPI for the backend framework
React for the frontend framework
All other open-source contributors

Support
For support, please open an issue in the GitHub repository or contact the maintainers.
