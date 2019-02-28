'use strict';

angular.module('beaconApp.newbeacon', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/newbeacon', {
    templateUrl: 'newbeacon/newbeacon.html',
    controller: 'NewBeaconCtrl'
  });
}])

.controller('NewBeaconCtrl', ['$scope', '$http', function($scope, $http) {

  $scope.beacons = '';

  $http({
    method: 'GET',
    url: "https://registry-beacon.rahtiapp.fi/services?serviceType=GA4GHBeacon"
  }).then(function successCallback(response) {
      $scope.beacons = response.data;
    }, function errorCallback(response) {
      // console.log(response);
  });

}]);
