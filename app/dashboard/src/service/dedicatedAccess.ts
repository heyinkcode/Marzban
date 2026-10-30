import { fetch } from "service/http";

export type AccessState = {
  node_id: number; username: string; granted: boolean; effective: boolean;
  sync_state: "synced" | "pending" | "error";
  policy_revision: number; applied_revision: number | null;
  operation_id?: string; requested_granted?: boolean; detail?: string | null;
};
export type DedicatedNode = {
  id: number; name: string; enabled: boolean; status: string;
};
export type PendingAccess = { operation_id: string; granted: boolean };
export type NodeAccessPolicy = Pick<AccessState, "sync_state" | "policy_revision" | "applied_revision"> & {
  node_id: number; access_mode: "public" | "restricted";
};
const path = (username: string, nodeId: number) =>
  `/user/${encodeURIComponent(username)}/dedicated-nodes/${nodeId}`;
const key = (actor: string, username: string, nodeId: number) =>
  `dedicated-access-v1:${encodeURIComponent(actor)}:${encodeURIComponent(username)}:${nodeId}`;

export function readPending(actor: string, username: string, nodeId: number): PendingAccess | null {
  const value = sessionStorage.getItem(key(actor, username, nodeId));
  if (!value) return null;
  const parsed = JSON.parse(value);
  if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(parsed.operation_id)
      || typeof parsed.granted !== "boolean") throw new Error("INVALID_PENDING_ACCESS");
  return { operation_id: parsed.operation_id, granted: parsed.granted };
}

export function startPending(actor: string, username: string, nodeId: number, granted: boolean): PendingAccess {
  // 请求编号先落盘；断线后只能查询/显式续办同一编号，不能换编号盲重发。
  const existing = readPending(actor, username, nodeId);
  if (existing) return existing;
  const operation = { operation_id: crypto.randomUUID(), granted };
  sessionStorage.setItem(key(actor, username, nodeId), JSON.stringify(operation));
  return operation;
}

export function finishPending(actor: string, username: string, nodeId: number, state: AccessState) {
  if (state.sync_state === "synced") sessionStorage.removeItem(key(actor, username, nodeId));
}

export async function loadUserAccess(username: string) {
  const [catalog, access] = await Promise.all([
    fetch<{ capability: string; nodes: DedicatedNode[] }>("/dedicated-nodes", { retry: 0 }),
    fetch<{ capability: string; nodes: AccessState[] }>(`/user/${encodeURIComponent(username)}/dedicated-nodes`, { retry: 0 }),
  ]);
  if (catalog.capability !== "dedicated-node-access-v1" || access.capability !== catalog.capability)
    throw new Error("UNSUPPORTED_DEDICATED_ACCESS");
  return { nodes: catalog.nodes, states: access.nodes };
}

export const submitAccess = (username: string, nodeId: number, operation: PendingAccess) =>
  fetch<AccessState>(path(username, nodeId), {
    method: operation.granted ? "PUT" : "DELETE", retry: 0, timeout: 90000,
    body: { operation_id: operation.operation_id },
  });
export const accessReceipt = (operation: PendingAccess) =>
  fetch<AccessState>(`/dedicated-node-operations/${encodeURIComponent(operation.operation_id)}`, { retry: 0 });
export const readNodePolicy = (nodeId: number) => fetch<NodeAccessPolicy>(`/node/${nodeId}/access`, { retry: 0 });
export const saveNodePolicy = (nodeId: number, mode: "public" | "restricted", confirmed: boolean) =>
  fetch<NodeAccessPolicy>(`/node/${nodeId}/access`, {
    method: "PUT", body: { access_mode: mode, confirm_public_access: mode === "public" && confirmed },
    retry: 0, timeout: 90000,
  });
