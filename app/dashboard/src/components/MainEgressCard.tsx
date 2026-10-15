import {
  Alert, AlertIcon, Button, FormControl, FormLabel, HStack, Input, Tooltip,
  Modal, ModalBody, ModalCloseButton, ModalContent, ModalFooter, ModalHeader,
  ModalOverlay, Select, SimpleGrid, Stack, Text, useDisclosure, useToast,
} from "@chakra-ui/react";
import { AdjustmentsHorizontalIcon } from "@heroicons/react/24/outline";
import { FC, useState } from "react";
import { useTranslation } from "react-i18next";
import { useMutation, useQuery, useQueryClient } from "react-query";
import { fetch } from "service/http";
import { MainEgressProbe, egressErrorCode } from "./MainEgressProbe";

type Protocol = "http" | "socks";
type UdpMode = "legacy" | "proxy" | "tcp_only";
type Egress = {
  configured: boolean;
  protocol?: Protocol;
  udp_mode?: UdpMode;
  server?: string;
  port?: number;
  username?: string;
  has_password?: boolean;
};
type FormState = {
  protocol: Protocol;
  udp_mode: UdpMode;
  server: string;
  port: string;
  username: string;
  password: string;
};

const formFrom = (egress?: Egress): FormState => ({
  protocol: egress?.protocol || "http",
  udp_mode: egress?.udp_mode || "legacy",
  server: egress?.server || "",
  port: String(egress?.port || 1080),
  username: egress?.username || "",
  password: "",
});

