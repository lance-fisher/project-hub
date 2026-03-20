import { memo } from 'react';
import { motion } from 'motion/react';
import type { AgentType, CollaborationPair } from '../types';
import { SYNC_CHAMBER, ROOM_WIDTH, ROOM_HEIGHT } from '../data/config';

// ─── Room Floor ─────────────────────────────────────────

export const RoomFloor = memo(function RoomFloor() {
  return (
    <>
      {/* Layer 1: Base floor */}
      <div style={{
        position: 'absolute', inset: 0,
        background: 'linear-gradient(135deg, #0f172a 0%, #000000 50%, #0f172a 100%)',
        transform: 'translateZ(-40px)',
        boxShadow: '0 30px 80px rgba(0,0,0,0.9)',
        borderRadius: 8,
      }} />

      {/* Layer 2: Cyber grid */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `
          linear-gradient(rgba(6,182,212,0.15) 1px, transparent 1px),
          linear-gradient(90deg, rgba(6,182,212,0.15) 1px, transparent 1px)
        `,
        backgroundSize: '40px 40px',
        animation: 'gridScroll 20s linear infinite',
        transform: 'translateZ(0px)',
        borderRadius: 8,
      }} />

      {/* Layer 3: Circuit overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'radial-gradient(circle, rgba(6,182,212,0.12) 1px, transparent 1px)',
        backgroundSize: '100px 100px',
        transform: 'translateZ(5px)',
        borderRadius: 8,
        pointerEvents: 'none',
      }} />

      {/* Scanline */}
      <div style={{
        position: 'absolute', inset: 0,
        overflow: 'hidden', transform: 'translateZ(6px)',
        borderRadius: 8, pointerEvents: 'none',
      }}>
        <div style={{
          width: '100%', height: 2,
          background: 'linear-gradient(90deg, transparent, rgba(6,182,212,0.08), transparent)',
          animation: 'scanline 8s linear infinite',
        }} />
      </div>

      {/* Room border */}
      <div style={{
        position: 'absolute', inset: 0,
        border: '1px solid rgba(6,182,212,0.2)',
        borderRadius: 8,
        boxShadow: 'inset 0 0 40px rgba(6,182,212,0.04)',
        transform: 'translateZ(1px)',
        pointerEvents: 'none',
      }} />
    </>
  );
});

// ─── Sync Chamber ──────────────────────────────────────

const MARKERS = [
  { x: -10, y: -10 }, { x: 110, y: -10 },
  { x: -10, y: 110 }, { x: 110, y: 110 },
];

export const SyncChamber = memo(function SyncChamber() {
  const size = SYNC_CHAMBER.radius * 2;
  return (
    <div style={{
      position: 'absolute',
      left: SYNC_CHAMBER.x - SYNC_CHAMBER.radius,
      top: SYNC_CHAMBER.y - SYNC_CHAMBER.radius,
      width: size, height: size,
      transform: 'translateZ(5px)',
      transformStyle: 'preserve-3d',
    }}>
      <motion.div
        animate={{ rotate: 360, scale: [1, 1.05, 1] }}
        transition={{
          rotate: { duration: 8, repeat: Infinity, ease: 'linear' },
          scale: { duration: 8, repeat: Infinity },
        }}
        style={{
          position: 'absolute', inset: 0,
          border: '2px dashed rgba(168,85,247,0.5)',
          borderRadius: '50%',
          boxShadow: '0 0 25px rgba(168,85,247,0.3)',
        }}
      />
      {MARKERS.map((m, i) => (
        <motion.div
          key={i}
          animate={{ opacity: [0.5, 1, 0.5], scale: [1, 1.3, 1] }}
          transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.2 }}
          style={{
            position: 'absolute',
            left: `${m.x}%`, top: `${m.y}%`,
            width: 6, height: 6, borderRadius: 2,
            background: '#a855f7',
            boxShadow: '0 0 8px rgba(168,85,247,0.6)',
            transform: 'translateZ(12px)',
          }}
        />
      ))}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        width: 30, height: 30, borderRadius: '50%',
        transform: 'translate(-50%, -50%)',
        background: 'radial-gradient(circle, rgba(168,85,247,0.25) 0%, transparent 70%)',
        filter: 'blur(4px)',
      }} />
      <div style={{
        position: 'absolute', bottom: -18, left: '50%',
        transform: 'translateX(-50%) translateZ(15px)',
        fontSize: 7, fontFamily: 'var(--font-mono)',
        color: 'rgba(168,85,247,0.6)',
        letterSpacing: '1px', textTransform: 'uppercase', whiteSpace: 'nowrap',
      }}>
        SYNC CHAMBER
      </div>
    </div>
  );
});

// ─── Collaboration Lines ────────────────────────────────

export function CollaborationLines({ pairs, agents }: { pairs: CollaborationPair[]; agents: AgentType[] }) {
  if (pairs.length === 0) return null;
  return (
    <svg style={{
      position: 'absolute', top: 0, left: 0,
      width: ROOM_WIDTH, height: ROOM_HEIGHT,
      transform: 'translateZ(18px)',
      pointerEvents: 'none', overflow: 'visible',
    }}>
      {pairs.map(pair => {
        const a1 = agents.find(a => a.id === pair.agent1Id);
        const a2 = agents.find(a => a.id === pair.agent2Id);
        if (!a1 || !a2) return null;
        return (
          <motion.line
            key={`${pair.agent1Id}-${pair.agent2Id}`}
            x1={a1.position.x} y1={a1.position.y}
            x2={a2.position.x} y2={a2.position.y}
            stroke={a1.color} strokeWidth={2.5} strokeDasharray="8 4"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.7 }}
            transition={{ duration: 0.8 }}
          />
        );
      })}
    </svg>
  );
}
