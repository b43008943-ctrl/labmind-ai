/* TrendingTab — Hashtag trending list */

import { motion } from 'framer-motion';
import { Flame, TrendingUp } from 'lucide-react';
import { TRENDING_TOPICS } from './communityData';

export default function TrendingTab() {
    return (
        <motion.div key="tab-trending" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="flex flex-col gap-3 pt-2">
            <h3 className="text-[10px] font-bold tracking-[0.25em] uppercase text-white/30 mb-1">🔥 Trending Now</h3>
            {TRENDING_TOPICS.map((topic, idx) => (
                <motion.div
                    key={idx}
                    initial={{ opacity: 0, y: 15 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.08 }}
                    className="flex items-center justify-between p-3.5 rounded-xl cursor-pointer"
                    style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(0,240,255,0.04)'; e.currentTarget.style.borderColor = 'rgba(0,240,255,0.15)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.02)'; e.currentTarget.style.borderColor = 'rgba(255,255,255,0.05)'; }}
                >
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(0,240,255,0.08)', border: '1px solid rgba(0,240,255,0.15)' }}>
                            <Flame size={14} color="#00F0FF" />
                        </div>
                        <div>
                            <p className="text-[13px] font-bold text-white/80">{topic.tag}</p>
                            <p className="text-[10px] text-white/30">{topic.posts} posts</p>
                        </div>
                    </div>
                    {topic.trend === 'up' && <TrendingUp size={14} color="#10B981" />}
                </motion.div>
            ))}
        </motion.div>
    );
}
