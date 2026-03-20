import type { SystemTelemetry, IntegrationState } from '../../types';

interface SystemsResponse {
  ollama?: { status: string };
  openclaw?: { status: string };
  auton?: { status: string };
  home_hub?: { status: string };
  [key: string]: unknown;
}

export class DataAdapterLayer {
  private baseUrl: string;

  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  async fetchSystems(): Promise<SystemsResponse | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/systems`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  async fetchProjects(): Promise<unknown[] | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/projects`);
      if (!res.ok) return null;
      const data = await res.json();
      return data.projects ?? data;
    } catch {
      return null;
    }
  }

  async fetchStats(): Promise<Record<string, number> | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/stats`);
      if (!res.ok) return null;
      return await res.json();
    } catch {
      return null;
    }
  }

  async fetchActiveSessions(): Promise<unknown[] | null> {
    try {
      const res = await fetch(`${this.baseUrl}/api/active-sessions`);
      if (!res.ok) return null;
      const data = await res.json();
      return data.sessions ?? [];
    } catch {
      return null;
    }
  }

  mapSystemsToIntegrations(systems: SystemsResponse | null): Partial<Record<string, IntegrationState['status']>> {
    if (!systems) return {};
    const map: Partial<Record<string, IntegrationState['status']>> = {};
    if (systems.ollama) map['ollama'] = systems.ollama.status === 'online' ? 'connected' : 'disconnected';
    if (systems.openclaw) map['openclaw'] = systems.openclaw.status === 'online' ? 'connected' : 'disconnected';
    if (systems.auton) map['auton'] = systems.auton.status === 'online' ? 'connected' : 'disconnected';
    return map;
  }

  generateSimulatedTelemetry(): SystemTelemetry {
    return {
      cpuUsage: Math.round(15 + Math.random() * 40),
      ramUsage: Math.round(35 + Math.random() * 30),
      gpuUsage: Math.round(5 + Math.random() * 25),
      vramUsage: Math.round(20 + Math.random() * 40),
      diskActivity: Math.round(2 + Math.random() * 15),
      networkState: 'local-only',
    };
  }

  async fetchAll() {
    const [systems, projects, stats, sessions] = await Promise.allSettled([
      this.fetchSystems(),
      this.fetchProjects(),
      this.fetchStats(),
      this.fetchActiveSessions(),
    ]);
    return {
      systems: systems.status === 'fulfilled' ? systems.value : null,
      projects: projects.status === 'fulfilled' ? projects.value : null,
      stats: stats.status === 'fulfilled' ? stats.value : null,
      sessions: sessions.status === 'fulfilled' ? sessions.value : null,
    };
  }
}
