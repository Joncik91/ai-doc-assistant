import type { Panel } from './workspace-model'

interface WorkspaceTabsProps {
  activePanel: Panel
  panels: Array<{ id: Panel; label: string }>
  onPanelChange: (panel: Panel) => void
}

export function WorkspaceTabs({ activePanel, panels, onPanelChange }: WorkspaceTabsProps) {
  return (
    <nav className="workspace-toolbar panel" aria-label="Workspace sections">
      <div className="tab-list" aria-label="Workspace panels">
        {panels.map((panel) => (
          <button
            key={panel.id}
            type="button"
            aria-pressed={activePanel === panel.id}
            className={activePanel === panel.id ? 'tab-list__item is-active' : 'tab-list__item'}
            onClick={() => onPanelChange(panel.id)}
          >
            {panel.label}
          </button>
        ))}
      </div>
    </nav>
  )
}
