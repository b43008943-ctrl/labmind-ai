import React, { createContext, useContext, useState } from 'react';

const LearningContext = createContext();

export function LearningProvider({ children }) {
    const [isLearningMode, setIsLearningMode] = useState(false);

    return (
        <LearningContext.Provider value={{ isLearningMode, setIsLearningMode }}>
            {children}
        </LearningContext.Provider>
    );
}

export function useLearningMode() {
    return useContext(LearningContext);
}
