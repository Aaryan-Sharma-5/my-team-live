import { expect, test } from 'vitest';
import { nextPlayback } from './playback';

test('play and pause preserve position; replay resets at full time', () => {
  expect(nextPlayback(10, 20, true)).toEqual({index:10,running:false});
  expect(nextPlayback(10, 20, false)).toEqual({index:10,running:true});
  expect(nextPlayback(20, 20, false)).toEqual({index:-1,running:true});
});
