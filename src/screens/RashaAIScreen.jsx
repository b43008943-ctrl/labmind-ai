import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, Bot, User, Send, Loader2 } from 'lucide-react';
import { useNavigation } from '../context/NavigationContext';
import { askRasha } from '../services/apiClient';

export default function RashaAIScreen() {
    const { goBack } = useNavigation();
    
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    
    const messagesEndRef = useRef(null);

    // Auto-scroll to bottom when messages change
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isTyping]);

    const suggestions = [
        "What is sickle cell disease?",
        "How to read a Gram stain?",
        "Normal urine sediment findings?",
        "Difference between cocci and bacilli?"
    ];

    const handleSendMessage = async (textToSend = inputText) => {
        const text = textToSend.trim();
        if (!text || isTyping) return;

        // 1. Add user message to UI immediately
        const userMsg = {
            id: Date.now().toString(),
            role: 'user',
            content: text,
            timestamp: new Date()
        };
        
        setMessages(prev => [...prev, userMsg]);
        setInputText('');
        setIsTyping(true);

        try {
            // 2. Call backend API
            const response = await askRasha(text, null, sessionId);
            
            // 3. Update sessionId if returned (for conversation continuity)
            if (response.session_id && !sessionId) {
                setSessionId(response.session_id);
            }

            // 4. Add AI response to UI
            const aiMsg = {
                id: (Date.now() + 1).toString(),
                role: 'ai',
                content: response.reply,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, aiMsg]);
        } catch (error) {
            console.error('Error asking Rasha:', error);
            // Add error message to UI
            const errorMsg = {
                id: (Date.now() + 1).toString(),
                role: 'ai',
                content: "I'm sorry, I'm having trouble connecting to my neural network right now. Please try again later.",
                isError: true,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const formatTime = (date) => {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    return (
        <div style={{
            minHeight:'100vh',
            height:'100vh',
            background:'radial-gradient(ellipse at 40% 10%, rgba(139,92,246,0.1), transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(245,158,11,0.06), transparent 40%), linear-gradient(180deg,#070C1A,#050810)',
            fontFamily:"'Plus Jakarta Sans',sans-serif",
            color:'#E8F4FF',
            display:'flex',
            flexDirection:'column',
            overflow:'hidden',
        }}>

            <style>{`
@keyframes rashaTyping {
                    0%,100%{opacity:0.3;transform:scale(0.8);}
                    50%{opacity:1;transform:scale(1.2);}
                }
                @keyframes rashaFadeIn {
                    from{opacity:0;transform:translateY(10px);}
                    to{opacity:1;transform:translateY(0);}
                }
            `}</style>

            {/* ══════════ HEADER ══════════ */}
            <div style={{
                padding:'14px 20px',
                background:'rgba(5,8,16,0.9)',
                backdropFilter:'blur(24px)',
                WebkitBackdropFilter:'blur(24px)',
                borderBottom:'1px solid rgba(139,92,246,0.12)',
                display:'flex',alignItems:'center',gap:12,
                flexShrink:0,
            }}>
                <button
                    onClick={goBack}
                    style={{
                        width:36,height:36,borderRadius:10,
                        background:'rgba(255,255,255,0.04)',
                        border:'1px solid rgba(255,255,255,0.08)',
                        display:'flex',alignItems:'center',justifyContent:'center',
                        cursor:'pointer',color:'rgba(255,255,255,0.6)',fontSize:16,flexShrink:0,
                    }}
                >←</button>

                {/* Rasha Avatar */}
                <div style={{
                    width:38,height:38,borderRadius:'50%',
                    background:'radial-gradient(circle at 35% 35%, rgba(139,92,246,0.9), rgba(245,158,11,0.7))',
                    display:'flex',alignItems:'center',justifyContent:'center',
                    fontSize:18,flexShrink:0,
                    boxShadow:'0 0 16px rgba(139,92,246,0.4)',
                }}>🤖</div>

                <div style={{flex:1}}>
                    <h1 style={{margin:0,fontSize:15,fontWeight:800,color:'#F0F9FF',letterSpacing:-0.3}}>
                        Rasha AI
                    </h1>
                    <div style={{display:'flex',alignItems:'center',gap:5}}>
                        <div style={{width:5,height:5,borderRadius:'50%',background:'#10B981',boxShadow:'0 0 5px #10B981'}}/>
                        <p style={{margin:0,fontSize:9,color:'rgba(255,255,255,0.3)',letterSpacing:1,fontFamily:"'JetBrains Mono',monospace"}}>
                            ONLINE • SMART ANALYST
                        </p>
                    </div>
                </div>
            </div>

            {/* ══════════ MESSAGES AREA ══════════ */}
            <div style={{
                flex:1,
                overflowY:'auto',
                WebkitOverflowScrolling:'touch',
                padding:'16px 16px 8px',
                display:'flex',
                flexDirection:'column',
                gap:12,
            }}>

                {/* Welcome state if no messages */}
                {messages.length === 0 ? (
                    <div style={{
                        textAlign:'center',
                        padding:'40px 20px',
                        display:'flex',
                        flexDirection:'column',
                        alignItems:'center',
                        gap:12,
                        animation:'rashaFadeIn 0.4s ease-out',
                    }}>
                        <div style={{
                            width:64,height:64,borderRadius:'50%',
                            background:'radial-gradient(circle at 35% 35%, rgba(139,92,246,0.8), rgba(245,158,11,0.6))',
                            display:'flex',alignItems:'center',justifyContent:'center',
                            fontSize:28,position:'relative',
                            boxShadow:'0 0 30px rgba(139,92,246,0.3)',
                        }}>
                            🤖
                            <div style={{
                                position:'absolute',bottom:2,right:2,
                                width:14,height:14,borderRadius:'50%',
                                background:'#10B981',border:'2px solid #070C1A',
                            }}/>
                        </div>
                        <h2 style={{margin:0,fontSize:16,fontWeight:800,color:'#F0F9FF'}}>
                            Hi! I'm Rasha, your AI lab assistant
                        </h2>
                        <p style={{margin:0,fontSize:12,color:'rgba(255,255,255,0.4)',maxWidth:280,lineHeight:1.6}}>
                            Ask me anything about medical laboratory science, diagnostics, or lab procedures.
                        </p>

                        {/* Quick suggestions — calls handleSendMessage directly */}
                        <div style={{display:'flex',flexDirection:'column',gap:8,width:'100%',maxWidth:340,marginTop:12}}>
                            {suggestions.map((suggestion, index) => (
                                <button
                                    key={index}
                                    onClick={() => handleSendMessage(suggestion)}
                                    style={{
                                        width:'100%',textAlign:'left',
                                        padding:'12px 16px',borderRadius:12,
                                        background:'rgba(139,92,246,0.06)',
                                        border:'1px solid rgba(139,92,246,0.15)',
                                        color:'rgba(255,255,255,0.7)',fontSize:12,fontWeight:500,
                                        cursor:'pointer',
                                        fontFamily:"'Plus Jakarta Sans',sans-serif",
                                        transition:'all 0.15s',
                                    }}
                                    onMouseEnter={e => {e.currentTarget.style.background='rgba(139,92,246,0.12)';e.currentTarget.style.borderColor='rgba(139,92,246,0.3)';e.currentTarget.style.color='#F0F9FF';}}
                                    onMouseLeave={e => {e.currentTarget.style.background='rgba(139,92,246,0.06)';e.currentTarget.style.borderColor='rgba(139,92,246,0.15)';e.currentTarget.style.color='rgba(255,255,255,0.7)';}}
                                >{suggestion}</button>
                            ))}
                        </div>
                    </div>
                ) : (
                    /* Messages list */
                    <div style={{display:'flex',flexDirection:'column',gap:12}}>
                        {messages.map((msg) => {
                            const isUser = msg.role === 'user';
                            return (
                                <div key={msg.id} style={{
                                    display:'flex',
                                    justifyContent: isUser ? 'flex-end' : 'flex-start',
                                    gap:8,
                                    alignItems:'flex-end',
                                    animation:'rashaFadeIn 0.3s ease-out',
                                }}>
                                    {/* AI avatar */}
                                    {!isUser && (
                                        <div style={{
                                            width:28,height:28,borderRadius:'50%',flexShrink:0,
                                            background:'radial-gradient(circle, rgba(139,92,246,0.8), rgba(245,158,11,0.5))',
                                            display:'flex',alignItems:'center',justifyContent:'center',
                                            fontSize:12,
                                        }}>🤖</div>
                                    )}

                                    <div style={{
                                        display:'flex',flexDirection:'column',
                                        gap:3,
                                        maxWidth:'78%',
                                        alignItems: isUser ? 'flex-end' : 'flex-start',
                                    }}>
                                        <div style={{
                                            padding:'10px 14px',
                                            borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                                            background: isUser
                                                ? 'linear-gradient(135deg,rgba(139,92,246,0.25),rgba(139,92,246,0.15))'
                                                : msg.isError
                                                    ? 'rgba(239,68,68,0.08)'
                                                    : 'rgba(255,255,255,0.05)',
                                            border: isUser
                                                ? '1px solid rgba(139,92,246,0.3)'
                                                : msg.isError
                                                    ? '1px solid rgba(239,68,68,0.2)'
                                                    : '1px solid rgba(255,255,255,0.08)',
                                            fontSize:12,
                                            lineHeight:1.7,
                                            color: isUser ? '#DDD6FF' : msg.isError ? '#FCA5A5' : 'rgba(255,255,255,0.85)',
                                            whiteSpace:'pre-wrap',
                                        }}>
                                            {msg.content}
                                        </div>
                                        <span style={{
                                            fontSize:9,color:'rgba(255,255,255,0.2)',
                                            fontFamily:"'JetBrains Mono',monospace",
                                            paddingLeft:4,paddingRight:4,
                                        }}>
                                            {formatTime(msg.timestamp)}
                                        </span>
                                    </div>

                                    {/* User avatar */}
                                    {isUser && (
                                        <div style={{
                                            width:28,height:28,borderRadius:'50%',flexShrink:0,
                                            background:'rgba(34,211,238,0.15)',
                                            border:'1px solid rgba(34,211,238,0.3)',
                                            display:'flex',alignItems:'center',justifyContent:'center',
                                            fontSize:12,
                                        }}>👤</div>
                                    )}
                                </div>
                            );
                        })}

                        {/* Typing indicator */}
                        {isTyping && (
                            <div style={{display:'flex',gap:8,alignItems:'flex-end',animation:'rashaFadeIn 0.3s ease-out'}}>
                                <div style={{
                                    width:28,height:28,borderRadius:'50%',
                                    background:'radial-gradient(circle, rgba(139,92,246,0.8), rgba(245,158,11,0.5))',
                                    display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,
                                }}>🤖</div>
                                <div style={{
                                    padding:'12px 16px',
                                    background:'rgba(255,255,255,0.05)',
                                    border:'1px solid rgba(255,255,255,0.08)',
                                    borderRadius:'16px 16px 16px 4px',
                                    display:'flex',gap:4,alignItems:'center',
                                }}>
                                    {[0,1,2].map(j => (
                                        <div key={j} style={{
                                            width:6,height:6,borderRadius:'50%',
                                            background:'rgba(139,92,246,0.7)',
                                            animation:`rashaTyping 1.2s ease-in-out ${j*0.2}s infinite`,
                                        }}/>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>
                )}
            </div>

            {/* ══════════ INPUT AREA ══════════ */}
            <div style={{
                padding:'12px 16px 24px',
                background:'rgba(5,8,16,0.9)',
                backdropFilter:'blur(20px)',
                WebkitBackdropFilter:'blur(20px)',
                borderTop:'1px solid rgba(255,255,255,0.05)',
                flexShrink:0,
            }}>
                <div style={{
                    display:'flex',gap:8,
                    background:'rgba(255,255,255,0.04)',
                    border:'1px solid rgba(139,92,246,0.2)',
                    borderRadius:14,
                    padding:'6px 6px 6px 14px',
                    alignItems:'flex-end',
                    maxWidth:700,margin:'0 auto',
                }}>
                    <textarea
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask Rasha anything about lab science..."
                        rows={1}
                        disabled={isTyping}
                        style={{
                            flex:1,background:'transparent',
                            border:'none',outline:'none',
                            fontSize:12,color:'#F0F9FF',
                            fontFamily:"'Plus Jakarta Sans',sans-serif",
                            resize:'none',lineHeight:1.5,
                            maxHeight:80,overflowY:'auto',
                            paddingTop:6,
                        }}
                    />
                    <button
                        onClick={() => handleSendMessage()}
                        disabled={!inputText.trim() || isTyping}
                        style={{
                            width:38,height:38,borderRadius:10,flexShrink:0,
                            background: inputText.trim() && !isTyping
                                ? 'linear-gradient(135deg,#5B21B6,#8B5CF6)'
                                : 'rgba(255,255,255,0.05)',
                            border:'none',cursor: inputText.trim() && !isTyping ? 'pointer' : 'default',
                            display:'flex',alignItems:'center',justifyContent:'center',
                            fontSize:16,
                            boxShadow: inputText.trim() && !isTyping ? '0 0 12px rgba(139,92,246,0.4)' : 'none',
                            transition:'all 0.15s',
                            color: inputText.trim() && !isTyping ? '#fff' : 'rgba(255,255,255,0.2)',
                        }}
                    >
                        {isTyping ? '⏳' : '➤'}
                    </button>
                </div>
                <p style={{
                    margin:'6px 0 0',fontSize:9,
                    color:'rgba(255,255,255,0.15)',
                    textAlign:'center',letterSpacing:0.3,
                }}>
                    Rasha AI • Powered by LabMind • Educational use only
                </p>
            </div>

        </div>
    );
}
