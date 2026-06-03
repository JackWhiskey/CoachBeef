import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function ChatPanel({ selectedActivityId }: { selectedActivityId: number | null }) {
    const [messages, setMessages] = useState<{ role: 'user' | 'coach', text: string }[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const sendMessage = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        // 1. Add user message to UI immediately
        const userMessage = input;
        setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
        setInput('');
        setIsLoading(true);

        try {
            // 2. Call your FastAPI Backend
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: userMessage, 
                    this_activity_id: selectedActivityId?.toString() || null
                }),
            });

            const data = await response.json();

            // 3. Add Coach Beef's response to UI
            if (response.ok) {
                setMessages(prev => [...prev, { role: 'coach', text: data.response }]);
            } else {
                console.error("Backend error:", data);
            }
        } catch (error) {
            console.error("Network error:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleClearHistory = async () => {
        // Double-check with the user first!
        if (!window.confirm("Are you sure you want to clear your chat history with Coach Beef?")) {
            return;
        }

        setIsLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/chat/history', {
                method: 'DELETE'
            });

            if (response.ok) {
                // Instantly wipe the screen on success
                setMessages([]);
            } else {
                console.error("Failed to clear chat history on the server.");
            }
        } catch (error) {
            console.error("Network error while clearing history:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLoadHistory = async () => {
        setIsLoading(true);
        try {
            const response = await fetch('http://localhost:8000/api/chat/history');
            
            if (response.ok) {
                const data = await response.json();
                
                // Map the backend data ({ role, content }) to our frontend state ({ role, text })
                // Note: OpenAI uses 'assistant', but your frontend uses 'coach'
                const formattedHistory = data.history.map((msg: any) => ({
                    role: msg.role === 'user' ? 'user' : 'coach',
                    text: msg.content
                }));
                
                setMessages(formattedHistory);
            } else {
                console.error("Failed to load chat history from the server.");
            }
        } catch (error) {
            console.error("Network error while loading history:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAthleteIntelligence = async () => {
        if (!selectedActivityId) return;

        setIsLoading(true);

        try {
            // 2. Hit your specialized Athlete Intelligence endpoint
            const response = await fetch('http://localhost:8000/api/chat/athlete-intelligence', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: "Generate summary",
                    this_activity_id: selectedActivityId
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // 3. Append Coach Beef's specialized summary
                setMessages(prev => [...prev, { role: 'coach', text: data.response }]);
            } else {
                console.error("Backend error:", data);
            }
        } catch (error) {
            console.error("Network error:", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <aside className="chat-panel" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
            <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'flex-start', 
                paddingBottom: '15px',
                borderBottom: '1px solid #e1e4e8',
                marginBottom: '20px'
            }}>
                <h3 style={{ margin: 0 }}>Coach Beef 🥩</h3>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
                <button 
                    onClick={handleAthleteIntelligence}
                    disabled={!selectedActivityId || isLoading}
                    style={{
                        backgroundColor: selectedActivityId ? 'rgba(252, 76, 2, 0.1)' : 'transparent',
                        border: selectedActivityId ? '1px solid #fc4c02' : '1px solid #e1e4e8',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        color: selectedActivityId ? '#fc4c02' : '#ccc',
                        cursor: (!selectedActivityId || isLoading) ? 'not-allowed' : 'pointer',
                        fontSize: '0.85rem',
                        fontWeight: 'bold',
                        transition: 'all 0.2s ease'
                    }}
                >
                    Athlete Intelligence
                </button>
                <button 
                    onClick={handleLoadHistory}
                    disabled={isLoading}
                    style={{
                        backgroundColor: 'transparent',
                        border: '1px solid #e1e4e8',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        color: '#666',
                        cursor: isLoading ? 'not-allowed' : 'pointer',
                        fontSize: '0.85rem',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f4f5f7'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                    🔄 Load
                </button>
                <button 
                    onClick={handleClearHistory}
                    disabled={isLoading}
                    style={{
                        backgroundColor: 'transparent',
                        border: '1px solid #e1e4e8',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        color: '#666',
                        cursor: isLoading ? 'not-allowed' : 'pointer',
                        fontSize: '0.85rem',
                        transition: 'all 0.2s ease'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#ffeee6'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                    🗑️ Clear
                </button>
            </div>
            
            {/* 1. Message History Area */}
            <div style={{ flex: 1, overflowY: 'auto', marginBottom: '20px', paddingRight: '10px', marginTop: '20px',}}>
            {messages.length === 0 ? (
                <p style={{ color: '#888' }}></p>
            ) : (
                messages.map((msg, idx) => (
                <div key={idx} style={{ 
                    marginBottom: '15px', 
                    textAlign: msg.role === 'user' ? 'right' : 'left'
                }}>
                    <div style={{
                        display: 'inline-block',
                        padding: '10px 15px',
                        borderRadius: '12px',
                        backgroundColor: msg.role === 'user' ? '#fc4c02' : '#f0f0f0',
                        color: msg.role === 'user' ? '#fff' : '#333',
                        maxWidth: '85%',
                        textAlign: 'left',
                        lineHeight: '1.4'
                        }}>
                        {msg.role === 'coach' ? (
                            <div className="coach-markdown">
                                <ReactMarkdown>{msg.text}</ReactMarkdown>
                            </div>
                        ) : (
                            msg.text
                        )}
                    </div>
                </div>
                ))
            )}
            {isLoading && <div style={{ color: '#888', fontStyle: 'italic' }}>Coach is thinking...</div>}
            </div>

            {/* 2. Input Form */}
            <form onSubmit={sendMessage} style={{ display: 'flex', gap: '10px' }}>
            <input 
                type="text" 
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask Coach Beef to analyze this run..."
                style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid #ccc' }}
                disabled={isLoading}
            />
            <button 
                type="submit" 
                disabled={isLoading}
                style={{ padding: '0 20px', backgroundColor: '#fc4c02', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
            >
                Send
            </button>
            </form>
        </aside>
    );
}