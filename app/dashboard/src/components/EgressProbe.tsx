import { useEffect, useRef, useState } from "react";
import { Badge, Box, Button, HStack, Icon, IconButton, Select, SimpleGrid, Stack, Text, Tooltip } from "@chakra-ui/react";
import { ArrowPathIcon, CheckCircleIcon, ChevronDownIcon, ChevronUpIcon, InformationCircleIcon, XCircleIcon } from "@heroicons/react/24/outline";
import { useTranslation } from "react-i18next";
import { fetch } from "service/http";

export type EgressDraft = {protocol: string; udp_mode: string; server: string; port: number; username: string | null; password: string | null};
type Step = {stage: string; status: string; code: string; duration_ms: number};
type Result = {ok: boolean; code?: string; completed: number; attempts: number; checked_at: string;
  rounds: {ok: boolean; steps: Step[]; exit_ip?: string}[]};

export function EgressHelp({label}: {label: string}) {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  return <Tooltip label={label} hasArrow isOpen={open} maxW="min(320px, calc(100vw - 32px))" overflowWrap="anywhere">
    <IconButton type="button" variant="unstyled" minW="24px" h="24px" display="inline-flex" alignItems="center" justifyContent="center"
      aria-label={label} aria-expanded={open} color="gray.400" icon={<Icon as={InformationCircleIcon} boxSize={4} />}
      onMouseEnter={() => setOpen(true)} onMouseLeave={() => { if (!pinned) setOpen(false); }} onFocus={() => setOpen(true)}
      onBlur={() => { setPinned(false); setOpen(false); }} onClick={() => { setPinned(!pinned); setOpen(!pinned); }}
      onKeyDown={event => { if (event.key === "Escape") { event.stopPropagation(); setPinned(false); setOpen(false); } }} />
  </Tooltip>;
}

export const egressErrorCode = (error: any) => {
  const value = error?.data?.detail?.code;
  return typeof value === "string" && /^[A-Z_]{2,64}$/.test(value) ? value : "NODE_CONTROL_UNAVAILABLE";
};

