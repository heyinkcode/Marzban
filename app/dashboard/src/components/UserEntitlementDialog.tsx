import {
  Alert, AlertIcon, Button, Checkbox, FormControl, FormLabel, HStack, Input,
  Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader, ModalOverlay,
  SimpleGrid, Skeleton, Stack, Text, Textarea, usePrefersReducedMotion,
} from "@chakra-ui/react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { fetch } from "service/http";

type Action = "extend" | "add" | "renew" | "restore";
type State = {expires_at: number | null; quota_bytes: string | null; used_bytes: string;
  remaining_bytes: string | null; reset_strategy: string; has_next_plan: boolean};
type Overview = {state: State; can_restore: boolean;
  latest_reset: {id: number; reset_at: string; bytes: string; origin: string; restored: boolean} | null};
type Command = {action: Action; expires_at?: number; extra_bytes?: string; reset_id?: number; reason?: string};
type Preview = {guard: string; before: State; after: State};
type Pending = {operation_id: string; guard: string; command: Command; confirmed: boolean};
type Receipt = {operation_id: string; after: State};

const binaryGiB = 1073741824;
export function parseEntitlementGiB(value: string) {
  if (!/^(0|[1-9][0-9]{0,7})(\.[0-9]{1,3})?$/.test(value)) return null;
  const [whole, fraction = ""] = value.split(".");
  // Multiply decimal digits individually; the result can exceed JS's safe integer.
  const digits = whole + fraction.padEnd(3, "0");
  let carry = 0;
  let product = "";
  for (let i = digits.length - 1; i >= 0; i--) {
    const part = Number(digits[i]) * binaryGiB + carry;
    product = String(part % 10) + product;
    carry = Math.floor(part / 10);
  }
  return (String(carry) + product).slice(0, -3).replace(/^0+/, "") || null;
}
const storageKey = (username: string) => "marzban-entitlement-v1:" + username;
const operationPath = (username: string) => "/user/" + encodeURIComponent(username) + "/entitlement";

function readPending(username: string): Pending | null {
  try {
    const value = JSON.parse(sessionStorage.getItem(storageKey(username)) || "null");
    return value && typeof value.operation_id === "string" && value.command ? value : null;
  } catch { return null; }
}

function writePending(username: string, value: Pending | null) {
  try {
    if (value) sessionStorage.setItem(storageKey(username), JSON.stringify(value));
    else sessionStorage.removeItem(storageKey(username));
    return true;
  } catch { return false; }
}

function newOperationId() {
  // getRandomValues works on existing HTTP-only panels too.
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = Array.from(bytes, n => n.toString(16).padStart(2, "0")).join("");
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join("-");
}

