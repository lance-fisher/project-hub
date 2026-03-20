import { memo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import type { AgentType, BossState, ActivityLogEntry, IntegrationState } from '../types';
import { Activity } from 'lucide-react';

const STATUS_KEY = [
  { label: 'WORKING', color: '#22c55e' },
  { label: 'SYNCING', color: '#3b82f6' },
  { label: 'THINKING', color: '#a855f7' },
  { label: 'IDLE', color: '#9ca3af' },
];

function ts(t: number) {
  return new Date(t).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

interface Props {
  activityLog: ActivityLogEntry[];
  agents: AgentType[];
  boss: BossState;
  integrations: IntegrationState[];
}

function ActivityPanelInner({ activityLog, agents, boss, integrations }: Props) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: 8,
      background: 'rgba(0,0,0,0.6)',
      border: '1px solid rgba(6,182,212,0.2)',
      borderRadius: 12, padding: 10,
      backdropFilter: 'blur(8px)',
      overflow: 'hidden', flex: 1,
    }}>
      {/* System Log */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingBottom: 6, borderBottom: '1px solid rgba(6,182,212,0.12)' }}>
        <Activity size={13} color="#06b6d4" />
        <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#06b6d4', letterSpacing: '0.5px' }}>
          SYSTEM LOG
        </span>
      </div>

      <div style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column', gap: 2, maxHeight: 150 }}>
        <AnimatePresence initial={false}>
          {activityLog.slice(0, 15).map(entry => (
            <motion.div
              key={entry.id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.25 }}
              style={{
                background: 'rgba(0,0,0,0.35)',
                border: '1px solid rgba(6,182,212,0.08)',
                borderRadius: 3, padding: '2px 5px',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              }}
            >
              <span style={{ fontSize: 8, fontFamily: 'var(--font-mono)', color: entry.color ?? '#67e8f9', flex: 1 }}>
                {entry.message}
              </span>
              <span style={{ fontSize: 7, fontFamily: 'var(--font-mono)', color: 'rgba(6,182,212,0.35)', marginLeft: 4, whiteSpace: 'nowrap' }}>
                {ts(entry.timestamp)}
              </span>
            </motion.div>
          ))}
        </AnimatePresence>
        {activityLog.length === 0 && (
          <div style={{ fontSize: 9, fontFamily: 'var(--font-mono)', color: 'rgba(6,182,212,0.25)', textAlign: 'center', padding: 12 }}>
            Monitoring neural activity...
          </div>
        )}
      </div>

      {/* Agent Roster */}
      <div style={{ borderTop: '1px solid rgba(6,182,212,0.12)', paddingTop: 6 }}>
        <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'rgba(6,182,212,0.45)', marginBottom: 3, letterSpacing: '1px' }}>
          AGENT ROSTER
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {agents.map(a => (
            <div key={a.id} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 8, fontFamily: 'var(--font-mono)' }}>
              <motion.div
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 2, repeat: Infinity }}
                style={{ width: 4, height: 4, borderRadius: '50%', background: a.color, boxShadow: `0 0 4px ${a.color}`, flexShrink: 0 }}
              />
              <span style={{ color: a.color, fontWeight: 500, width: 40 }}>{a.name}</span>
              <span style={{ color: 'rgba(6,182,212,0.4)', flex: 1 }}>{a.role}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Status Key */}
      <div style={{ borderTop: '1px solid rgba(6,182,212,0.12)', paddingTop: 6 }}>
        <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'rgba(6,182,212,0.45)', marginBottom: 3, letterSpacing: '1px' }}>
          STATUS KEY
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1 }}>
          {STATUS_KEY.map(s => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: 7, fontFamily: 'var(--font-mono)' }}>
              <div style={{ width: 4, height: 4, borderRadius: '50%', background: s.color, boxShadow: `0 0 3px ${s.color}`, animation: 'pulseDot 2s infinite' }} />
              <span style={{ color: s.color }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Boss Section */}
      <div style={{ borderTop: '1px solid rgba(6,182,212,0.12)', paddingTop: 6 }}>
        <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'rgba(6,182,212,0.45)', marginBottom: 3, letterSpacing: '1px' }}>
          BOSS OVERSEER
        </div>
        <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', display: 'flex', flexDirection: 'column', gap: 1 }}>
          <div><span style={{ color: 'rgba(6,182,212,0.4)' }}>Mode: </span><span style={{ color: '#06b6d4' }}>{boss.mode.toUpperCase()}</span></div>
          <div><span style={{ color: 'rgba(6,182,212,0.4)' }}>Agents: </span><span style={{ color: '#22c55e' }}>{boss.supervisedAgents.length}</span></div>
          <div><span style={{ color: 'rgba(6,182,212,0.4)' }}>Event: </span><span style={{ color: '#67e8f9' }}>{boss.lastEvent}</span></div>
          {boss.attentionTarget && (
            <div><span style={{ color: 'rgba(6,182,212,0.4)' }}>Focus: </span><span style={{ color: '#f59e0b' }}>{boss.attentionTarget}</span></div>
          )}
        </div>
      </div>

      {/* Integrations */}
      <div style={{ borderTop: '1px solid rgba(6,182,212,0.12)', paddingTop: 6 }}>
        <div style={{ fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'rgba(6,182,212,0.45)', marginBottom: 3, letterSpacing: '1px' }}>
          INTEGRATIONS
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {integrations.map(i => (
            <div key={i.id} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 7, fontFamily: 'var(--font-mono)' }}>
              <div style={{
                width: 4, height: 4, borderRadius: '50%',
                background: i.status === 'connected' ? i.color : '#4b5563',
                boxShadow: i.status === 'connected' ? `0 0 3px ${i.color}` : 'none',
              }} />
              <span style={{ color: i.status === 'connected' ? i.color : '#6b7280', width: 65 }}>{i.label}</span>
              <span style={{ color: i.status === 'connected' ? '#22c55e' : '#ef4444', fontSize: 6 }}>
                {i.status === 'connected' ? 'ONLINE' : 'OFFLINE'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export const ActivityPanel = memo(ActivityPanelInner);
