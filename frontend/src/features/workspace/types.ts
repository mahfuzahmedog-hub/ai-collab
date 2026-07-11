export interface Organization {
  id: string;
  name: string;
  icon?: string;
}

export interface WorkspaceSummary {
  id: string;
  orgId: string | null;
  name: string;
  icon?: string;
  color?: string;
  isPinned: boolean;
  isFavorite: boolean;
  lastOpenedAt?: string;
  unreadCount?: number;
}

export interface WorkspaceSwitcherState {
  organizations: Organization[];
  workspaces: WorkspaceSummary[];
  activeOrgId: string | null;
  activeWorkspaceId: string | null;
  recent: WorkspaceSummary[];
  pinned: WorkspaceSummary[];
  favorites: WorkspaceSummary[];
}
