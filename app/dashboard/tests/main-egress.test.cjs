const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),vm=require('node:vm'),ts=require('typescript');
const root=path.resolve(__dirname,'..');
const read=name=>fs.readFileSync(path.join(root,'src/components',name),'utf8');
const card=read('MainEgressCard.tsx'),probe=read('MainEgressProbe.tsx');
function load(source,imports={}){const box={exports:{},require:name=>imports[name]||require(name)};vm.runInNewContext(ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,box);return box.exports;}
test('original Node components remain byte-identical except the explicit dedicated access additions',()=>{
 const expected={'NodesModal.tsx':'464c5af195a667f421e47eee90871be10b9fadfc510c27fa68336591dab67545','NodeEgressCard.tsx':'3b2c6a9d54967f6c58bb210377b8ce2b7459bd17ca2f7430370e6497cd4856c9','EgressProbe.tsx':'c9abcde57569177e6dc7fe84a957c66d0759af42a999d66da41ed88afd249cba','NodeRelayCard.tsx':'2aee03ba9f574326bebfba6e72e340ad834ece77208f3d1ee9b4f0dc0348dfd0','NodeHealthCard.tsx':'1fe3e14983817421d6649dda7227b004746b09adb87f5eaf68811159c1f8940b'};
 for(const [name,hash] of Object.entries(expected)){
  let source=read(name).replace(/\r\n/g,'\n');
  if(name==='NodesModal.tsx'){
   // Exclude only reviewed, additive access controls; keep the old byte-level
   // guarantee for every pre-existing Node control, layout and subcomponent.
   source=source.replace('  Select,\n','')
    .replace('import { DedicatedNodeSettings } from "./DedicatedAccessModal";\n','')
    .replace('            <DedicatedNodeSettings nodes={nodeList} />\n','')
    .replace(/        \{addAsHost && \(\n          <FormControl>\n[\s\S]*?          <\/FormControl>\n        \)\}\n/,'');
  }
  assert.equal(crypto.createHash('sha256').update(source).digest('hex'),hash,name);
 }
});
test('only main card adds the independent management row and independent cache/endpoint',()=>{
 const usage=read('MainUsageCard.tsx');assert.match(usage,/<MainEgressCard/);assert.match(card,/const endpoint = "\/node\/main\/egress"/);assert.match(card,/const queryKey = \["main-egress"\]/);
 assert.ok(!card.includes('nodeId'));assert.ok(!probe.includes('nodeId'));assert.match(probe,/"\/node\/main\/egress\/test"/);
 assert.ok(!card.includes('NodeEgressCard'));assert.match(card,/retry: 0, timeout: 90000/);
});
test('errors expose only bounded codes, never raw exceptions, and unknown mutation outcome stays unconfirmed',()=>{
 const component=load(probe,{'service/http':{fetch:()=>{throw Error('No network')}}});
 assert.equal(component.egressErrorCode({data:{detail:{code:'MAIN_CORE_BUSY'}}}),'MAIN_CORE_BUSY');
 assert.equal(component.egressErrorCode({data:{detail:{code:'password:secret'}}}),'MAIN_REQUEST_UNCONFIRMED');
 assert.equal(component.egressErrorCode(new Error('secret')),'MAIN_REQUEST_UNCONFIRMED');
 assert.match(card,/isError \|\| isFetching/);assert.match(card,/nodes.mainEgress.loadFailed/);assert.match(card,/onClick=\{\(\) => refetch\(\)\}/);
});
test('all main strings and safe error codes exist in all four languages with interpolation parity',()=>{
 const english=JSON.parse(fs.readFileSync(path.join(root,'public/statics/locales/en.json'),'utf8'));
 const keys=Object.keys(english).filter(key=>key.startsWith('nodes.mainEgress.'));
 assert.ok(keys.length>=22);
 for(const language of ['zh','en','ru','fa']){const value=JSON.parse(fs.readFileSync(path.join(root,`public/statics/locales/${language}.json`),'utf8'));
  for(const key of keys){assert.ok(value[key]&&value[key].trim(),language+key);const vars=s=>[...s.matchAll(/\{\{([^}]+)\}\}/g)].map(m=>m[1]).sort();assert.deepEqual(vars(value[key]),vars(english[key]));}}
});
test('main draft diagnostics are cancellable, bounded and do not restart the business core',()=>{
 assert.match(probe,/sequence.current === current/);assert.match(probe,/controller.current\?\.abort\(\)/);assert.match(probe,/timeout:45000/);assert.match(probe,/nodes.mainEgress.probeScope/);assert.ok(!probe.includes('/restart'));
 assert.match(card,/size="lg"/);assert.match(card,/form.password \|\| null/);assert.match(card,/data\?\.has_password/);
});
