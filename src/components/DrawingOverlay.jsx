import React, { useRef, useEffect } from 'react';

export const DrawingOverlay = ({ isDrawingMode, color = '#00e5ff', lineWidth = 3 }) => {
    const canvasRef = useRef(null);
    const isDrawing = useRef(false);
    const lastPos = useRef({ x: 0, y: 0 });

    // 1. THE RESOLUTION FIX (CRITICAL)
    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        // Force internal resolution to match CSS pixel size
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;

        const ctx = canvas.getContext('2d');
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
    }, [isDrawingMode]); // Sync size when mode changes

    // 2. THE COORDINATE FIX (BULLETPROOF MATH)
    const getCoordinates = (e) => {
        const canvas = canvasRef.current;
        const rect = canvas.getBoundingClientRect();
        return {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
    };

    const startDrawing = (e) => {
        if (!isDrawingMode) return;
        isDrawing.current = true;
        lastPos.current = getCoordinates(e);
        e.target.setPointerCapture(e.pointerId);
    };

    const draw = (e) => {
        if (!isDrawing.current || !isDrawingMode) return;
        const ctx = canvasRef.current.getContext('2d');
        const currentPos = getCoordinates(e);

        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;

        ctx.beginPath();
        ctx.moveTo(lastPos.current.x, lastPos.current.y);
        ctx.lineTo(currentPos.x, currentPos.y);
        ctx.stroke();

        lastPos.current = currentPos;
    };

    const stopDrawing = (e) => {
        isDrawing.current = false;
        e.target.releasePointerCapture(e.pointerId);
    };

    return (
        <canvas
            ref={canvasRef}
            onPointerDown={startDrawing}
            onPointerMove={draw}
            onPointerUp={stopDrawing}
            onPointerCancel={stopDrawing}
            className={`absolute inset-0 z-[100] w-full h-full touch-none transition-all ${isDrawingMode ? 'pointer-events-auto cursor-crosshair' : 'pointer-events-none'
                }`}
        />
    );
};
