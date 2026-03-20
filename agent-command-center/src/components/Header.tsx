import { memo } from 'react';
import type { AgentType, BossState, InfrastructureMode } from '../types';
import { Zap } from 'lucide-react';

interface HeaderProps {
  agents: AgentType[];
  boss: BossState;
  infraMode: InfrastructureMode;
}

const MODE_COLORS: Record<string, string> = {
  online: '#06b6d4', observing: '#3b82f6', dispatching: '#f59e0b',
  alert: '#ef4444', syncing: '#a855f7',
};

function StatusCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div style={{
      background: 'rgba(0,0,0,0.8)',
      border: `1px solid ${color}40`,
      borderRadius: 8, padding: '5px 10px',
      backdropFilter: 'blur(8px)',
      boxShadow: `0 0 8px ${color}15`,
      minWidth: 70, textAlign: 'center',
    }}>
      <div style={{
        fontSize: 8, fontFamily: 'var(--font-mono)',
        color: `${color}90`, letterSpacing: '0.5px', textTransform: 'uppercase',
      }}>
        {label}
      </div>
      <div style={{
        fontSize: 14, fontWeight: 700, fontFamily: 'var(--font-mono)',
        color, marginTop: 1,
      }}>
        {value}
      </div>
    </div>
  );
}

function HeaderInner({ agents, boss, infraMode }: HeaderProps) {
  const working = agents.filter(a => a.status === 'working' || a.status === 'collaborating').length;
  const bossColor = MODE_COLORS[boss.mode] ?? '#06b6d4';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '6px 14px',
      background: 'rgba(0,0,0,0.65)',
      borderBottom: '1px solid rgba(6,182,212,0.2)',
      backdropFilter: 'blur(12px)',
      boxShadow: '0 2px 20px rgba(6,182,212,0.06)',
      flexShrink: 0,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Zap size={18} color="#06b6d4" style={{ filter: 'drop-shadow(0 0 4px #06b6d4)' }} />
        <div>
          <div style={{
            fontSize: 15, fontWeight: 700,
            background: 'linear-gradient(90deg, #06b6d4, #3b82f6)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            fontFamily: 'var(--font-mono)',
          }}>
            ProjectHub Agent Command Center
          </div>
          <div style={{
            fontSize: 9, color: 'rgba(103,232,249,0.5)', fontFamily: 'var(--font-mono)',
          }}>
            Neural Operations Monitoring System
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <StatusCard label="Active" value={agents.length} color="#06b6d4" />
        <StatusCard label="Working" value={working} color="#22c55e" />
        <StatusCard label="Boss" value={boss.mode.toUpperCase()} color={bossColor} />
        <StatusCard label="Queue" value={boss.queueDepth} color="#a855f7" />
        <StatusCard label="Security" value="LOCAL" color="#22c55e" />
        <StatusCard label="Mode" value={infraMode.toUpperCase()} color="#3b82f6" />
      </div>
    </div>
  );
}

export const Header = memo(HeaderInner);
