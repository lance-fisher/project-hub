import { memo } from 'react';
import { motion } from 'motion/react';
import type { BossState } from '../types';
import { BOSS_POSITION } from '../data/config';
import { Eye } from 'lucide-react';

const MODE_COLORS: Record<string, string> = {
  online: '#06b6d4', observing: '#3b82f6', dispatching: '#f59e0b',
  alert: '#ef4444', syncing: '#a855f7',
};

function BossCore3DInner({ boss }: { boss: BossState }) {
  const mc = MODE_COLORS[boss.mode] ?? '#06b6d4';

  return (
    <div style={{
      position: 'absolute',
      left: BOSS_POSITION.x, top: BOSS_POSITION.y,
      transform: 'translate(-50%, -50%)',
      transformStyle: 'preserve-3d',
      zIndex: 10,
    }}>
      {/* Pedestal glow */}
      <div style={{
        position: 'absolute', top: 30, left: '50%',
        width: 80, height: 40,
        transform: 'translateX(-50%) translateZ(0px) rotateX(90deg)',
        background: `radial-gradient(ellipse, ${mc}30 0%, ${mc}08 50%, transparent 70%)`,
        borderRadius: '50%',
      }} />

      {/* Vertical projection beam */}
      <motion.div
        animate={{ opacity: [0.1, 0.3, 0.1] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          position: 'absolute', top: -35, left: '50%',
          width: 2, height: 70,
          transform: 'translateX(-50%) translateZ(20px)',
          background: `linear-gradient(to top, ${mc}50, transparent)`,
        }}
      />

      {/* Secondary beams */}
      {[-12, 12].map(offset => (
        <motion.div
          key={offset}
          animate={{ opacity: [0.05, 0.15, 0.05] }}
          transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut', delay: Math.abs(offset) * 0.05 }}
          style={{
            position: 'absolute', top: -20, left: `calc(50% + ${offset}px)`,
            width: 1, height: 50,
            transform: 'translateZ(18px)',
            background: `linear-gradient(to top, ${mc}30, transparent)`,
          }}
        />
      ))}

      {/* Rotating core */}
      <motion.div
        animate={{ rotateY: 360 }}
        transition={{ duration: 12, repeat: Infinity, ease: 'linear' }}
        style={{
          transformStyle: 'preserve-3d',
          transform: 'translateZ(30px)',
          position: 'relative',
          width: 0, height: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}
      >
        {/* Diamond faces */}
        {[0, 60, 120].map(angle => (
          <motion.div
            key={angle}
            animate={boss.mode === 'dispatching' ? { opacity: [0.5, 1, 0.5] } : { opacity: 0.7 }}
            transition={{ duration: 0.6, repeat: boss.mode === 'dispatching' ? Infinity : 0 }}
            style={{
              position: 'absolute',
              width: 24, height: 24,
              background: `linear-gradient(135deg, ${mc}90, ${mc}30)`,
              border: `1px solid ${mc}cc`,
              transform: `rotateY(${angle}deg)`,
              boxShadow: `0 0 20px ${mc}50, inset 0 0 10px ${mc}20`,
            }}
          />
        ))}

        {/* Inner icon */}
        <div style={{
          position: 'absolute',
          transform: 'translateZ(13px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Eye size={12} color="white" style={{ filter: 'drop-shadow(0 0 6px white)' }} />
        </div>
      </motion.div>

      {/* Orbit ring 1 */}
      <motion.div
        animate={{ rotateZ: 360 }}
        transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
        style={{
          position: 'absolute', top: -22, left: -27,
          width: 54, height: 54,
          border: `1px solid ${mc}40`,
          borderRadius: '50%',
          transform: 'translateZ(30px) rotateX(70deg)',
        }}
      />

      {/* Orbit ring 2 */}
      <motion.div
        animate={{ rotateZ: -360 }}
        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
        style={{
          position: 'absolute', top: -32, left: -37,
          width: 74, height: 74,
          border: `1px dashed ${mc}25`,
          borderRadius: '50%',
          transform: 'translateZ(25px) rotateX(55deg) rotateY(20deg)',
        }}
      />

      {/* Orbit ring 3 */}
      <motion.div
        animate={{ rotateZ: 360 }}
        transition={{ duration: 25, repeat: Infinity, ease: 'linear' }}
        style={{
          position: 'absolute', top: -38, left: -43,
          width: 86, height: 86,
          border: '1px solid rgba(168,85,247,0.15)',
          borderRadius: '50%',
          transform: 'translateZ(28px) rotateX(80deg) rotateY(-15deg)',
        }}
      />

      {/* Energy pulse */}
      <motion.div
        animate={{ scale: [1, 1.6, 1], opacity: [0.25, 0, 0.25] }}
        transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
        style={{
          position: 'absolute', top: -12, left: -12,
          width: 24, height: 24, borderRadius: '50%',
          background: mc, filter: 'blur(8px)',
          transform: 'translateZ(30px)',
          pointerEvents: 'none',
        }}
      />

      {/* Boss label */}
      <div style={{
        position: 'absolute', top: 42, left: '50%',
        transform: 'translateX(-50%) translateZ(25px)',
        background: 'rgba(0,0,0,0.9)',
        border: `1.5px solid ${mc}`,
        borderRadius: 4, padding: '2px 10px',
        fontSize: 10, fontFamily: 'var(--font-mono)',
        fontWeight: 700, color: mc, whiteSpace: 'nowrap',
        boxShadow: `0 0 12px ${mc}40`,
        letterSpacing: '2px',
        textTransform: 'uppercase',
      }}>
        BOSS
      </div>

      {/* Mode indicator */}
      <div style={{
        position: 'absolute', top: 58, left: '50%',
        transform: 'translateX(-50%) translateZ(25px)',
        fontSize: 7, fontFamily: 'var(--font-mono)',
        color: `${mc}bb`, whiteSpace: 'nowrap',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}>
        {boss.mode}
      </div>
    </div>
  );
}

export const BossCore3D = memo(BossCore3DInner);
