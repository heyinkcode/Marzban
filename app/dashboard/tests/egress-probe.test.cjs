const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');const path=require('node:path');const vm=require('node:vm');const ts=require('typescript');
const root=path.resolve(__dirname,'..');
const source=fs.readFileSync(path.join(root,'src/components/EgressProbe.tsx'),'utf8');
const modal=fs.readFileSync(path.join(root,'src/components/NodeEgressCard.tsx'),'utf8');
function load(code,locals={}){const box={exports:{},require:name=>locals[name]||require(name)};vm.runInNewContext(ts.transpileModule(code,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,box);return box.exports;}
const component=load(source,{'service/http':{fetch:()=>{throw Error('No network in SSR')}}});
test('probe authenticates through existing HTTP helper and never restarts',()=>{
 assert.match(source,/from "service\/http"/);assert.match(source,/egress\/test/);assert.match(source,/retry:0, timeout:45000/);
 assert.ok(!source.includes('/restart'));assert.match(source,/signal:request.signal/);assert.match(source,/sequence.current === current/);
});
test('draft changes and unmount invalidate results and cancel waiting',()=>{
 assert.match(source,/JSON.stringify\(\[nodeId, draft, timeout, attempts\]\)/);
 assert.match(source,/setResult\(null\); setError\(null\)/);assert.match(source,/controller.current\?\.abort\(\)/);
 assert.match(source,/WAIT_CANCELLED/);assert.match(source,/useState\(false\)/);
});
test('error rendering uses a bounded code rather than raw credential-bearing errors',()=>{
 assert.equal(component.egressErrorCode({data:{detail:{code:'NODE_BUSY'}}}),'NODE_BUSY');
 assert.equal(component.egressErrorCode({data:{detail:{code:'secret-user:secret-password'}}}),'NODE_CONTROL_UNAVAILABLE');
 assert.equal(component.egressErrorCode(new Error('password')),'NODE_CONTROL_UNAVAILABLE');
});
test('original fields, modal width, UDP and saved-password semantics remain',()=>{
 for(const token of ['size="lg"','<ModalContent mx={3}>','udpLegacy','udpProxy','udpTcpOnly','form.password || null','data?.has_password','nodes.egress.clear','nodes.egress.save'])assert.ok(modal.includes(token),token);
 assert.match(modal,/<EgressProbe nodeId=\{nodeId\}/);assert.match(modal,/save.isLoading \|\| clear.isLoading/);
});
test('all probe strings and codes translated in four menu languages',()=>{
 const english=JSON.parse(fs.readFileSync(path.join(root,'public/statics/locales/en.json'),'utf8'));
 const keys=Object.keys(english).filter(key=>key.startsWith('nodes.egressProbe.'));
 for(const lang of ['zh','en','ru','fa']){const strings=JSON.parse(fs.readFileSync(path.join(root,`public/statics/locales/${lang}.json`),'utf8'));
  for(const key of keys){assert.ok(typeof strings[key]==='string'&&strings[key].trim(),lang+': '+key);
   const variables=value=>[...value.matchAll(/\{\{([^}]+)\}\}/g)].map(m=>m[1]).sort();assert.deepEqual(variables(strings[key]),variables(english[key]));}}
});
test('actual React/Chakra diagnostic component SSR renders translated collapsed controls',async()=>{
 const React=require('react');const {renderToString}=require('react-dom/server');const {ChakraProvider}=require('@chakra-ui/react');const {I18nextProvider}=require('react-i18next');const i18next=require('i18next');
 for(const lang of ['zh','en','ru','fa']){const strings=JSON.parse(fs.readFileSync(path.join(root,`public/statics/locales/${lang}.json`),'utf8'));
  const i18n=i18next.createInstance();await i18n.init({lng:lang,resources:{[lang]:{translation:strings}},interpolation:{escapeValue:false}});
  const html=renderToString(React.createElement(ChakraProvider,null,React.createElement(I18nextProvider,{i18n},React.createElement(component.EgressProbe,{nodeId:1,nodeName:'Node 01',disabled:false,draft:{protocol:'socks',udp_mode:'tcp_only',server:'proxy.example.test',port:1080,username:null,password:null}}))));
  assert.ok(html.includes(strings['nodes.egressProbe.title']));assert.ok(html.includes(strings['nodes.egressProbe.test']));assert.ok(html.includes('aria-expanded="false"'));assert.ok(!html.includes('203.0.113.42'));
 }
});
