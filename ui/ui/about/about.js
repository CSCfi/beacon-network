'use strict';

angular.module('beaconApp.about', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/about', {
    templateUrl: 'about/about.html',
    controller: 'AboutCtrl'
  });
}])

.controller('AboutCtrl', ['$scope', '$http', function($scope, $http) {

  // Beacons from Registry will be put here
  $scope.beacons = '';
  // Beacon online status will be put here
  $scope.statusList = {};

  $http({
    method: 'GET',
    url: "https://registry-beacon.rahtiapp.fi/services?serviceType=GA4GHBeacon"
  }).then(function successCallback(response) {
      // We have received list of Beacons from Registry
      $scope.beacons = response.data;
      var i = 0;
      // Ping Beacons to check their statuses
      for (i = 0; i < response.data.length; i++) {
        $scope.statusList[response.data[i].id] = $http({method: 'GET', url: response.data[i].welcomeUrl});;
      }
    }, function errorCallback(response) {
      // console.log(response);
  });

  // Read from status list if service is online
  $scope.beaconStatus = function(beacon) {
    if ($scope.statusList[beacon]) {
      return true;
    } else {
      return false;
    }
  }

}]);
