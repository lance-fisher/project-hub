export type AgentStatus = 'idle' | 'working' | 'collaborating' | 'thinking';
export type GovernanceTier = 'tier1' | 'tier2' | 'tier3' | 'tier4';
export type BossMode = 'online' | 'observing' | 'dispatching' | 'alert' | 'syncing';
export type InfrastructureType = 'claude-code' | 'openclaw' | 'ollama' | 'local-bot' | 'github-pipeline' | 'projecthub' | 'telemetry' | 'communications';
export type InfrastructureStatus = 'idle' | 'active' | 'warning' | 'offline';
export type InfrastructureMode = 'visual' | 'live' | 'infrastructure-map' | 'hybrid';

export interface Position { x: number; y: number; }

export interface AgentType {
  id: string;
  name: string;
  role: string;
  color: string;
  icon: string;
  position: Position;
  status: AgentStatus;
  currentTask: string;
  trail: Position[];
  governanceTier: GovernanceTier;
  workstationId: string;
  sourceState?: string;
  lastUpdated: number;
  infrastructureAffinity?: string;
}

export interface BossState {
  mode: BossMode;
  currentTask: string;
  attentionTarget: string | null;
  supervisedAgents: string[];
  queueDepth: number;
  lastEvent: string;
  securityState: string;
}

export interface InfrastructureNodeType {
  id: string;
  label: string;
  type: InfrastructureType;
  status: InfrastructureStatus;
  position: Position;
  linkedAgents: string[];
  metadata?: Record<string, unknown>;
}

export interface WorkstationType {
  id: string;
  name: string;
  type: string;
  color: string;
  icon: string;
  position: Position;
}

export interface CollaborationPair {
  agent1Id: string;
  agent2Id: string;
  startTime: number;
}

export interface ActivityLogEntry {
  id: string;
  message: string;
  timestamp: number;
  type: 'system' | 'collaboration' | 'task' | 'error' | 'dispatch' | 'security' | 'infrastructure';
  agentId?: string;
  color?: string;
}

export interface SystemTelemetry {
  cpuUsage: number;
  ramUsage: number;
  gpuUsage: number;
  vramUsage: number;
  diskActivity: number;
  networkState: 'connected' | 'local-only' | 'offline';
}

export interface IntegrationState {
  id: string;
  label: string;
  status: 'connected' | 'disconnected' | 'unknown';
  color: string;
}
