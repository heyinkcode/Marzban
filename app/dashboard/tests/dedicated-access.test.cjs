const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '..');
const helper = fs.readFileSync(path.join(root, 'src/service/dedicatedAccess.ts'), 'utf8');
const component = fs.readFileSync(path.join(root, 'src/components/DedicatedAccessModal.tsx'), 'utf8');
function load(responder = () => ({}), storageFailure = false) {
  const items = new Map(), requests = [];
  const box = { exports: {}, crypto, sessionStorage: {
    getItem(key) { if (storageFailure) throw Error('blocked'); return items.get(key) || null; },
    setItem(key, value) { if (storageFailure) throw Error('blocked'); items.set(key, value); },
    removeItem: key => items.delete(key),
  }, require: name => { assert.equal(name, 'service/http'); return { fetch: async (url, options = {}) => {
    requests.push({url, options}); return responder(url, options);
  } }; } };
  vm.runInNewContext(ts.transpileModule(helper, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, box);
  return { api: box.exports, items, requests };
}
test('production helper persists one UUID and does not overwrite an unresolved opposite intent', () => {
  const {api, items} = load();
  const first = api.startPending('admin', 'user', 3, true);
  const replay = api.startPending('admin', 'user', 3, false);
  assert.equal(replay.operation_id, first.operation_id);
  assert.equal(replay.granted, true);
  assert.equal(items.size, 1);
  assert.notEqual(api.startPending('other-admin', 'user', 3, true).operation_id, first.operation_id);
  api.finishPending('admin', 'user', 3, {sync_state:'pending'});
  assert.ok(api.readPending('admin', 'user', 3));
  api.finishPending('admin', 'user', 3, {sync_state:'synced',granted:false});
  assert.equal(api.readPending('admin', 'user', 3), null);
});
test('storage failure refuses creating a new request and sends no network write', () => {
  const {api, requests} = load(undefined, true);
  assert.throws(() => api.startPending('admin','user',3,true), /blocked/);
  assert.equal(requests.length, 0);
});
test('PUT and DELETE use the durable UUID with no automatic retries or account mutations', async () => {
  const {api, requests} = load();
  const operation = {operation_id:crypto.randomUUID(),granted:true};
  await api.submitAccess('user',3,operation);
  await api.submitAccess('user',3,{...operation,granted:false});
  assert.equal(requests[0].url,'/user/user/dedicated-nodes/3');
  assert.equal(requests[0].options.method,'PUT');
  assert.equal(requests[1].options.method,'DELETE');
  for (const {options} of requests) {
    assert.equal(options.retry,0);
    assert.deepEqual(Object.keys(options.body),['operation_id']);
    assert.equal(options.body.operation_id,operation.operation_id);
  }
});
test('receipt is read-only and unsupported panel catalog is rejected', async () => {
  const {api, requests} = load(() => ({capability:'old-version',nodes:[]}));
  await api.accessReceipt({operation_id:'example',granted:true});
  assert.equal(requests[0].options.method,undefined);
  assert.equal(requests[0].options.retry,0);
  await assert.rejects(api.loadUserAccess('user'),/UNSUPPORTED_DEDICATED_ACCESS/);
  assert.ok(requests.every(request => !request.options.body));
});
test('public reopening confirmation is scoped to node policy endpoint', async () => {
  const {api, requests} = load();
  await api.saveNodePolicy(3,'public',true);
  await api.saveNodePolicy(4,'restricted',true);
  assert.equal(requests[0].url,'/node/3/access');
  assert.equal(requests[0].options.body.confirm_public_access,true);
  assert.equal(requests[1].options.body.confirm_public_access,false);
  assert.ok(requests.every(request => request.options.retry===0));
});
test('new UI uses original modals with pending feedback and no batch or reset endpoint', () => {
  for (const value of ['ModalOverlay','ModalCloseButton','scrollBehavior="inside"','query.isError',
    'dedicated.pending','dedicated.receipt','dedicated.confirmPublic','storageError']) assert.ok(component.includes(value),value);
  for (const forbidden of ['resetUsage','revokeSubscription','Promise.all','/core/restart']) assert.ok(!component.includes(forbidden));
  const nodes = fs.readFileSync(path.join(root,'src/components/NodesModal.tsx'),'utf8');
  const table = fs.readFileSync(path.join(root,'src/components/UsersTable.tsx'),'utf8');
  assert.ok(nodes.includes('<DedicatedNodeSettings nodes={nodeList} />'));
  // Desktop and expanded mobile rows share ActionButtons: one definition, not a second mobile button.
  assert.equal((table.match(/<DedicatedUserAccessButton/g)||[]).length,1);
  assert.ok(component.includes('actionRef.current?.focus()'));
  assert.ok(component.includes('[busy, locked]'));
  assert.ok(nodes.includes('form.register("access_mode")'));
  assert.ok(nodes.includes('maxW="800px"'));
});
test('all dedicated strings are present in all four existing languages', () => {
  const keys = Object.keys(JSON.parse(fs.readFileSync(path.join(root,'public/statics/locales/en.json'),'utf8')))
    .filter(key=>key.startsWith('dedicated.'));
  assert.ok(keys.length>35);
  for (const lang of ['zh','en','ru','fa']) {
    const strings = JSON.parse(fs.readFileSync(path.join(root,`public/statics/locales/${lang}.json`),'utf8'));
    for (const key of keys) assert.ok(typeof strings[key]==='string' && strings[key].trim(),`${lang}: ${key}`);
    for (const match of component.matchAll(/t\("([a-zA-Z.]+)"\)/g)) assert.ok(strings[match[1]],`${lang}: ${match[1]}`);
  }
});
