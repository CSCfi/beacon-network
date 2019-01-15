'use strict';

angular.module('beaconApp.version', [
  'beaconApp.version.interpolate-filter',
  'beaconApp.version.version-directive'
])

.value('version', '0.1');
