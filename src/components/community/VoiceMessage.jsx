/* VoiceMessage — Audio playback bubble inside chat messages */

import { useState, useEffect, useRef } from 'react';

export default function VoiceMessage({ msg, chatColor, hex2rgba }) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const audioRef = useRef(null);

    useEffect(() => {
        if (msg.audioUrl && !audioRef.current) {
            audioRef.current = new Audio(msg.audioUrl);
            audioRef.current.onended = () => {
                setIsPlaying(false);
                setProgress(0);
            };
            audioRef.current.ontimeupdate = () => {
                const duration = audioRef.current.duration;
                const currentTime = audioRef.current.currentTime;
                if (duration) {
                    setProgress((currentTime / duration) * 100);
                }
            };
        }
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
        };
    }, [msg.audioUrl]);

    const togglePlayback = () => {
        if (!audioRef.current) return;

        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            audioRef.current.play().catch(e => console.error("Audio playback failed", e));
            setIsPlaying(true);
        }
    };

    return (
        <div className="flex items-center gap-3 relative z-10 w-48 py-1">
            <button
                onClick={togglePlayback}
                className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 border border-current shadow-[0_0_15px_currentColor] cursor-pointer transition-transform active:scale-95"
                style={{ color: chatColor, backgroundColor: hex2rgba(chatColor, 0.15) }}
            >
                {isPlaying ? (
                    <div className="flex gap-1">
                        <div className="w-1 h-3 bg-current rounded-sm shadow-[0_0_5px_currentColor]" />
                        <div className="w-1 h-3 bg-current rounded-sm shadow-[0_0_5px_currentColor]" />
                    </div>
                ) : (
                    <div className="w-0 h-0 border-t-[5px] border-b-[5px] border-l-[8px] border-transparent border-l-current ml-1 shadow-[0_0_5px_currentColor]" />
                )}
            </button>
            <div className="flex-1 h-8 flex items-center gap-[2px] opacity-90 relative">
                {/* Fake Waveform Container */}
                {[...Array(18)].map((_, i) => (
                    <div
                        key={i}
                        className="w-1 rounded-full transition-all duration-300"
                        style={{
                            height: `${Math.random() * 80 + 20}%`,
                            backgroundColor: i * (100 / 18) <= progress ? chatColor : 'rgba(255,255,255,0.2)',
                            boxShadow: i * (100 / 18) <= progress ? `0 0 8px ${chatColor}` : 'none'
                        }}
                    />
                ))}
            </div>
            <span className="text-[10px] font-mono" style={{ color: isPlaying ? chatColor : 'rgba(255,255,255,0.5)' }}>
                {isPlaying ? `0:0${Math.floor(progress / 10)}` : msg.duration}
            </span>
        </div>
    );
}
