'use strict';

describe('beaconApp.version module', function() {
  beforeEach(module('beaconApp.version'));

  describe('version service', function() {
    it('should return current version', inject(function(version) {
      expect(version).toEqual('0.1');
    }));
  });
});