export function EgressProbe({nodeId, nodeName, draft, disabled}: {nodeId: number; nodeName: string; draft: EgressDraft; disabled: boolean}) {
  const {t} = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const [advanced, setAdvanced] = useState(false);
  const [timeout, setTimeoutSeconds] = useState(5);
  const [attempts, setAttempts] = useState(1);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const sequence = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const key = JSON.stringify([nodeId, draft, timeout, attempts]);
  useEffect(() => {
    sequence.current++; controller.current?.abort(); setRunning(false); setResult(null); setError(null);
    return () => { sequence.current++; controller.current?.abort(); };
  }, [key]);
  async function test() {
    if (disabled || running) return;
    const current = ++sequence.current;
    const request = new AbortController(); controller.current = request;
    setExpanded(true); setResult(null); setError(null); setRunning(true);
    try {
      const value = await fetch<Result>(`/node/${nodeId}/egress/test`, {method:"POST", retry:0, timeout:45000,
        signal:request.signal, body:{profile:draft,timeout_seconds:timeout,attempts}});
      if (sequence.current === current) setResult(value);
    } catch (failure) {
      if (sequence.current === current) setError(egressErrorCode(failure));
    } finally { if (sequence.current === current) setRunning(false); }
  }
  function stop() { sequence.current++; controller.current?.abort(); setRunning(false); setError("WAIT_CANCELLED"); }
  const message = (code: string) => t(`nodes.egressProbe.code.${code}`, {defaultValue:t("nodes.egressProbe.unknown")});
  return <Box borderWidth="1px" borderColor="gray.200" _dark={{borderColor:"gray.600"}} borderRadius="md" p={3} data-testid="egress-probe">
    <HStack justify="space-between" gap={2} flexWrap="wrap">
      <HStack spacing={1}>
        <Button type="button" variant="unstyled" size="xs" display="inline-flex" alignItems="center" gap={1}
          aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>
          <Text fontSize="sm" fontWeight="medium">{t("nodes.egressProbe.title")}</Text><Icon as={expanded ? ChevronUpIcon : ChevronDownIcon} boxSize={3}/>
        </Button>
        <EgressHelp label={t("nodes.egressProbe.help")}/>
        {result && <Badge colorScheme={result.ok ? "green" : "red"}>{t(result.ok ? "nodes.egressProbe.passed" : "nodes.egressProbe.failed")}</Badge>}
      </HStack>
      <Button type="button" size="xs" variant="outline" colorScheme="primary" isDisabled={!running && disabled}
        leftIcon={<Icon as={ArrowPathIcon} boxSize={3}/>} onClick={running ? stop : test}>
        {t(running ? "nodes.egressProbe.stop" : "nodes.egressProbe.test")}</Button>
    </HStack>
    {expanded && <Stack spacing={2} mt={2}>
      <Text fontSize="xs" color="gray.500" _dark={{color:"gray.400"}}>{t("nodes.egressProbe.source",{name:nodeName})}</Text>
      <Text fontSize="xs" color="gray.500" _dark={{color:"gray.400"}} overflowWrap="anywhere">{nodeName} → {draft.server}:{draft.port} → Internet</Text>
      <Button type="button" size="xs" variant="link" alignSelf="start" color="gray.500" aria-expanded={advanced}
        rightIcon={<Icon as={advanced ? ChevronUpIcon : ChevronDownIcon} boxSize={3}/>} onClick={() => setAdvanced(!advanced)}>{t("nodes.egressProbe.advanced")}</Button>
      {advanced && <SimpleGrid columns={2} spacing={3}>
        <Box><Text as="label" htmlFor={`egress-timeout-${nodeId}`} fontSize="xs">{t("nodes.egressProbe.timeout")}</Text>
          <Select id={`egress-timeout-${nodeId}`} size="xs" value={timeout} isDisabled={running} onChange={event => setTimeoutSeconds(Number(event.target.value))}>
            <option value={5}>5 {t("nodes.egressProbe.seconds")}</option><option value={10}>10 {t("nodes.egressProbe.seconds")}</option></Select></Box>
        <Box><Text as="label" htmlFor={`egress-attempts-${nodeId}`} fontSize="xs">{t("nodes.egressProbe.attempts")}</Text>
          <Select id={`egress-attempts-${nodeId}`} size="xs" value={attempts} isDisabled={running} onChange={event => setAttempts(Number(event.target.value))}>
            <option value={1}>1</option><option value={3}>3</option></Select></Box>
      </SimpleGrid>}
      <Box aria-live="polite" overflowWrap="anywhere">
        {running && <Text fontSize="xs">{t("nodes.egressProbe.running")}</Text>}
        {!running && !result && !error && <Text fontSize="xs" color="gray.500">{t("nodes.egressProbe.idle")}</Text>}
        {error && <Text fontSize="xs" color="red.500">{message(error)}</Text>}
        {result && <Stack spacing={2}>
          <Text fontSize="xs">{t("nodes.egressProbe.completed",{count:result.completed,total:result.attempts})}</Text>
          {result.rounds.map((round,index) => <Box key={index} borderTopWidth="1px" pt={2}>
            <Text fontSize="xs" fontWeight="medium">{t("nodes.egressProbe.round",{number:index+1})}</Text>
            {round.steps.map(step => <HStack key={step.stage} justify="space-between" spacing={2} mt={1}>
              <HStack spacing={1}><Icon boxSize={4} as={step.status === "failed" ? XCircleIcon : step.status === "ok" ? CheckCircleIcon : InformationCircleIcon}
                color={step.status === "failed" ? "red.500" : step.status === "ok" ? "green.500" : "gray.400"}/>
                <Text fontSize="xs">{t(`nodes.egressProbe.stage.${step.stage}`)}</Text></HStack><Text fontSize="xs" flexShrink={0}>{step.duration_ms} ms</Text>
            </HStack>)}
            {round.steps.filter(step => step.code !== "OK").map(step => <Text key={step.stage} fontSize="xs" mt={1}
              color={step.status === "failed" ? "red.500" : "gray.500"}>{message(step.code)}</Text>)}
            {round.exit_ip && <Text fontSize="xs" mt={1}>{t("nodes.egressProbe.exit",{ip:round.exit_ip})}</Text>}
          </Box>)}
          {result.code && <Text fontSize="xs" color="red.500">{message(result.code)}</Text>}
          <Text fontSize="xs" color="gray.500">{t("nodes.egressProbe.checked",{time:result.checked_at})}</Text>
        </Stack>}
      </Box>
      <Text fontSize="xs" color="gray.500" _dark={{color:"gray.400"}}>{t("nodes.egressProbe.scope")}</Text>
    </Stack>}
  </Box>;
}
