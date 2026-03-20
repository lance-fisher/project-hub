import { useRef, useState, useCallback } from 'react';
import { useMotionValue, useSpring, useTransform } from 'motion/react';

const SPRING_CONFIG = { stiffness: 100, damping: 30 };

export function useCamera() {
  const rotateXTarget = useMotionValue(60);
  const rotateZTarget = useMotionValue(-45);
  const zoomTarget = useMotionValue(1);

  const smoothRX = useSpring(rotateXTarget, SPRING_CONFIG);
  const smoothRZ = useSpring(rotateZTarget, SPRING_CONFIG);
  const smoothZoom = useSpring(zoomTarget, SPRING_CONFIG);

  const roomTransform = useTransform(
    [smoothRX, smoothRZ, smoothZoom],
    ([rx, rz, z]: number[]) => `rotateX(${rx}deg) rotateZ(${rz}deg) scale(${z})`
  );

  const [isDragging, setIsDragging] = useState(false);
  const [displayValues, setDisplayValues] = useState({ rx: 60, rz: -45, zoom: 100 });
  const lastPos = useRef({ x: 0, y: 0 });

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    setIsDragging(true);
    lastPos.current = { x: e.clientX, y: e.clientY };
    (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
  }, []);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!e.currentTarget.hasPointerCapture(e.pointerId)) return;
    const dx = e.clientX - lastPos.current.x;
    const dy = e.clientY - lastPos.current.y;
    lastPos.current = { x: e.clientX, y: e.clientY };

    const newRX = Math.max(20, Math.min(80, rotateXTarget.get() - dy * 0.3));
    const newRZ = rotateZTarget.get() - dx * 0.3;
    rotateXTarget.set(newRX);
    rotateZTarget.set(newRZ);
    setDisplayValues(prev => ({ ...prev, rx: Math.round(newRX), rz: Math.round(newRZ % 360) }));
  }, [rotateXTarget, rotateZTarget]);

  const onPointerUp = useCallback((e: React.PointerEvent) => {
    setIsDragging(false);
    if (e.currentTarget.hasPointerCapture(e.pointerId)) {
      (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
    }
  }, []);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const newZoom = Math.max(0.5, Math.min(1.5, zoomTarget.get() - e.deltaY * 0.001));
    zoomTarget.set(newZoom);
    setDisplayValues(prev => ({ ...prev, zoom: Math.round(newZoom * 100) }));
  }, [zoomTarget]);

  return {
    roomTransform,
    isDragging,
    displayValues,
    handlers: { onPointerDown, onPointerMove, onPointerUp, onWheel },
  };
}