export const MainEgressCard: FC<{ nodeName: string; enabled?: boolean }> = ({
  nodeName, enabled = true,
}) => {
  const { t } = useTranslation();
  const toast = useToast();
  const queryClient = useQueryClient();
  const modal = useDisclosure();
  const [form, setForm] = useState<FormState>(formFrom());
  const endpoint = "/node/main/egress";
  const queryKey = ["main-egress"];
  const available = enabled;
  const { data, isError, isFetching, refetch } = useQuery<Egress>(queryKey, () => fetch(endpoint), {
    enabled: available, retry: false,
  });
  const errorMessage = (error: unknown) => {
    const code = egressErrorCode(error);
    return t(`${code.startsWith("MAIN_") ? "nodes.mainEgress.code" : "nodes.egressProbe.code"}.${code}`,
      {defaultValue:t("nodes.mainEgress.code.MAIN_REQUEST_UNCONFIRMED")});
  };

  const save = useMutation(() => fetch(endpoint, {
    method: "PUT",
    retry: 0, timeout: 90000,
    body: {
      protocol: form.protocol,
      udp_mode: form.udp_mode,
      server: form.server.trim(),
      port: Number(form.port),
      username: form.username.trim() || null,
      password: form.password || null,
    },
  }), {
    onSuccess: () => {
      queryClient.invalidateQueries(queryKey);
      modal.onClose();
      toast({ status: "success", title: t("nodes.mainEgress.saved") });
    },
    onError: (error) => { toast({status:"error",title:errorMessage(error)}); },
  });

  const clear = useMutation(() => fetch(endpoint, { method: "DELETE", retry: 0, timeout: 90000 }), {
    onSuccess: () => {
      queryClient.invalidateQueries(queryKey);
      modal.onClose();
      toast({ status: "success", title: t("nodes.mainEgress.cleared") });
    },
    onError: (error) => { toast({status:"error",title:errorMessage(error)}); },
  });

  const openManager = () => {
    setForm(formFrom(data));
    modal.onOpen();
  };
  const set = (key: keyof FormState, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));
  const port = Number(form.port);
  const credentialsValid = (!form.username.trim() && !form.password) || Boolean(
    form.username.trim() && (form.password ||
      (data?.has_password && form.username.trim() === (data.username || "")))
  );
  const canSave = Boolean(form.server.trim() && Number.isInteger(port) && port >= 1 && port <= 65535 && credentialsValid);

  return <>
    <HStack w="full" minH="38px" justify="space-between" borderWidth="1px"
      borderColor="gray.200" _dark={{ borderColor: "gray.600" }} borderRadius="md" px={3} py={2}>
      <HStack spacing={2} minW={0}>
        <AdjustmentsHorizontalIcon width="18" />
        <Text fontSize="sm" fontWeight="medium" noOfLines={1}>{t("nodes.egress.title")}</Text>
        {data && <Text fontSize="xs" color="gray.500" flexShrink={0} display={{ base: "none", sm: "block" }}>
          {data?.configured ? t("nodes.egress.configured") : t("nodes.egress.empty")}
        </Text>}
      </HStack>
      <Button type="button" size="xs" variant="outline" colorScheme="primary" onClick={openManager}
        isDisabled={!available || !data || isError || isFetching} flexShrink={0}>{t("nodes.egress.manage")}</Button>
    </HStack>
    {isError && <Alert status="error" mt={2} borderRadius="md">
      <AlertIcon /><Text fontSize="xs" flex={1}>{t("nodes.mainEgress.loadFailed")}</Text>
      <Button type="button" size="xs" onClick={() => refetch()} isLoading={isFetching}>{t("nodes.relay.retry")}</Button>
    </Alert>}

    <Modal isOpen={modal.isOpen} onClose={() => { if (!save.isLoading && !clear.isLoading) modal.onClose(); }} size="lg" isCentered scrollBehavior="inside">
      <ModalOverlay />
      <ModalContent mx={3}>
        <ModalHeader fontSize="md">{nodeName} · {t("nodes.egress.manage")}</ModalHeader>
        <ModalCloseButton isDisabled={save.isLoading || clear.isLoading} />
        <ModalBody pt={0}>
          <Alert status="info" mb={4} borderRadius="md" alignItems="flex-start">
            <AlertIcon /><Text fontSize="xs">{t("nodes.mainEgress.hint")}</Text>
          </Alert>
          <Stack spacing={3}>
            <SimpleGrid columns={{ base: 1, md: 2 }} spacing={3}>
              <FormControl>
                <FormLabel fontSize="sm">{t("nodes.egress.protocol")}</FormLabel>
                <Select size="sm" value={form.protocol} isDisabled={save.isLoading || clear.isLoading}
                  onChange={(e) => setForm((current) => ({ ...current,
                    protocol: e.target.value as Protocol,
                    udp_mode: e.target.value === "http" && current.udp_mode === "proxy" ? "legacy" : current.udp_mode,
                  }))}>
                  <option value="http">HTTP</option><option value="socks">SOCKS5</option>
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm" display="flex" alignItems="center" gap={2}>
                  {t("nodes.egress.udpMode")}
                  <Tooltip label={t("nodes.egress.udpHelp")} hasArrow placement="top">
                    <Text as="span" tabIndex={0} aria-label={t("nodes.egress.udpHelp")}
                      fontSize="xs" color="gray.500" cursor="help">ⓘ</Text>
                  </Tooltip>
                </FormLabel>
                <Select size="sm" value={form.udp_mode} isDisabled={save.isLoading || clear.isLoading} onChange={(e) => set("udp_mode", e.target.value)}>
                  <option value="legacy">{t("nodes.egress.udpLegacy")}</option>
                  <option value="proxy" disabled={form.protocol !== "socks"}>{t("nodes.egress.udpProxy")}</option>
                  <option value="tcp_only">{t("nodes.egress.udpTcpOnly")}</option>
                </Select>
              </FormControl>
              <FormControl isRequired>
                <FormLabel fontSize="sm">{t("nodes.egress.server")}</FormLabel>
                <Input size="sm" value={form.server} placeholder="proxy.example.com" isDisabled={save.isLoading || clear.isLoading}
                  onChange={(e) => set("server", e.target.value)} />
              </FormControl>
              <FormControl isRequired>
                <FormLabel fontSize="sm">{t("nodes.egress.port")}</FormLabel>
                <Input size="sm" type="number" value={form.port} isDisabled={save.isLoading || clear.isLoading}
                  onChange={(e) => set("port", e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm">{t("nodes.egress.username")}</FormLabel>
                <Input size="sm" value={form.username} isDisabled={save.isLoading || clear.isLoading}
                  onChange={(e) => set("username", e.target.value)} />
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm" display="flex" alignItems="center" gap={2}>
                  {t("nodes.egress.passwordShort")}
                  <Tooltip label={t("nodes.egress.password")} hasArrow placement="top">
                    <Text as="span" tabIndex={0} aria-label={t("nodes.egress.password")}
                      fontSize="xs" color="gray.500" cursor="help">ⓘ</Text>
                  </Tooltip>
                </FormLabel>
                <Input size="sm" type="password" value={form.password} isDisabled={save.isLoading || clear.isLoading}
                  placeholder={data?.has_password ? "••••••••" : ""}
                  onChange={(e) => set("password", e.target.value)} />
              </FormControl>
            </SimpleGrid>
            <MainEgressProbe nodeName={nodeName} disabled={!canSave || save.isLoading || clear.isLoading}
              draft={{protocol:form.protocol,udp_mode:form.udp_mode,server:form.server.trim(),port:Number(form.port),
                username:form.username.trim() || null,password:form.password || null}} />
          </Stack>
        </ModalBody>
        <ModalFooter gap={2} flexWrap="wrap">
          {data?.configured && <Button size="sm" variant="ghost" colorScheme="red" mr="auto"
            onClick={() => clear.mutate()} isLoading={clear.isLoading} isDisabled={save.isLoading}>
            {t("nodes.mainEgress.clear")}
          </Button>}
          <Button size="sm" onClick={modal.onClose} isDisabled={save.isLoading || clear.isLoading}>{t("cancel")}</Button>
          <Button size="sm" colorScheme="primary" onClick={() => save.mutate()}
            isLoading={save.isLoading} isDisabled={!canSave || clear.isLoading}>
            {t("nodes.mainEgress.save")}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  </>;
};
