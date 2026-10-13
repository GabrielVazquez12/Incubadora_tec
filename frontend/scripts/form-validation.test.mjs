import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { passwordError } from '../src/shared/registration/validation.js';

test('bcrypt limits count UTF-8 bytes and preserve password spaces', () => {
  assert.equal(passwordError('Valid password 2026'), '');
  assert.equal(passwordError('á'.repeat(36)), '');
  assert.notEqual(passwordError('á'.repeat(37)), '');
  assert.notEqual(passwordError('x'.repeat(73)), '');
  assert.notEqual(passwordError('short'), '');
  assert.equal(passwordError('legacy', 1), '');
});

test('innovation catalogs agree between the API and the frontend', () => {
  const frontend = JSON.parse(readFileSync(new URL('../src/modules/innovacion/catalogs.json', import.meta.url)));
  const backend = JSON.parse(readFileSync(new URL('../../backend/app/innovation_catalog.json', import.meta.url)));
  assert.deepEqual(frontend, backend);
});
