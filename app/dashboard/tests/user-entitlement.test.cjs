const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const component = fs.readFileSync(path.join(root, 'src/components/UserEntitlementDialog.tsx'), 'utf8');
const editor = fs.readFileSync(path.join(root, 'src/components/UserDialog.tsx'), 'utf8');
const namespace = {exports: {}, require: name => name === 'service/http' ? {} : require(name)};
vm.runInNewContext(ts.transpileModule(component, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX }
}).outputText, namespace);

test('production quota conversion is exact beyond the safe integer limit', () => {
  const parse = namespace.exports.parseEntitlementGiB;
  const unit = 1073741824n;
  for (const [input, numerator] of [['1',1000n],['0.001',1n],['12.5',12500n],
                                   ['8398910.234',8398910234n],['99999999.999',99999999999n]]) {
    assert.equal(parse(input), String(numerator * unit / 1000n), input);
  }
  for (const input of ['', '0', '0.000', '-1', '1.0001', '01', '1e3', 'Infinity', '100000000']) {
    assert.equal(parse(input), null, input);
  }
});

test('all four languages include each action, confirmation and unknown-result state', () => {
  const patterns = [...(component + editor).matchAll(/"(entitlement\.[a-zA-Z.]+)"/g)].map(match => match[1]);
  const keys = new Set(patterns.filter(key => !key.endsWith('.')));
  for (const action of ['extend', 'add', 'renew', 'restore']) {
    keys.add('entitlement.' + action);
    keys.add('entitlement.help.' + action);
  }
  keys.add('entitlement.confirm.renew');
  keys.add('entitlement.confirm.restore');
  for (const locale of ['en', 'zh', 'ru', 'fa']) {
    const strings = JSON.parse(fs.readFileSync(path.join(root, 'public/statics/locales', locale + '.json'), 'utf8'));
    for (const key of keys) assert.ok(strings[key]?.trim(), locale + ': ' + key);
    for (const placeholder of ['id','date','quota']) assert.ok(strings['entitlement.resetDetail'].includes('{{' + placeholder + '}}'));
  }
});
