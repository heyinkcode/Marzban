import {
  Alert, AlertIcon, Badge, Box, Button, Checkbox, FormControl, FormLabel, HStack,
  Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader,
  ModalOverlay, Select, Skeleton, Stack, Text, Tooltip, useDisclosure, useToast, usePrefersReducedMotion,
} from "@chakra-ui/react";
import { ShieldCheckIcon } from "@heroicons/react/24/outline";
import { NodeType, FetchNodesQueryKey } from "contexts/NodesContext";
import useGetUser from "hooks/useGetUser";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useQuery, useQueryClient } from "react-query";
import {
  AccessState, DedicatedNode, PendingAccess, accessReceipt, finishPending, loadUserAccess,
  readNodePolicy, readPending, saveNodePolicy, startPending, submitAccess,
} from "service/dedicatedAccess";

function Help({ label }: { label: string }) {
  return <Tooltip label={label} hasArrow><Text as="span" tabIndex={0} aria-label={label}
    fontSize="sm" color="gray.500" cursor="help">ⓘ</Text></Tooltip>;
}

function AccessRow({ node, state, actor, username, locked, lock, refresh }: {
  node: DedicatedNode; state?: AccessState; actor: string; username: string;
  locked: boolean; lock: (busy: boolean) => void; refresh: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const [pending, setPending] = useState<PendingAccess | null>(null);
  const [storageError, setStorageError] = useState(false);
  const [uncertain, setUncertain] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const actionRef = useRef<HTMLButtonElement>(null);
  const wasBusy = useRef(false);
  useEffect(() => {
    if (busy) wasBusy.current = true;
    if (wasBusy.current && !busy && !locked) {
      actionRef.current?.focus();
      wasBusy.current = false;
    }
  }, [busy, locked]);
  useEffect(() => {
    try { setPending(readPending(actor, username, node.id)); }
    catch { setStorageError(true); }
  }, [actor, username, node.id]);

  const perform = async (receiptOnly: boolean) => {
    if (locked || storageError) return;
    setBusy(true); lock(true); setConfirm(false); setUncertain(false);
    let operation = pending;
    try {
      if (!operation) {
        if (receiptOnly || !state) return;
        try { operation = startPending(actor, username, node.id, !state.granted); setPending(operation); }
        catch { setStorageError(true); return; } // 保存编号失败，绝不发送写请求。
      }
      const result = receiptOnly ? await accessReceipt(operation) : await submitAccess(username, node.id, operation);
      finishPending(actor, username, node.id, result);
      if (result.sync_state === "synced") setPending(null);
      toast({ status: result.sync_state === "synced" ? "success" : "warning",
        title: t(result.sync_state === "synced" ? "dedicated.updated" : "dedicated.pending") });
      refresh();
    } catch {
      // 请求可能已提交。保留编号，用只读回执确认；不自动重试写请求。
      setUncertain(true);
    } finally { setBusy(false); lock(false); }
  };
  return <Box borderWidth="1px" borderRadius="md" p={3}>
    <Stack direction={{ base: "column", sm: "row" }} justify="space-between" spacing={3}>
      <Box minW={0}>
        <Text fontWeight="medium" fontSize="sm" overflowWrap="anywhere">{node.name}</Text>
        <HStack mt={1} flexWrap="wrap">
          <Badge colorScheme={state?.effective ? "green" : state?.granted ? "orange" : "gray"}>
            {t(state?.effective ? "dedicated.effective" : state?.granted ? "dedicated.granted" : "dedicated.notGranted")}
          </Badge>
          {state && <Text fontSize="xs" color="gray.500">{t(`dedicated.sync.${state.sync_state}`)}</Text>}
          {!node.enabled && <Text fontSize="xs">{t("dedicated.nodeDisabled")}</Text>}
        </HStack>
        {state?.granted && !state.effective && <Text mt={1} fontSize="xs" color="gray.500">{t("dedicated.notEffectiveHelp")}</Text>}
      </Box>
      <Stack direction={{ base: "column", sm: "row" }} align="stretch" flexShrink={0}>
        {pending ? <>
          <Button ref={actionRef} size="sm" type="button" minH="44px" onClick={() => perform(true)} isLoading={busy} isDisabled={locked && !busy}>
            {t("dedicated.receipt")}
          </Button>
          <Button size="sm" type="button" minH="44px" variant="outline" onClick={() => setConfirm(true)} isDisabled={locked || storageError}>
            {t("dedicated.resume")}
          </Button>
        </> : <Button ref={actionRef} size="sm" type="button" minH="44px" colorScheme={state?.granted ? "red" : "primary"}
          variant={state?.granted ? "outline" : "solid"} onClick={() => setConfirm(true)}
          isDisabled={locked || !state || storageError}>
          {t(state?.granted ? "dedicated.revoke" : "dedicated.grant")}
        </Button>}
      </Stack>
    </Stack>
    {pending && <Text fontSize="xs" mt={2} color="gray.500" overflowWrap="anywhere">
      {t(pending.granted ? "dedicated.intentGrant" : "dedicated.intentRevoke")} · {pending.operation_id}
    </Text>}
    {(storageError || uncertain) && <Alert status="warning" mt={2} borderRadius="md"><AlertIcon />
      <Text fontSize="xs">{t(storageError ? "dedicated.storageError" : "dedicated.uncertain")}</Text>
    </Alert>}
    {confirm && <Box mt={3}>
      <Alert status="warning" borderRadius="md" alignItems="flex-start"><AlertIcon />
        <Text fontSize="xs">{t("dedicated.confirmChange")}</Text></Alert>
      <HStack justify="end" mt={2}>
        <Button size="sm" type="button" onClick={() => setConfirm(false)}>{t("cancel")}</Button>
        <Button size="sm" type="button" colorScheme="primary" isDisabled={locked || storageError}
          onClick={() => perform(false)}>{t("dedicated.confirm")}</Button>
      </HStack>
    </Box>}
  </Box>;
}

export function DedicatedUserAccessButton({ username, compact = false }: { username: string; compact?: boolean }) {
  const modal = useDisclosure();
  const reduceMotion = usePrefersReducedMotion();
  const { userData } = useGetUser();
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const query = useQuery(["dedicated-user-access", userData.username, username], () => loadUserAccess(username), {
    enabled: modal.isOpen && !!userData.username, retry: false, refetchOnWindowFocus: false,
    refetchInterval: modal.isOpen && !busy ? 10000 : false,
  });
  return <>
    <Tooltip label={t("dedicated.userTitle")}>
      <Button type="button" size="sm" minH="44px" px={compact ? 2 : 3} variant="ghost" isDisabled={!userData.username}
        aria-label={`${t("dedicated.userTitle")} · ${username}`} onClick={(event) => { event.stopPropagation(); modal.onOpen(); }}>
        <ShieldCheckIcon width={18} />{!compact && <Text ml={2}>{t("dedicated.userTitle")}</Text>}
      </Button>
    </Tooltip>
    {/* 复用原 Chakra Modal 的可逆开关和遮罩反馈，不新增自定义动效。 */}
    <Modal isOpen={modal.isOpen} onClose={() => { if (!busy) modal.onClose(); }} size="xl" isCentered scrollBehavior="inside" motionPreset={reduceMotion ? "none" : "scale"}>
      <ModalOverlay /><ModalContent mx={3} onClick={event => event.stopPropagation()}>
        <ModalHeader fontSize="md" pr={12} overflowWrap="anywhere">{username} · {t("dedicated.userTitle")}</ModalHeader>
        <ModalCloseButton isDisabled={busy} />
        <ModalBody pt={0} sx={{ "@media (prefers-reduced-motion: reduce)": { ".chakra-skeleton": { animation: "none" } } }}>
          <Alert status="info" borderRadius="md" mb={4} alignItems="flex-start"><AlertIcon />
            <Text fontSize="xs">{t("dedicated.userHelp")}</Text></Alert>
          {query.isLoading && <Stack><Skeleton h="78px" /><Skeleton h="78px" /></Stack>}
          {query.isError && <Alert status="error" borderRadius="md"><AlertIcon /><Text fontSize="sm">{t("dedicated.loadError")}</Text></Alert>}
          {!query.isLoading && !query.isError && query.data?.nodes.length === 0 && <Text fontSize="sm">{t("dedicated.empty")}</Text>}
          {!query.isError && <Stack spacing={3}>{query.data?.nodes.map(node => <AccessRow key={node.id} node={node}
            state={query.data.states.find(state => state.node_id === node.id)} actor={userData.username}
            username={username} locked={busy || query.isFetching} lock={setBusy} refresh={() => query.refetch()} />)}</Stack>}
        </ModalBody>
        <ModalFooter gap={2}>
          <Button type="button" size="sm" onClick={() => query.refetch()} isLoading={query.isFetching} isDisabled={busy}>{t("dedicated.refresh")}</Button>
          <Button type="button" size="sm" onClick={modal.onClose} isDisabled={busy}>{t("cancel")}</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  </>;
}

export function DedicatedNodeSettings({ nodes }: { nodes: NodeType[] }) {
  const { t } = useTranslation();
  const { userData } = useGetUser();
  const modal = useDisclosure();
  const reduceMotion = usePrefersReducedMotion();
  const client = useQueryClient();
  const toast = useToast();
  const [nodeId, setNodeId] = useState(0);
  const [mode, setMode] = useState<"public" | "restricted">("public");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);
  const query = useQuery(["dedicated-node-policy", nodeId], () => readNodePolicy(nodeId), {
    enabled: modal.isOpen && !!nodeId && userData.is_sudo, retry: false, refetchOnWindowFocus: false,
  });
  useEffect(() => { if (query.data) { setMode(query.data.access_mode); setConfirmed(false); } }, [query.data]);
  if (!userData.is_sudo) return null;
  const canSave = !!query.data && !query.isFetching && !query.isError && !error && !busy && confirmed
    && mode !== query.data.access_mode;
  const save = async () => {
    if (!canSave) return;
    setBusy(true); setError(false);
    try {
      const result = await saveNodePolicy(nodeId, mode, confirmed);
      client.setQueryData(["dedicated-node-policy", nodeId], result);
      client.invalidateQueries(FetchNodesQueryKey);
      toast({ status: result.sync_state === "synced" ? "success" : "warning",
        title: t(result.sync_state === "synced" ? "dedicated.updated" : "dedicated.pending") });
      setConfirmed(false);
    } catch { setError(true); } finally { setBusy(false); }
  };
  return <>
    <HStack justify="end" mb={3}><Button type="button" size="sm" variant="outline" colorScheme="primary" minH="44px"
      onClick={() => { setError(false); setNodeId(nodes[0]?.id || 0); modal.onOpen(); }}>
      {t("dedicated.nodeTitle")}
    </Button></HStack>
    <Modal isOpen={modal.isOpen} onClose={() => { if (!busy) modal.onClose(); }} size="lg" isCentered scrollBehavior="inside" motionPreset={reduceMotion ? "none" : "scale"}>
      <ModalOverlay /><ModalContent mx={3}>
        <ModalHeader fontSize="md">{t("dedicated.nodeTitle")}</ModalHeader><ModalCloseButton isDisabled={busy} />
        <ModalBody pt={0}>
          <Stack spacing={4}>
            <FormControl><FormLabel fontSize="sm">{t("dedicated.node")}</FormLabel>
              <Select value={nodeId} isDisabled={busy} onChange={event => { setNodeId(Number(event.target.value)); setConfirmed(false); setError(false); }}>
                <option value={0}>{t("dedicated.selectNode")}</option>
                {nodes.map(node => <option key={node.id!} value={node.id!}>{node.name}</option>)}
              </Select>
            </FormControl>
            {query.isLoading && !!nodeId && <Skeleton h="64px" />}
            {(query.isError || error) && <Alert status="warning"><AlertIcon /><Text fontSize="xs">{t(error ? "dedicated.policyError" : "dedicated.loadError")}</Text></Alert>}
            {!!nodeId && query.data && !query.isError && <>
              <FormControl><FormLabel fontSize="sm" display="flex" alignItems="center" gap={2}>
                {t("dedicated.mode")}<Help label={t("dedicated.modeHelp")} /></FormLabel>
                <Select value={mode} isDisabled={busy || query.isFetching} onChange={event => { setMode(event.target.value as typeof mode); setConfirmed(false); }}>
                  <option value="public">{t("dedicated.public")}</option><option value="restricted">{t("dedicated.restricted")}</option>
                </Select>
              </FormControl>
              <Text fontSize="sm">{t(`dedicated.sync.${query.data.sync_state}`)}</Text>
              <Alert status="warning" borderRadius="md" alignItems="flex-start"><AlertIcon /><Text fontSize="xs">{t("dedicated.modeWarning")}</Text></Alert>
              {mode !== query.data.access_mode && <Checkbox isChecked={confirmed} isDisabled={busy} onChange={event => setConfirmed(event.target.checked)}>
                <Text fontSize="sm">{t(mode === "public" ? "dedicated.confirmPublic" : "dedicated.confirmRestricted")}</Text>
              </Checkbox>}
            </>}
          </Stack>
        </ModalBody>
        <ModalFooter gap={2}>
          <Button type="button" size="sm" onClick={async () => { const result = await query.refetch(); if (!result.isError) setError(false); }} isDisabled={!nodeId || busy} isLoading={query.isFetching}>{t("dedicated.refresh")}</Button>
          <Button type="button" size="sm" onClick={modal.onClose} isDisabled={busy}>{t("cancel")}</Button>
          <Button type="button" size="sm" colorScheme="primary" onClick={save} isLoading={busy} isDisabled={!canSave}>{t("dedicated.save")}</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  </>;
}
