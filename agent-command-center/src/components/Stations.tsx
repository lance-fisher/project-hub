import { memo } from 'react';
import { motion } from 'motion/react';
import type { WorkstationType, InfrastructureNodeType } from '../types';
import {
  Monitor, Database, Cpu, Server, FlaskConical, Radio,
  Cloud, Bot, Brain, GitBranch, LayoutDashboard, Wifi,
} from 'lucide-react';

const WS_ICONS: Record<string, React.ComponentType<{ size?: number; color?: string }>> = {
  Monitor, Database, Cpu, Server, FlaskConical, Radio,
};

const INFRA_ICONS: Record<string, React.ComponentType<{ size?: number; color?: string }>> = {
  'claude-code': Cloud, 'openclaw': Bot, 'ollama': Brain,
  'github-pipeline': GitBranch, 'projecthub': LayoutDashboard,
  'telemetry': Wifi, 'local-bot': Bot, 'communications': Radio,
};

const INFRA_COLORS: Record<string, string> = {
  'claude-code': '#06b6d4', 'openclaw': '#3b82f6', 'ollama': '#22c55e',
  'github-pipeline': '#8b5cf6', 'projecthub': '#f59e0b',
  'telemetry': '#ec4899', 'local-bot': '#06b6d4', 'communications': '#f59e0b',
};

// ─── Workstation3D ──────────────────────────────────────

function Workstation3DInner({ station }: { station: WorkstationType }) {
  const Icon = WS_ICONS[station.icon];
  return (
    <div style={{
      position: 'absolute',
      left: station.position.x, top: station.position.y,
      transform: 'translate(-50%, -50%)',
      transformStyle: 'preserve-3d',
    }}>
      {/* Front face */}
      <motion.div
        animate={{ boxShadow: [`0 0 15px ${station.color}40`, `0 0 25px ${station.color}60`, `0 0 15px ${station.color}40`] }}
        transition={{ duration: 2, repeat: Infinity }}
        style={{
          width: 44, height: 44, borderRadius: 6,
          background: `${station.color}18`,
          border: `1.5px solid ${station.color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transform: 'translateZ(8px)',
          boxShadow: `0 0 20px ${station.color}40, inset 0 0 15px ${station.color}15`,
        }}
      >
        {Icon && <Icon size={20} color={station.color} />}
      </motion.div>

      {/* Top face */}
      <div style={{
        position: 'absolute', top: 0, left: 0,
        width: 44, height: 8,
        background: `${station.color}30`, filter: 'brightness(1.4)',
        transform: 'translateZ(8px) rotateX(90deg)', transformOrigin: 'top',
        borderRadius: '6px 6px 0 0',
      }} />

      {/* Side face */}
      <div style={{
        position: 'absolute', top: 0, right: 0,
        width: 8, height: 44,
        background: `${station.color}20`, filter: 'brightness(0.8)',
        transform: 'translateZ(8px) rotateY(90deg)', transformOrigin: 'right',
        borderRadius: '0 6px 6px 0',
      }} />

      {/* Label */}
      <div style={{
        position: 'absolute', top: 50, left: '50%',
        transform: 'translateX(-50%) translateZ(15px)',
        background: 'rgba(0,0,0,0.85)',
        border: `1px solid ${station.color}60`,
        borderRadius: 3, padding: '1px 6px',
        fontSize: 8, fontFamily: 'var(--font-mono)',
        color: station.color, whiteSpace: 'nowrap',
        boxShadow: `0 0 6px ${station.color}30`,
        letterSpacing: '0.3px',
      }}>
        {station.name}
      </div>

      {/* Point light */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        width: 60, height: 60, borderRadius: '50%',
        transform: 'translate(-50%, -50%) translateZ(2px)',
        background: `radial-gradient(circle, ${station.color}12 0%, transparent 70%)`,
        pointerEvents: 'none',
      }} />
    </div>
  );
}

export const Workstation3D = memo(Workstation3DInner);

// ─── InfrastructureNode3D ───────────────────────────────

function InfrastructureNode3DInner({ node }: { node: InfrastructureNodeType }) {
  const color = INFRA_COLORS[node.type] ?? '#06b6d4';
  const Icon = INFRA_ICONS[node.type];
  const isActive = node.status === 'active';

  return (
    <div style={{
      position: 'absolute',
      left: node.position.x, top: node.position.y,
      transform: 'translate(-50%, -50%)',
      transformStyle: 'preserve-3d',
    }}>
      {/* Diamond node */}
      <motion.div
        animate={isActive ? { scale: [1, 1.06, 1], opacity: [0.8, 1, 0.8] } : {}}
        transition={{ duration: 2.5, repeat: isActive ? Infinity : 0 }}
        style={{
          width: 26, height: 26,
          background: `${color}18`,
          border: `1px solid ${color}80`,
          borderRadius: 4,
          transform: 'translateZ(10px) rotate(45deg)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: isActive ? `0 0 12px ${color}40` : 'none',
        }}
      >
        <div style={{ transform: 'rotate(-45deg)' }}>
          {Icon && <Icon size={11} color={color} />}
        </div>
      </motion.div>

      {/* Label */}
      <div style={{
        position: 'absolute', top: 22, left: '50%',
        transform: 'translateX(-50%) translateZ(12px)',
        fontSize: 7, fontFamily: 'var(--font-mono)',
        color: `${color}bb`, whiteSpace: 'nowrap',
        letterSpacing: '0.3px',
      }}>
        {node.label}
      </div>

      {/* Active pulse */}
      {isActive && (
        <motion.div
          animate={{ scale: [1, 2, 1], opacity: [0.2, 0, 0.2] }}
          transition={{ duration: 2.5, repeat: Infinity }}
          style={{
            position: 'absolute', top: '50%', left: '50%',
            width: 16, height: 16, borderRadius: '50%',
            transform: 'translate(-50%, -50%) translateZ(8px)',
            background: color, filter: 'blur(5px)',
            pointerEvents: 'none',
          }}
        />
      )}
    </div>
  );
}

export const InfrastructureNode3D = memo(InfrastructureNode3DInner);
