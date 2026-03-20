import { memo, useState } from 'react';
import { motion } from 'motion/react';
import type { AgentType, SystemTelemetry } from '../types';
import { Cpu, HardDrive, Gauge, Send, Pause, Play, Eye, RefreshCw, Terminal, List, Zap } from 'lucide-react';

// ─── Telemetry Panel ──────────────────────────────────────

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
      <span style={{ fontSize: 7, fontFamily: 'var(--font-mono)', color: 'rgba(6,182,212,0.5)', width: 30, textAlign: 'right' }}>{label}</span>
      <div style={{ flex: 1, height: 3, background: 'rgba(255,255,255,0.05)', borderRadius: 2, overflow: 'hidden' }}>
        <motion.div
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8 }}
          style={{
            height: '100%',
            background: `linear-gradient(90deg, ${color}80, ${color})`,
            borderRadius: 2,
            boxShadow: `0 0 4px ${color}30`,
          }}
        />
      </div>
      <span style={{ fontSize: 7, fontFamily: 'var(--font-mono)', color, width: 22, textAlign: 'right' }}>{value}%</span>
    </div>
  );
}

function TelemetryPanelInner({ telemetry }: { telemetry: SystemTelemetry }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.6)',
      border: '1px solid rgba(6,182,212,0.2)',
      borderRadius: 12, padding: 10,
      backdropFilter: 'blur(8px)',
    }}>
      <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'rgba(6,182,212,0.45)', marginBottom: 5, letterSpacing: '1px' }}>
        SYSTEM TELEMETRY
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <MetricBar label="CPU" value={telemetry.cpuUsage} color="#06b6d4" />
        <MetricBar label="RAM" value={telemetry.ramUsage} color="#3b82f6" />
        <MetricBar label="GPU" value={telemetry.gpuUsage} color="#22c55e" />
        <MetricBar label="VRAM" value={telemetry.vramUsage} color="#a855f7" />
        <MetricBar label="DISK" value={telemetry.diskActivity} color="#f59e0b" />
      </div>
      <div style={{
        marginTop: 5, paddingTop: 5, borderTop: '1px solid rgba(6,182,212,0.08)',
        display: 'flex', alignItems: 'center', gap: 4,
      }}>
        <div style={{
          width: 4, height: 4, borderRadius: '50%',
          background: telemetry.networkState === 'connected' ? '#22c55e' : '#f59e0b',
          boxShadow: `0 0 3px ${telemetry.networkState === 'connected' ? '#22c55e' : '#f59e0b'}`,
        }} />
        <span style={{ fontSize: 7, fontFamily: 'var(--font-mono)', color: 'rgba(6,182,212,0.5)', textTransform: 'uppercase' }}>
          {telemetry.networkState}
        </span>
      </div>
    </div>
  );
}

export const TelemetryPanel = memo(TelemetryPanelInner);

// ─── Command Panel ────────────────────────────────────────

const COMMANDS = [
  { id: 'dispatch', label: 'Dispatch', icon: Send },
  { id: 'pause', label: 'Pause', icon: Pause },
  { id: 'resume', label: 'Resume', icon: Play },
  { id: 'inspect', label: 'Inspect', icon: Eye },
  { id: 'sync', label: 'Sync', icon: RefreshCw },
  { id: 'escalate', label: 'Escalate', icon: Zap },
  { id: 'logs', label: 'Logs', icon: Terminal },
  { id: 'queue', label: 'Queue', icon: List },
];

interface CommandPanelProps {
  agents: AgentType[];
  onCommand: (command: string, agentId?: string) => void;
}

function CommandPanelInner({ agents, onCommand }: CommandPanelProps) {
  const [selected, setSelected] = useState<string>('');

  return (
    <div style={{
      background: 'rgba(0,0,0,0.6)',
      border: '1px solid rgba(6,182,212,0.2)',
      borderRadius: 12, padding: 10,
      backdropFilter: 'blur(8px)',
    }}>
      <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'rgba(6,182,212,0.45)', marginBottom: 5, letterSpacing: '1px' }}>
        COMMAND CENTER
      </div>

      {/* Agent selector */}
      <select
        value={selected}
        onChange={e => setSelected(e.target.value)}
        style={{
          width: '100%', padding: '3px 5px', marginBottom: 5,
          background: 'rgba(0,0,0,0.5)',
          border: '1px solid rgba(6,182,212,0.25)',
          borderRadius: 4, color: '#67e8f9',
          fontSize: 8, fontFamily: 'var(--font-mono)',
          outline: 'none',
        }}
      >
        <option value="">All Agents</option>
        {agents.map(a => (
          <option key={a.id} value={a.id}>{a.name} — {a.role}</option>
        ))}
      </select>

      {/* Command grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 3 }}>
        {COMMANDS.map(cmd => (
          <motion.button
            key={cmd.id}
            whileHover={{ scale: 1.04, borderColor: '#06b6d4' }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onCommand(cmd.label, selected || undefined)}
            style={{
              display: 'flex', alignItems: 'center', gap: 3,
              padding: '3px 5px',
              background: 'rgba(6,182,212,0.05)',
              border: '1px solid rgba(6,182,212,0.18)',
              borderRadius: 4, cursor: 'pointer',
              fontSize: 7, fontFamily: 'var(--font-mono)',
              color: '#67e8f9',
            }}
          >
            <cmd.icon size={9} color="#06b6d4" />
            {cmd.label}
          </motion.button>
        ))}
      </div>

      {/* Security state footer */}
      <div style={{
        marginTop: 6, paddingTop: 5, borderTop: '1px solid rgba(6,182,212,0.08)',
        display: 'flex', flexWrap: 'wrap', gap: 4,
      }}>
        {['LOCAL MODE', 'SANDBOXED', 'TRUSTED'].map(badge => (
          <span key={badge} style={{
            fontSize: 6, fontFamily: 'var(--font-mono)',
            color: '#22c55e', letterSpacing: '0.5px',
            background: 'rgba(34,197,94,0.08)',
            border: '1px solid rgba(34,197,94,0.2)',
            borderRadius: 2, padding: '1px 4px',
          }}>
            {badge}
          </span>
        ))}
      </div>
    </div>
  );
}

export const CommandPanel = memo(CommandPanelInner);
