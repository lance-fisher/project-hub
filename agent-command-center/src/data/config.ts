import type { AgentType, BossState, WorkstationType, InfrastructureNodeType, SystemTelemetry, IntegrationState } from '../types';

export const INITIAL_AGENTS: AgentType[] = [
  { id: 'atlas', name: 'Atlas', role: 'Task Scheduler', color: '#3b82f6', icon: 'Calendar', position: { x: 150, y: 150 }, status: 'idle', currentTask: 'Coordinating project tasks', trail: [], governanceTier: 'tier1', workstationId: 'planning', lastUpdated: Date.now(), infrastructureAffinity: 'projecthub' },
  { id: 'sage', name: 'Sage', role: 'Data Analyst', color: '#10b981', icon: 'BarChart3', position: { x: 450, y: 200 }, status: 'idle', currentTask: 'Analyzing system metrics', trail: [], governanceTier: 'tier1', workstationId: 'analytics', lastUpdated: Date.now(), infrastructureAffinity: 'telemetry' },
  { id: 'cipher', name: 'Cipher', role: 'Code Auditor', color: '#8b5cf6', icon: 'Code', position: { x: 750, y: 180 }, status: 'idle', currentTask: 'Reviewing repository changes', trail: [], governanceTier: 'tier2', workstationId: 'code-terminal', lastUpdated: Date.now(), infrastructureAffinity: 'github-pipeline' },
  { id: 'echo', name: 'Echo', role: 'Comms Relay', color: '#f59e0b', icon: 'Headphones', position: { x: 250, y: 450 }, status: 'idle', currentTask: 'Monitoring communication queues', trail: [], governanceTier: 'tier1', workstationId: 'support', lastUpdated: Date.now(), infrastructureAffinity: 'communications' },
  { id: 'nova', name: 'Nova', role: 'Research Agent', color: '#ec4899', icon: 'BookOpen', position: { x: 550, y: 480 }, status: 'idle', currentTask: 'Gathering research insights', trail: [], governanceTier: 'tier1', workstationId: 'research', lastUpdated: Date.now(), infrastructureAffinity: 'ollama' },
  { id: 'nexus', name: 'Nexus', role: 'Orchestrator', color: '#06b6d4', icon: 'Network', position: { x: 800, y: 500 }, status: 'idle', currentTask: 'Optimizing task pipelines', trail: [], governanceTier: 'tier2', workstationId: 'command', lastUpdated: Date.now(), infrastructureAffinity: 'openclaw' },
];

export const WORKSTATIONS: WorkstationType[] = [
  { id: 'planning', name: 'Planning Station', type: 'Monitor', color: '#3b82f6', icon: 'Monitor', position: { x: 120, y: 120 } },
  { id: 'analytics', name: 'Analytics Hub', type: 'Database', color: '#10b981', icon: 'Database', position: { x: 420, y: 160 } },
  { id: 'code-terminal', name: 'Code Terminal', type: 'CPU', color: '#8b5cf6', icon: 'Cpu', position: { x: 720, y: 140 } },
  { id: 'support', name: 'Support Console', type: 'Server', color: '#f59e0b', icon: 'Server', position: { x: 220, y: 420 } },
  { id: 'research', name: 'Research Lab', type: 'Workflow', color: '#ec4899', icon: 'FlaskConical', position: { x: 520, y: 450 } },
  { id: 'command', name: 'Command Node', type: 'Radio', color: '#06b6d4', icon: 'Radio', position: { x: 770, y: 470 } },
];

export const INFRASTRUCTURE_NODES: InfrastructureNodeType[] = [
  { id: 'claude-code', label: 'Claude Code', type: 'claude-code', status: 'active', position: { x: 300, y: 100 }, linkedAgents: ['cipher'] },
  { id: 'openclaw', label: 'OpenClaw', type: 'openclaw', status: 'active', position: { x: 650, y: 350 }, linkedAgents: ['nexus'] },
  { id: 'ollama', label: 'Ollama', type: 'ollama', status: 'active', position: { x: 150, y: 350 }, linkedAgents: ['nova'] },
  { id: 'github', label: 'GitHub Pipeline', type: 'github-pipeline', status: 'idle', position: { x: 800, y: 300 }, linkedAgents: ['cipher'] },
  { id: 'projecthub', label: 'ProjectHub', type: 'projecthub', status: 'active', position: { x: 450, y: 550 }, linkedAgents: ['atlas'] },
];

export const INITIAL_BOSS: BossState = {
  mode: 'online',
  currentTask: 'Monitoring all systems',
  attentionTarget: null,
  supervisedAgents: ['atlas', 'sage', 'cipher', 'echo', 'nova', 'nexus'],
  queueDepth: 3,
  lastEvent: 'System initialized',
  securityState: 'Local Only',
};

export const DEFAULT_TASKS = [
  'Processing incoming requests',
  'Analyzing system metrics',
  'Optimizing workflows',
  'Reviewing documentation',
  'Coordinating tasks',
  'Gathering insights',
  'Synchronizing data',
  'Planning operations',
  'Monitoring performance',
  'Generating reports',
  'Scanning repositories',
  'Auditing security posture',
];

export const INITIAL_TELEMETRY: SystemTelemetry = {
  cpuUsage: 23,
  ramUsage: 48,
  gpuUsage: 12,
  vramUsage: 34,
  diskActivity: 8,
  networkState: 'local-only',
};

export const INITIAL_INTEGRATIONS: IntegrationState[] = [
  { id: 'claude-code', label: 'Claude Code', status: 'connected', color: '#06b6d4' },
  { id: 'ollama', label: 'Ollama', status: 'connected', color: '#22c55e' },
  { id: 'openclaw', label: 'OpenClaw', status: 'connected', color: '#3b82f6' },
  { id: 'github', label: 'GitHub', status: 'connected', color: '#8b5cf6' },
  { id: 'projecthub', label: 'ProjectHub', status: 'connected', color: '#f59e0b' },
  { id: 'auton', label: 'Auton', status: 'disconnected', color: '#ec4899' },
];

export const GOVERNANCE_LABELS: Record<string, { label: string; color: string }> = {
  tier1: { label: 'AUTO', color: '#22c55e' },
  tier2: { label: 'APPROVE', color: '#f59e0b' },
  tier3: { label: 'CONFIRM', color: '#ef4444' },
  tier4: { label: 'SECURE', color: '#dc2626' },
};

export const SYNC_CHAMBER = { x: 450, y: 350, radius: 50 };
export const BOSS_POSITION = { x: 450, y: 280 };
export const ROOM_WIDTH = 900;
export const ROOM_HEIGHT = 600;
