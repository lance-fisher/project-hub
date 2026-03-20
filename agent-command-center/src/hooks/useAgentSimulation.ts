import { useState, useEffect, useRef, useCallback } from 'react';
import type { AgentType, BossState, CollaborationPair, ActivityLogEntry, SystemTelemetry, IntegrationState, InfrastructureMode } from '../types';
import { INITIAL_AGENTS, INITIAL_BOSS, WORKSTATIONS, DEFAULT_TASKS, INITIAL_TELEMETRY, INITIAL_INTEGRATIONS, SYNC_CHAMBER, ROOM_WIDTH, ROOM_HEIGHT } from '../data/config';
import { DataAdapterLayer } from '../data/adapters/DataAdapterLayer';

function clamp(v: number, min: number, max: number) { return Math.max(min, Math.min(max, v)); }
function uid() { return Math.random().toString(36).slice(2, 10); }

export function useAgentSimulation() {
  const [agents, setAgents] = useState<AgentType[]>(INITIAL_AGENTS);
  const [boss, setBoss] = useState<BossState>(INITIAL_BOSS);
  const [collaborationPairs, setCollaborationPairs] = useState<CollaborationPair[]>([]);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([
    { id: uid(), message: 'Neural Operations System initialized', timestamp: Date.now(), type: 'system', color: '#06b6d4' },
    { id: uid(), message: 'Boss overseer online. All agents reporting.', timestamp: Date.now() - 1000, type: 'system', color: '#06b6d4' },
  ]);
  const [telemetry, setTelemetry] = useState<SystemTelemetry>(INITIAL_TELEMETRY);
  const [integrations, setIntegrations] = useState<IntegrationState[]>(INITIAL_INTEGRATIONS);
  const [infraMode, setInfraMode] = useState<InfrastructureMode>('visual');

  const agentsRef = useRef(agents);
  useEffect(() => { agentsRef.current = agents; }, [agents]);

  const adapter = useRef(new DataAdapterLayer());

  const addLog = useCallback((message: string, type: ActivityLogEntry['type'], color?: string) => {
    setActivityLog(prev => [{ id: uid(), message, timestamp: Date.now(), type, color }, ...prev].slice(0, 50));
  }, []);

  // Agent movement interval
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => {
        if (agent.status === 'collaborating') return agent;
        if (Math.random() > 0.3) return agent;

        const station = WORKSTATIONS[Math.floor(Math.random() * WORKSTATIONS.length)];
        const tx = clamp(station.position.x + (Math.random() - 0.5) * 60, 80, ROOM_WIDTH - 80);
        const ty = clamp(station.position.y + (Math.random() - 0.5) * 60, 80, ROOM_HEIGHT - 80);

        // Collision avoidance
        let fx = tx, fy = ty;
        const others = prev.filter(a => a.id !== agent.id);
        for (let attempt = 0; attempt < 8; attempt++) {
          const tooClose = others.some(o => Math.hypot(o.position.x - fx, o.position.y - fy) < 40);
          if (!tooClose) break;
          const angle = (attempt / 8) * Math.PI * 2;
          const r = 30 + attempt * 8;
          fx = clamp(tx + Math.cos(angle) * r, 80, ROOM_WIDTH - 80);
          fy = clamp(ty + Math.sin(angle) * r, 80, ROOM_HEIGHT - 80);
        }

        const newTask = DEFAULT_TASKS[Math.floor(Math.random() * DEFAULT_TASKS.length)];
        const newStatus = Math.random() < 0.15 ? 'thinking' as const : 'working' as const;

        return { ...agent, position: { x: fx, y: fy }, status: newStatus, currentTask: newTask, workstationId: station.id, lastUpdated: Date.now() };
      }));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Collaboration interval
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.4) return;
      const current = agentsRef.current;
      const available = current.filter(a => a.status !== 'collaborating');
      if (available.length < 2) return;

      const shuffled = [...available].sort(() => Math.random() - 0.5);
      const [a1, a2] = [shuffled[0], shuffled[1]];

      setAgents(prev => prev.map(a => {
        if (a.id === a1.id) return { ...a, position: { x: SYNC_CHAMBER.x - 50, y: SYNC_CHAMBER.y }, status: 'collaborating' as const };
        if (a.id === a2.id) return { ...a, position: { x: SYNC_CHAMBER.x + 50, y: SYNC_CHAMBER.y }, status: 'collaborating' as const };
        return a;
      }));

      const pair: CollaborationPair = { agent1Id: a1.id, agent2Id: a2.id, startTime: Date.now() };
      setCollaborationPairs(prev => [...prev, pair]);
      addLog(`${a1.name} syncing with ${a2.name}`, 'collaboration', a1.color);

      setBoss(prev => ({ ...prev, mode: 'observing', attentionTarget: a1.id, lastEvent: `Observing ${a1.name}-${a2.name} sync` }));

      setTimeout(() => {
        setAgents(prev => prev.map(a => {
          if (a.id === a1.id || a.id === a2.id) return { ...a, status: 'idle' as const };
          return a;
        }));
        setCollaborationPairs(prev => prev.filter(p => !(p.agent1Id === a1.id && p.agent2Id === a2.id)));
        setBoss(prev => ({ ...prev, mode: 'online', attentionTarget: null }));
        addLog(`${a1.name} and ${a2.name} sync complete`, 'task', '#22c55e');
      }, 3500);
    }, 8000);
    return () => clearInterval(interval);
  }, [addLog]);

  // Boss ambient behavior
  useEffect(() => {
    const interval = setInterval(() => {
      const modes: BossState['mode'][] = ['online', 'observing', 'dispatching', 'syncing'];
      const mode = modes[Math.floor(Math.random() * modes.length)];
      const current = agentsRef.current;
      const target = Math.random() < 0.3 ? current[Math.floor(Math.random() * current.length)]?.id ?? null : null;
      setBoss(prev => ({
        ...prev,
        mode,
        attentionTarget: target,
        queueDepth: Math.max(0, prev.queueDepth + Math.floor(Math.random() * 5) - 2),
      }));
    }, 12000);
    return () => clearInterval(interval);
  }, []);

  // Data adapter polling
  useEffect(() => {
    const poll = async () => {
      const data = await adapter.current.fetchAll();
      if (data.systems) {
        const mapped = adapter.current.mapSystemsToIntegrations(data.systems);
        setIntegrations(prev => prev.map(i => ({ ...i, status: mapped[i.id] ?? i.status })));
      }
      setTelemetry(adapter.current.generateSimulatedTelemetry());
    };
    poll();
    const interval = setInterval(poll, 15000);
    return () => clearInterval(interval);
  }, []);

  // Idle reset for agents stuck as working
  useEffect(() => {
    const interval = setInterval(() => {
      setAgents(prev => prev.map(a => {
        if (a.status === 'working' && Date.now() - a.lastUpdated > 8000 && Math.random() < 0.5) {
          return { ...a, status: 'idle' };
        }
        return a;
      }));
    }, 6000);
    return () => clearInterval(interval);
  }, []);

  const dispatchCommand = useCallback((command: string, targetAgentId?: string) => {
    addLog(`Command dispatched: ${command}${targetAgentId ? ` -> ${targetAgentId}` : ''}`, 'dispatch', '#f59e0b');
    setBoss(prev => ({ ...prev, mode: 'dispatching', lastEvent: command }));
    if (targetAgentId) {
      setAgents(prev => prev.map(a => a.id === targetAgentId ? { ...a, status: 'working' as const, currentTask: command } : a));
    }
    setTimeout(() => setBoss(prev => ({ ...prev, mode: 'online' })), 2000);
  }, [addLog]);

  return { agents, boss, collaborationPairs, activityLog, telemetry, integrations, infraMode, setInfraMode, dispatchCommand };
}
