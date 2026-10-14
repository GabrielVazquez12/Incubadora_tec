import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';

const css = await readFile(new URL('../src/shared/design/tokens.css', import.meta.url), 'utf8');
const colors = Object.fromEntries([...css.matchAll(/--color-([a-z-]+):\s*(#[0-9a-f]{6});/g)].map(match => [match[1], match[2]]));
function luminance(hex) {
  const linear = [1,3,5].map(i => parseInt(hex.slice(i,i+2),16)/255).map(value => value<=.04045?value/12.92:((value+.055)/1.055)**2.4);
  return linear[0]*.2126+linear[1]*.7152+linear[2]*.0722;
}
function contrast(a,b) {const pair=[luminance(a),luminance(b)].sort((x,y)=>y-x);return (pair[0]+.05)/(pair[1]+.05);}

test('shared text and status tokens meet AA contrast without relying only on color', () => {
  for (const [foreground,background] of [['primary','surface'],['primary','paper'],['ink','paper'],['muted','surface'],['muted','paper'],['navy','surface'],['success','success-soft'],['warning','warning-soft'],['error','error-soft'],['info','info-soft']]) {
    assert.ok(contrast(colors[foreground],colors[background])>=4.5,`${foreground}/${background} must meet 4.5:1`);
  }
  assert.ok(contrast(colors.focus,colors.surface)>=3,'Visible focus must meet 3:1');
});

test('brand fonts are self hosted with swap and mobile header dimensions are explicit', () => {
  assert.equal((css.match(/font-display: swap/g)||[]).length,3);
  assert.ok(!css.includes('fonts.googleapis.com'));
  assert.ok(css.includes('--header-height: 72px')&&css.includes('--header-height: 56px'));
  assert.ok(css.includes('--symbol-height: 48px')&&css.includes('--symbol-height: 40px'));
});
