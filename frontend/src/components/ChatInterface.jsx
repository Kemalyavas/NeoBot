import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Bot, User, Loader2 } from 'lucide-react';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Merhaba! Ben NeoBot. Size nasıl yardımcı olabilirim?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Start a new chat session on load
    const startChat = async () => {
      try {
        const response = await axios.post('http://localhost:8000/api/chat/start');
        setThreadId(response.data.thread_id);
        console.log("Chat started, Thread ID:", response.data.thread_id);
      } catch (error) {
        console.error("Error starting chat:", error);
      }
    };
    startChat();
  }, []);

  const handleSend = async () => {
    if (!input.trim() || !threadId) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/chat/message', {
        thread_id: threadId,
        message: userMessage
      });

      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Üzgünüm, bir hata oluştu." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div style={{
      width: '100%',
      maxWidth: '600px',
      height: '80vh',
      backgroundColor: 'white',
      borderRadius: '12px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid #eee',
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        backgroundColor: '#fff'
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          backgroundColor: '#007AFF',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white'
        }}>
          <Bot size={24} />
        </div>
        <div>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#333' }}>NeoBot</h2>
          <span style={{ fontSize: '12px', color: '#666' }}>AI Assistant • Online</span>
        </div>
      </div>

      {/* Messages Area */}
      <div style={{
        flex: 1,
        padding: '20px',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: '15px',
        backgroundColor: '#f8f9fa'
      }}>
        {messages.map((msg, index) => (
          <div
            key={index}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
              gap: '10px'
            }}
          >
            {msg.role === 'assistant' && (
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#007AFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                flexShrink: 0
              }}>
                <Bot size={18} />
              </div>
            )}
            
            <div style={{
              maxWidth: '80%',
              padding: '12px 16px',
              borderRadius: '12px',
              backgroundColor: msg.role === 'user' ? '#007AFF' : 'white',
              color: msg.role === 'user' ? 'white' : '#333',
              boxShadow: msg.role === 'assistant' ? '0 2px 5px rgba(0,0,0,0.05)' : 'none',
              borderTopLeftRadius: msg.role === 'assistant' ? '4px' : '12px',
              borderTopRightRadius: msg.role === 'user' ? '4px' : '12px',
              whiteSpace: 'pre-wrap'
            }}>
              {msg.content.replace(/\*\*/g, '')}
            </div>

            {msg.role === 'user' && (
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#666',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                flexShrink: 0
              }}>
                <User size={18} />
              </div>
            )}
          </div>
        ))}
        {isLoading && (
          <div style={{ display: 'flex', gap: '10px' }}>
             <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#007AFF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white'
              }}>
                <Bot size={18} />
              </div>
              <div style={{
                padding: '12px 16px',
                backgroundColor: 'white',
                borderRadius: '12px',
                borderTopLeftRadius: '4px',
                display: 'flex',
                alignItems: 'center'
              }}>
                <Loader2 className="animate-spin" size={20} color="#007AFF" />
              </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{
        padding: '20px',
        backgroundColor: 'white',
        borderTop: '1px solid #eee',
        display: 'flex',
        gap: '10px'
      }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Bir mesaj yazın..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '12px 16px',
            borderRadius: '24px',
            border: '1px solid #e0e0e0',
            outline: 'none',
            fontSize: '14px'
          }}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          style={{
            width: '48px',
            height: '48px',
            borderRadius: '50%',
            backgroundColor: '#007AFF',
            color: 'white',
            border: 'none',
            cursor: isLoading ? 'not-allowed' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            opacity: isLoading ? 0.7 : 1
          }}
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;
