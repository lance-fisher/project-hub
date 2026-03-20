import { motion } from 'motion/react';
import { useCamera } from '../hooks/useCamera';
import { useAgentSimulation } from '../hooks/useAgentSimulation';
import { WORKSTATIONS, INFRASTRUCTURE_NODES, ROOM_WIDTH, ROOM_HEIGHT } from '../data/config';
import { Header } from './Header';
import { RoomFloor, SyncChamber, CollaborationLines } from './SceneElements';
import { Agent3D } from './Agent3D';
import { BossCore3D } from './BossCore3D';
import { Workstation3D, InfrastructureNode3D } from './Stations';
import { ActivityPanel } from './ActivityPanel';
import { TelemetryPanel, CommandPanel } from './ControlPanels';

export default function AgentRoom3D() {
  const { roomTransform, isDragging, displayValues, handlers } = useCamera();
  const {
    agents, boss, collaborationPairs, activityLog,
    telemetry, integrations, infraMode, dispatchCommand,
  } = useAgentSimulation();

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100vh', width: '100vw',
      background: 'linear-gradient(180deg, #000000 0%, #0a0c10 40%, #0f172a 100%)',
      overflow: 'hidden',
    }}>
      <Header agents={agents} boss={boss} infraMode={infraMode} />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* ─── 3D Scene Area ─── */}
        <div
          onPointerDown={handlers.onPointerDown}
          onPointerMove={handlers.onPointerMove}
          onPointerUp={handlers.onPointerUp}
          onWheel={handlers.onWheel}
          style={{
            flex: 1, position: 'relative', overflow: 'hidden',
            cursor: isDragging ? 'grabbing' : 'grab',
            touchAction: 'none',
          }}
        >
          {/* Camera stats overlay */}
          <div style={{
            position: 'absolute', top: 8, left: 8, zIndex: 30,
            background: 'rgba(0,0,0,0.7)',
            border: '1px solid rgba(6,182,212,0.15)',
            borderRadius: 6, padding: '3px 8px',
            fontSize: 9, fontFamily: 'var(--font-mono)',
            color: 'rgba(6,182,212,0.5)',
            opacity: isDragging ? 0.4 : 1,
            transition: 'opacity 0.2s',
            display: 'flex', gap: 10,
            userSelect: 'none',
          }}>
            <span>X: {displayValues.rx}°</span>
            <span>Z: {displayValues.rz}°</span>
            <span>Zoom: {displayValues.zoom}%</span>
          </div>

          {/* Control hint */}
          <div style={{
            position: 'absolute', bottom: 8, left: '50%',
            transform: 'translateX(-50%)', zIndex: 30,
            fontSize: 9, fontFamily: 'var(--font-mono)',
            color: 'rgba(6,182,212,0.25)',
            opacity: isDragging ? 0.2 : 0.5,
            transition: 'opacity 0.2s',
            userSelect: 'none',
          }}>
            Drag to Rotate &middot; Scroll to Zoom
          </div>

          {/* Perspective container */}
          <div style={{
            width: '100%', height: '100%',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            perspective: 1500,
          }}>
            {/* Room */}
            <motion.div style={{
              width: ROOM_WIDTH, height: ROOM_HEIGHT,
              position: 'relative',
              transformStyle: 'preserve-3d',
              transform: roomTransform,
              willChange: 'transform',
            }}>
              <RoomFloor />

              {WORKSTATIONS.map(ws => (
                <Workstation3D key={ws.id} station={ws} />
              ))}

              {INFRASTRUCTURE_NODES.map(node => (
                <InfrastructureNode3D key={node.id} node={node} />
              ))}

              <SyncChamber />
              <BossCore3D boss={boss} />

              {agents.map(agent => (
                <Agent3D key={agent.id} agent={agent} />
              ))}

              <CollaborationLines pairs={collaborationPairs} agents={agents} />
            </motion.div>
          </div>
        </div>

        {/* ─── Right Side Panels ─── */}
        <div style={{
          width: 260, display: 'flex', flexDirection: 'column',
          gap: 6, padding: 6, overflow: 'auto', flexShrink: 0,
          borderLeft: '1px solid rgba(6,182,212,0.1)',
        }}>
          <ActivityPanel
            activityLog={activityLog}
            agents={agents}
            boss={boss}
            integrations={integrations}
          />
          <TelemetryPanel telemetry={telemetry} />
          <CommandPanel agents={agents} onCommand={dispatchCommand} />
        </div>
      </div>
    </div>
  );
}
