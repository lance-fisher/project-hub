import { useState, useEffect, memo } from 'react';
import { motion, useMotionValue, useSpring } from 'motion/react';
import type { AgentType } from '../types';
import { GOVERNANCE_LABELS } from '../data/config';
import { Calendar, BarChart3, Code, Headphones, BookOpen, Network } from 'lucide-react';

const ICON_MAP: Record<string, React.ComponentType<{ size?: number; color?: string; style?: React.CSSProperties }>> = {
  Calendar, BarChart3, Code, Headphones, BookOpen, Network,
};

const SPRING = { stiffness: 80, damping: 15, mass: 0.5 };

const STATUS_COLORS: Record<string, string> = {
  idle: '#9ca3af', working: '#22c55e', collaborating: '#3b82f6', thinking: '#a855f7',
};

function Agent3DInner({ agent }: { agent: AgentType }) {
  const [hovered, setHovered] = useState(false);
  const [trail, setTrail] = useState<{ x: number; y: number }[]>([]);

  const targetX = useMotionValue(agent.position.x);
  const targetY = useMotionValue(agent.position.y);
  const x = useSpring(targetX, SPRING);
  const y = useSpring(targetY, SPRING);

  useEffect(() => { targetX.set(agent.position.x); }, [agent.position.x, targetX]);
  useEffect(() => { targetY.set(agent.position.y); }, [agent.position.y, targetY]);

  // Trail sampling
  useEffect(() => {
    const id = setInterval(() => {
      setTrail(prev => [...prev.slice(-14), { x: x.get(), y: y.get() }]);
    }, 100);
    return () => clearInterval(id);
  }, [x, y]);

  const Icon = ICON_MAP[agent.icon];
  const antennaColor = STATUS_COLORS[agent.status];
  const tier = GOVERNANCE_LABELS[agent.governanceTier];
  const isActive = agent.status === 'working' || agent.status === 'collaborating';

  return (
    <>
      {/* Trail dots */}
      {trail.map((pos, i) => (
        <div key={i} style={{
          position: 'absolute', left: pos.x - 1, top: pos.y - 1,
          width: 2, height: 2, borderRadius: '50%',
          background: agent.color,
          opacity: ((i + 1) / trail.length) * 0.5,
          transform: 'translateZ(2px)',
          pointerEvents: 'none',
        }} />
      ))}

      {/* Robot container */}
      <motion.div
        style={{ position: 'absolute', x, y, zIndex: hovered ? 20 : 5 }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      >
        <motion.div
          animate={{ scale: hovered ? 1.15 : 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 20 }}
          style={{
            transformStyle: 'preserve-3d',
            transform: 'translate(-50%, -50%)',
            cursor: 'pointer',
            position: 'relative',
          }}
        >
          {/* Shadow */}
          <div style={{
            position: 'absolute', bottom: -6, left: '50%',
            width: 30, height: 12, borderRadius: '50%',
            background: 'rgba(0,0,0,0.5)', filter: 'blur(4px)',
            transform: 'translateX(-50%) translateZ(-20px)',
          }} />

          {/* Glow aura */}
          {isActive && (
            <motion.div
              animate={{ scale: [1, 1.3, 1], opacity: [0.12, 0.35, 0.12] }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              style={{
                position: 'absolute', inset: -12,
                borderRadius: '50%', background: agent.color,
                filter: 'blur(10px)', transform: 'translateZ(5px)',
                pointerEvents: 'none',
              }}
            />
          )}

          {/* Antenna */}
          <div style={{
            position: 'absolute', top: -18, left: '50%',
            transform: 'translateX(-50%) translateZ(25px)',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
          }}>
            <div style={{ width: 1, height: 10, background: 'rgba(255,255,255,0.5)' }} />
            <motion.div
              animate={agent.status === 'thinking' ? { scale: [1, 1.4, 1] } : {}}
              transition={{ duration: 1, repeat: Infinity }}
              style={{
                width: 5, height: 5, borderRadius: '50%',
                background: antennaColor,
                boxShadow: `0 0 6px ${antennaColor}`,
              }}
            />
          </div>

          {/* Head */}
          <div style={{ transformStyle: 'preserve-3d', transform: 'translateZ(20px)', position: 'relative' }}>
            <div style={{
              width: 20, height: 16, borderRadius: 3,
              background: agent.color,
              border: '1.5px solid rgba(255,255,255,0.65)',
              display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 4,
              boxShadow: `0 0 8px ${agent.color}40`,
            }}>
              <div style={{ width: 4, height: 4, borderRadius: '50%', background: 'white', animation: 'blink 2.5s infinite' }} />
              <div style={{ width: 4, height: 4, borderRadius: '50%', background: 'white', animation: 'blink 2.5s infinite 0.1s' }} />
            </div>
            <div style={{
              position: 'absolute', top: 0, left: 0, width: 20, height: 4,
              background: agent.color, filter: 'brightness(1.3)',
              transform: 'rotateX(90deg)', transformOrigin: 'top', borderRadius: '3px 3px 0 0',
            }} />
            <div style={{
              position: 'absolute', top: 0, right: 0, width: 4, height: 16,
              background: agent.color, filter: 'brightness(0.7)',
              transform: 'rotateY(90deg)', transformOrigin: 'right', borderRadius: '0 3px 3px 0',
            }} />
          </div>

          {/* Body */}
          <div style={{ transformStyle: 'preserve-3d', transform: 'translateZ(15px)', position: 'relative', marginTop: 1 }}>
            <div style={{
              width: 24, height: 22, borderRadius: 4,
              background: agent.color,
              border: '1.5px solid rgba(255,255,255,0.65)',
              display: 'flex', justifyContent: 'center', alignItems: 'center',
              boxShadow: `0 0 12px ${agent.color}40`,
            }}>
              {Icon && <Icon size={12} color="white" style={{ filter: 'drop-shadow(0 0 3px white)' }} />}
            </div>
            <div style={{
              position: 'absolute', top: 0, left: 0, width: 24, height: 5,
              background: agent.color, filter: 'brightness(1.3)',
              transform: 'rotateX(90deg)', transformOrigin: 'top', borderRadius: '4px 4px 0 0',
            }} />
            <div style={{
              position: 'absolute', top: 0, right: 0, width: 5, height: 22,
              background: agent.color, filter: 'brightness(0.6)',
              transform: 'rotateY(90deg)', transformOrigin: 'right', borderRadius: '0 4px 4px 0',
            }} />
          </div>

          {/* Arms */}
          <div style={{ position: 'absolute', top: 20, left: -7, transform: 'translateZ(12px)' }}>
            <motion.div
              animate={agent.status === 'collaborating' ? { rotate: [-20, 20, -20] } : { rotate: 0 }}
              transition={{ duration: 0.7, repeat: agent.status === 'collaborating' ? Infinity : 0 }}
              style={{ width: 5, height: 12, borderRadius: 2, background: agent.color, filter: 'brightness(0.85)', transformOrigin: 'top' }}
            />
          </div>
          <div style={{ position: 'absolute', top: 20, right: -7, transform: 'translateZ(12px)' }}>
            <motion.div
              animate={agent.status === 'collaborating' ? { rotate: [20, -20, 20] } : { rotate: 0 }}
              transition={{ duration: 0.7, repeat: agent.status === 'collaborating' ? Infinity : 0 }}
              style={{ width: 5, height: 12, borderRadius: 2, background: agent.color, filter: 'brightness(0.85)', transformOrigin: 'top' }}
            />
          </div>

          {/* Legs */}
          <div style={{ display: 'flex', gap: 4, justifyContent: 'center', transform: 'translateZ(10px)' }}>
            <motion.div
              animate={agent.status === 'working' ? { scaleY: [1, 0.85, 1] } : {}}
              transition={{ duration: 0.5, repeat: agent.status === 'working' ? Infinity : 0 }}
              style={{ width: 5, height: 10, borderRadius: 2, background: agent.color, filter: 'brightness(0.75)', transformOrigin: 'top' }}
            />
            <motion.div
              animate={agent.status === 'working' ? { scaleY: [0.85, 1, 0.85] } : {}}
              transition={{ duration: 0.5, repeat: agent.status === 'working' ? Infinity : 0 }}
              style={{ width: 5, height: 10, borderRadius: 2, background: agent.color, filter: 'brightness(0.75)', transformOrigin: 'top' }}
            />
          </div>
        </motion.div>

        {/* Name tag */}
        <div style={{
          position: 'absolute', top: 52, left: '50%',
          transform: 'translateX(-50%) translateZ(25px)',
          background: 'rgba(0,0,0,0.85)',
          border: `1px solid ${agent.color}`,
          borderRadius: 3, padding: '1px 5px',
          fontSize: 9, fontFamily: 'var(--font-mono)',
          color: agent.color, whiteSpace: 'nowrap',
          boxShadow: `0 0 6px ${agent.color}40`,
        }}>
          {agent.name}
        </div>

        {/* Governance tier badge */}
        <div style={{
          position: 'absolute', top: 65, left: '50%',
          transform: 'translateX(-50%) translateZ(25px)',
          background: 'rgba(0,0,0,0.8)',
          border: `1px solid ${tier.color}`,
          borderRadius: 2, padding: '0px 3px',
          fontSize: 7, fontFamily: 'var(--font-mono)',
          color: tier.color, whiteSpace: 'nowrap',
          letterSpacing: '0.5px',
        }}>
          {tier.label}
        </div>

        {/* Hover task bubble */}
        {hovered && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              position: 'absolute', bottom: 60, left: '50%',
              transform: 'translateX(-50%) translateZ(40px)',
              background: 'rgba(0,0,0,0.92)',
              border: `1px solid ${agent.color}`,
              borderRadius: 6, padding: '6px 10px',
              minWidth: 140, textAlign: 'center',
              boxShadow: `0 0 15px ${agent.color}40`,
              pointerEvents: 'none',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 600, color: agent.color, fontFamily: 'var(--font-mono)' }}>
              {agent.role}
            </div>
            <div style={{ fontSize: 9, color: '#67e8f9', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
              {agent.currentTask}
            </div>
            <div style={{
              position: 'absolute', bottom: -5, left: '50%',
              transform: 'translateX(-50%) rotate(45deg)',
              width: 8, height: 8,
              background: 'rgba(0,0,0,0.92)',
              borderRight: `1px solid ${agent.color}`,
              borderBottom: `1px solid ${agent.color}`,
            }} />
          </motion.div>
        )}
      </motion.div>
    </>
  );
}

export const Agent3D = memo(Agent3DInner, (prev, next) =>
  prev.agent.position.x === next.agent.position.x &&
  prev.agent.position.y === next.agent.position.y &&
  prev.agent.status === next.agent.status &&
  prev.agent.currentTask === next.agent.currentTask
);
