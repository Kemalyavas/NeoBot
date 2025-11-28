import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, User, Loader2 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import neobiIcon from '../assets/neobi-icon.png';

// API Base URL: Production'da aynı origin'den sunulduğu için boş string kullanıyoruz
// Development'ta Vite proxy kullanılabilir veya .env.development ile override edilebilir
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Merhaba! Ben NeoBI. Size nasıl yardımcı olabilirim?' }
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

  // Custom Tooltip Component - Minimal Design
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const value = payload[0].value;

      return (
        <div style={{
          backgroundColor: 'rgba(255, 255, 255, 0.98)',
          padding: '12px 16px',
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          border: '1px solid #e0e0e0'
        }}>
          <p style={{
            margin: '0 0 6px 0',
            fontWeight: '600',
            color: '#333',
            fontSize: '13px'
          }}>{label}</p>
          <p style={{
            margin: '0',
            color: '#007AFF',
            fontWeight: '700',
            fontSize: '18px'
          }}>
            {value.toLocaleString('tr-TR')}
          </p>
        </div>
      );
    }
    return null;
  };

  // Helper to parse and render message content (Text + Chart)
  const renderMessageContent = (content) => {
    // 1. Check for JSON code block
    const jsonBlockRegex = /```json\s*([\s\S]*?)\s*```/;
    const match = content.match(jsonBlockRegex);

    let chartData = null;
    let textContent = content;

    if (match) {
      try {
        const parsed = JSON.parse(match[1]);
        if (parsed.type === 'chart') {
          chartData = parsed;
          // Calculate total for percentage
          const total = chartData.data.reduce((sum, item) => sum + item.value, 0);
          chartData.data = chartData.data.map(item => ({ ...item, total }));

          // Remove the JSON block from text to avoid duplication
          textContent = content.replace(match[0], '').trim();
        }
      } catch (e) {
        console.error("Failed to parse JSON in message", e);
      }
    }

    // Clean up markdown bolding for text
    const cleanText = textContent.replace(/\*\*/g, '');

    return (
      <div>
        {cleanText && <div style={{ whiteSpace: 'pre-wrap' }}>{cleanText}</div>}

        {chartData && (
          <div style={{
            marginTop: '20px',
            width: 'calc(100% + 8px)',
            marginLeft: '-4px',
            padding: '16px 12px',
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            border: '1px solid #e9ecef'
          }}>
            <div style={{
              marginBottom: '16px',
              paddingBottom: '12px',
              borderBottom: '1px solid #e9ecef'
            }}>
              <p style={{
                fontWeight: '600',
                fontSize: '15px',
                color: '#212529',
                margin: '0'
              }}>
                {chartData.title}
              </p>
            </div>

            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={chartData.data}
                margin={{ top: 10, right: 5, left: 5, bottom: 80 }}
              >
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#007AFF" stopOpacity={0.85}/>
                    <stop offset="100%" stopColor="#007AFF" stopOpacity={0.65}/>
                  </linearGradient>
                </defs>

                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#e9ecef"
                  vertical={false}
                />

                <XAxis
                  dataKey="name"
                  tick={{
                    fontSize: 11,
                    fontWeight: 500,
                    fill: '#6c757d'
                  }}
                  interval={0}
                  angle={-40}
                  textAnchor="end"
                  height={85}
                  stroke="#dee2e6"
                />

                <YAxis
                  tick={{
                    fontSize: 12,
                    fontWeight: 500,
                    fill: '#6c757d'
                  }}
                  stroke="#dee2e6"
                  label={{
                    value: 'Satış Adedi',
                    angle: -90,
                    position: 'insideLeft',
                    style: {
                      fontSize: '12px',
                      fill: '#6c757d',
                      fontWeight: 500
                    }
                  }}
                />

                <Tooltip content={<CustomTooltip />} cursor={{fill: 'rgba(0, 122, 255, 0.04)'}} />

                <Bar
                  dataKey="value"
                  fill="url(#barGradient)"
                  radius={[6, 6, 0, 0]}
                  animationDuration={600}
                  animationBegin={0}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    );
  };


  useEffect(() => {
    // Start a new chat session on load
    const startChat = async () => {
      try {
        const response = await axios.post(`${API_BASE_URL}/api/chat/start`);
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
      const response = await axios.post(`${API_BASE_URL}/api/chat/message`, {
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
        padding: '16px 20px',
        borderBottom: '1px solid #eee',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        backgroundColor: '#fff'
      }}>
        <img 
          src={neobiIcon} 
          alt="NeoBI" 
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            objectFit: 'cover'
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
          <h2 style={{ margin: 0, fontSize: '18px', color: '#333', lineHeight: '1.2' }}>NeoBI</h2>
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
              <img 
                src={neobiIcon} 
                alt="NeoBI" 
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  flexShrink: 0
                }}
              />
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
            }}>
              {renderMessageContent(msg.content)}
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
             <img 
                src={neobiIcon} 
                alt="NeoBI" 
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  objectFit: 'cover'
                }}
              />
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