export const UserEntitlementDialog = ({ username, isOpen, onClose, onUpdated, loadOverview, previewCommand, applyCommand }:{
  username: string; isOpen: boolean; onClose: () => void; onUpdated: () => void;
  loadOverview?: () => Promise<Overview>; previewCommand?: (body: Command) => Promise<Preview>;
  applyCommand?: (body: Pending) => Promise<Receipt>;
}) => {
  const { t, i18n } = useTranslation();
  const reduced = usePrefersReducedMotion();
  const busy = useRef(false);
  const [loading, setLoading] = useState(false);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [action, setAction] = useState<Action>("extend");
  const [date, setDate] = useState("");
  const [amount, setAmount] = useState("");
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState("");
  const [review, setReview] = useState<{command: Command; preview: Preview} | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const [succeeded, setSucceeded] = useState(false);
  const path = operationPath(username);

  const load = () => loadOverview ? loadOverview() : fetch<Overview>(path);
  useEffect(() => {
    if (!isOpen) return;
    let current = true;
    setOverview(null); setAction("extend"); setDate(""); setAmount(""); setReason(""); setError("");
    setConfirmed(false); setReview(null); setSucceeded(false); setPending(readPending(username));
    load().then(value => { if (current) setOverview(value); }, () => { if (current) setError("entitlement.loadFailed"); });
    return () => { current = false; };
  }, [isOpen, username]);

  const dateLabel = (v: number | null) => v ? new Date(v * 1000).toLocaleString(i18n.language) : t("entitlement.unlimited");
  const quotaLabel = (v: string | null) => v === null ? t("entitlement.unlimited")
    : new Intl.NumberFormat(i18n.language, {maximumFractionDigits: 3}).format(Number(v) / binaryGiB) + " GiB";
  const invalidate = () => { setReview(null); setConfirmed(false); setError(""); };
  const latest = overview?.latest_reset;
  const needsConfirm = action === "renew" || action === "restore";
  const actions: Action[] = ["extend", "add", "renew"];
  if (overview?.can_restore && latest && latest.origin !== "native_renewal" && !latest.restored) actions.push("restore");

  const buildCommand = (): Command | null => {
    if (action === "extend" || action === "renew") {
      if (!date) return action === "renew" ? {action} : null;
      const time = Math.floor(new Date(date).getTime() / 1000);
      return Number.isSafeInteger(time) ? {action, expires_at: time} : null;
    }
    if (action === "add") {
      const extra = parseEntitlementGiB(amount);
      return extra ? {action, extra_bytes: extra} : null;
    }
    return latest && reason.trim().length >= 5 ? {action, reset_id: latest.id, reason: reason.trim()} : null;
  };
  const run = async () => {
    if (busy.current) return;
    busy.current = true;
    setLoading(true); setError("");
    try {
      if (!pending && !review) {
        const command = buildCommand();
        if (!command) { setError("entitlement.invalidInput"); return; }
        const preview = await (previewCommand ? previewCommand(command) : fetch<Preview>(path + "/preview", {method: "POST", body: command}));
        setReview({command, preview});
        return;
      }
      if (!pending && needsConfirm && !confirmed) return;
      const body = pending || {operation_id: newOperationId(), guard: review!.preview.guard, command: review!.command, confirmed};
      if (!pending && !writePending(username, body)) {
        setError("entitlement.storageUnavailable");
        return;
      }
      setPending(body);
      let receipt: Receipt;
      try {
        receipt = await (applyCommand ? applyCommand(body) : fetch<Receipt>(path + "/operations", {method: "POST", body}));
      } catch (err: unknown) {
        const code = (err as {data?: {detail?: {code?: string}}})?.data?.detail?.code;
        if (code === "entitlement_changed" || code === "operation_conflict" || code === "reset_not_restorable"
            || code === "restore_would_reach_quota" || code === "next_plan_conflict" || code === "expiry_must_extend_finite_term"
            || code === "renewal_requires_future_expiry" || code === "restore_requires_active_term"
            || code === "finite_quota_and_valid_increment_required") {
          setPending(null); writePending(username, null); setReview(null); setConfirmed(false);
          setError("entitlement.reviewAgain");
        } else setError("entitlement.resultUnknown");
        return;
      }
      if (receipt.operation_id !== body.operation_id) {setError("entitlement.resultUnknown");return;}
      setPending(null); writePending(username, null); setReview(null); setConfirmed(false); setSucceeded(true);
      setOverview(value => value ? {...value, state: receipt.after} : value);
      onUpdated();
    } catch (err: unknown) {
      const code = (err as {data?: {detail?: {code?: string}}})?.data?.detail?.code;
      setError(code === "next_plan_conflict" ? "entitlement.nextPlan"
        : code === "finite_quota_and_valid_increment_required" ? "entitlement.finiteQuota"
        : code === "expiry_must_extend_finite_term" ? "entitlement.renewDateRule"
        : code === "restore_would_reach_quota" ? "entitlement.restoreLimit" : "entitlement.previewFailed");
    } finally {
      busy.current = false; setLoading(false);
    }
  };

  const stateRows = (state: State) => [
    [t("entitlement.expiry"), dateLabel(state.expires_at)],
    [t("entitlement.quota"), quotaLabel(state.quota_bytes)],
    [t("entitlement.used"), quotaLabel(state.used_bytes)],
    [t("entitlement.remaining"), quotaLabel(state.remaining_bytes)],
  ];
  return <Modal isOpen={isOpen} onClose={loading ? () => {} : onClose} isCentered size="lg"
    scrollBehavior="inside" motionPreset={reduced ? "none" : "scale"}
    closeOnOverlayClick={!loading} closeOnEsc={!loading} returnFocusOnClose>
    <ModalOverlay />
    <ModalContent mx={3}>
      <ModalHeader>{t("entitlement.title")} · {username}</ModalHeader>
      {!loading && <ModalCloseButton />}
      <ModalBody>
        <Stack spacing={4}>
          {!overview && !error && <Stack><Skeleton height="28px" /><Skeleton height="112px" /></Stack>}
          {overview && !pending && !succeeded && <>
            {overview.state.reset_strategy !== "no_reset" && <Alert status="warning" borderRadius="md">
              <AlertIcon />{t("entitlement.legacy")}
            </Alert>}
            <SimpleGrid columns={{base: 1, sm: 2}} spacing={2}>
              {actions.map(choice => <Button key={choice} type="button" minH="44px" isDisabled={loading}
                aria-pressed={action === choice} variant="outline" colorScheme="gray" whiteSpace="normal"
                {...(action === choice ? {
                  bg: "primary.100", color: "gray.900", borderColor: "primary.300",
                  _hover: { bg: "primary.200" }, _active: { bg: "primary.300" },
                  _dark: {
                    bg: "primary.800", color: "gray.50", borderColor: "primary.300",
                    _hover: { bg: "primary.700" }, _active: { bg: "primary.600" },
                  },
                } : {})}
                onClick={() => { setAction(choice); invalidate(); }}>{t("entitlement." + choice)}</Button>)}
            </SimpleGrid>
            <Text fontSize="sm" color="gray.500">{t("entitlement.help." + action)}</Text>
            {(action === "extend" || action === "renew") && <FormControl id="entitlement-expiry">
              <FormLabel>{t(action === "extend" ? "entitlement.newExpiry" : "entitlement.optionalExpiry")}</FormLabel>
              <Input type="datetime-local" fontSize="md" value={date} disabled={loading}
                onChange={e => { setDate(e.target.value); invalidate(); }} />
            </FormControl>}
            {action === "add" && <FormControl id="entitlement-extra">
              <FormLabel>{t("entitlement.extra")}</FormLabel>
              <Input inputMode="decimal" fontSize="md" value={amount} disabled={loading}
                onChange={e => { setAmount(e.target.value); invalidate(); }} />
            </FormControl>}
            {action === "restore" && latest && <FormControl id="entitlement-reason">
              <Text fontSize="sm" mb={2}>{t("entitlement.resetDetail", {
                id: latest.id, date: new Date(latest.reset_at).toLocaleString(i18n.language), quota: quotaLabel(latest.bytes)})}</Text>
              <FormLabel>{t("entitlement.reason")}</FormLabel>
              <Textarea value={reason} maxLength={240} disabled={loading}
                onChange={e => { setReason(e.target.value); invalidate(); }} />
            </FormControl>}
          </>}
          {overview && <Stack borderWidth="1px" borderRadius="md" spacing={2} p={3} aria-live="polite">
            <Text fontWeight="semibold">{t(review ? "entitlement.beforeAfter" : "entitlement.current")}</Text>
            {stateRows(review ? review.preview.before : overview.state).map(([label, value], i) =>
              <HStack key={i} justifyContent="space-between" flexWrap="wrap" fontSize="sm">
                <Text>{label}</Text><Text>{review && value !== stateRows(review.preview.after)[i][1]
                  ? value + " → " + stateRows(review.preview.after)[i][1] : value}</Text>
              </HStack>)}
          </Stack>}
          {review && needsConfirm && !pending && <Checkbox isChecked={confirmed} isDisabled={loading}
            onChange={event => setConfirmed(event.target.checked)}>{t("entitlement.confirm." + action)}</Checkbox>}
          {pending && <Alert status="warning" borderRadius="md"><AlertIcon />{t("entitlement.pending")}</Alert>}
          {succeeded && <Alert status="success" borderRadius="md"><AlertIcon />{t("entitlement.saved")}</Alert>}
          {error && <Alert status="error" borderRadius="md" role="alert"><AlertIcon />{t(error)}</Alert>}
        </Stack>
      </ModalBody>
      <ModalFooter gap={2} flexWrap="wrap">
        <Button type="button" variant="ghost" minH="44px" isDisabled={loading} onClick={onClose}>
          {t(succeeded ? "entitlement.close" : "cancel")}
        </Button>
        {!succeeded && <Button type="button" colorScheme={action === "renew" && review ? "red" : "primary"}
          minH="44px" isLoading={loading} isDisabled={(!overview && !pending) || (!!review && needsConfirm && !confirmed && !pending)}
          onClick={() => void run()}>
          {t(pending ? "entitlement.retry" : review ? "entitlement.apply" : "entitlement.preview")}
        </Button>}
      </ModalFooter>
    </ModalContent>
  </Modal>;
};
