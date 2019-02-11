'use strict';

angular.module('beaconApp.about', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/about', {
    templateUrl: 'about/about.html',
    controller: 'AboutCtrl'
  });
}])

.controller('AboutCtrl', ['$scope', '$http', function($scope, $http) {

  $scope.beacons = '';

  $http({
    method: 'GET',
    url: "https://aggregator-beacon.rahtiapp.fi/services?serviceType=GA4GHBeacon"
  }).then(function successCallback(response) {
      $scope.beacons = response.data;
    }, function errorCallback(response) {
      // console.log(response);
  });

}]);
