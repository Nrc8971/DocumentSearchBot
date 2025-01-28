import React, { useState } from 'react';
import { FaPaperPlane } from 'react-icons/fa';
import '../chatbot.css'; // Updated import path

interface Message {
  text: string;
  sender: 'user' | 'bot';
}

interface DocumentSearchProps {
  onQuery: (question: string) => Promise<string>;
  isLoading: boolean;
}

const DocumentSearch: React.FC<DocumentSearchProps> = ({ onQuery, isLoading }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      const userMessage: Message = { text: input, sender: 'user' };
      setMessages((prev) => [...prev, userMessage]);
      setInput('');
      const botResponse = await onQuery(input);
      const botMessage: Message = { text: botResponse, sender: 'bot' };
      setMessages((prev) => [...prev, botMessage]);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="input-form">
        <input 
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={isLoading}
          className="input-field"
        />
        <button 
          type="submit"
          disabled={isLoading || !input.trim()}
          className="send-button"
        >
          <FaPaperPlane />
        </button>
      </form>
    </div>
  );
};

export default DocumentSearch;
