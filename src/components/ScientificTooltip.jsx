import React from 'react';
import { useLearningMode } from '../context/LearningContext';

export default function ScientificTooltip({ text, children, className = '' }) {
    const { isLearningMode } = useLearningMode();

    return (
        <div className={`relative group inline-block ${className}`}>
            {children}
            {isLearningMode && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block z-50 bg-[#0f172a] text-blue-200 text-[10px] md:text-xs p-2 rounded border border-blue-500/50 shadow-xl max-w-xs w-max pointer-events-none">
                    {text}
                </div>
            )}
        </div>
    );
}
