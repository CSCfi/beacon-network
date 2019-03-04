'use strict';

angular.module('beaconApp.newbeacon', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/newbeacon', {
    templateUrl: 'newbeacon/newbeacon.html',
    controller: 'NewBeaconCtrl'
  });
}])

.controller('NewBeaconCtrl', ['$scope', '$http', function($scope, $http) {

  $scope.beaconURL = '';
  $scope.beaconInfo = {};

  $scope.fetchBeaconInfo = function() {
    $http({
      method: 'GET',
      url: $scope.beaconURL
    }).then(function successCallback(response) {
        $scope.beaconInfo = response.data;
        // document.getElementById("fetchedInfo").style.display = "block";
      }, function errorCallback(response) {
        // console.log(response);
    });
  }

  

}]);
