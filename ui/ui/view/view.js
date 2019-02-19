'use strict';

angular.module('beaconApp.view', ['ngRoute', 'ngMaterial', 'ngMessages', 'ngCookies', 'ui.bootstrap', 'angular.filter'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/view', {
    templateUrl: 'view/view.html',
    controller: 'ViewCtrl'
  });
}])

.controller('ViewCtrl', ['$scope', '$http', '$cookies', function($scope, $http, $cookies) {
  var that = this;
  that.searchText = "";
  that.selectedItem = '';
  that.message = "";
  that.searchClick = false;
  that.searchOptions = 'Advanced Search';

  that.triggerCredentials = false;

  $scope.assembly = {selected: 'GRCh38'};
  $scope.url = '';
  $scope.aggregatorUrl = '';
  that.aaiUrl = '';

  // Advanced search options
  $scope.adv = {assembly: 'GRCh38',
                chr: '1',
                start: '',
                startMin: '',
                startMax: '',
                end: '',
                endMin: '',
                endMax: '',
                ref: '',
                alt: '',
                vt: '',
                ds: 'ALL',
                resp: 'ALL'
              };

  // Read from config file
  $http.get('view/config.json').success(function (data){
    // url for beacon aggregator service
    $scope.aggregatorUrl = data.aggregatorUrl; // query endpoint
    // url for elixir aai client
    that.aaiUrl = data.aaiUrl;
  });

  // Store cookie when notice is acknowledged -> hide notice
  if($cookies.get('info') != null) {
    $scope.alertType = false;
  } else {
    $scope.alertType = true;
  }

  // Disable notice for 2 months on acknowledgement
  $scope.acknowledge = function() {
      var when = new Date();
      var mm =when.getMonth() + 2;
      var y = when.getFullYear();
      $cookies.put("info", "acknowledged", {
        expires: new Date(y, mm),
        path: '/'
      });
      $scope.alertType = false;
  };

  // Old regexp for bases only
  // that.regexp = /^(X|Y|MT|[1-9]|1[0-9]|2[0-2]) \: (\d+) ([ATCGN]+) \> ([ATCGN]+)$/i;
  // New regex that adds variant types
  that.regexp2 = /^(X|Y|MT|[1-9]|1[0-9]|2[0-2]) \: (\d+) ([ATCGN]+) \> (DEL:ME|INS:ME|DUP:TANDEM|DUP|DEL|INS|INV|CNV|SNP|MNP|[ATCGN]+)$/i;
  that.varTypes = ["DEL:ME", "INS:ME", "DUP:TANDEM", "DUP", "DEL", "INS", "INV", "CNV", "SNP", "MNP"]

  // Display or hide login button
  $scope.checkLogin = function() {
    if($cookies.get('access_token')) {
      return true;
    } else {
      return false;
    }
  }

  // Display bona fide status or info on getting it
  $scope.checkBonaFide = function() {
    if($cookies.get('bona_fide_status')) {
      return true;
    } else {
      return false;
    }
  }

  // Remnant
  that.querySearch = function(query){
    that.searchClick = false;
    if (query && that.searchText.length >= 2) {
      return {};
    } else {
      return {};
    }
  }

  // Toggle between basic search and advanced search
  that.toggleSearchOptions = function(value){
    if (value == 'Advanced Search') {
      document.getElementById("basicSearch").style.display = "none";
      document.getElementById("advancedSearch").style.display = "block";
      that.searchOptions = 'Basic Search';
    } else {
      document.getElementById("advancedSearch").style.display = "none";
      document.getElementById("basicSearch").style.display = "inherit";
      that.searchOptions = 'Advanced Search';
    }
  }

  // GET request to Beacon(s)
  $scope.submit = function(searchType) {
    that.loading = true; // spinner animation
    that.message = []; // put websocket responses here
    that.searchClick = true;
    if (searchType == 'basic') {
      if (that.regexp2.test(that.searchText)) {
        that.selectedItem = {type: 'variant', name: that.searchText}
      }
      if (that.selectedItem && that.selectedItem.type == 'variant') {
        that.triggerCredentials = true;
        var params = that.searchText.match(that.regexp2)
        var searchType = '';
        // Check if we are dealing with bases or variant types
        if (that.varTypes.indexOf(params[4]) >= 0) {
          // Variant type
          searchType = `&variantType=${params[4]}`;
        } else {
          // Alternate base
          searchType = `&alternateBases=${params[4]}`;
        }
        var startMin = Number(params[2]) - 1;
        var startMax = Number(params[2]);
        $scope.url = `${$scope.aggregatorUrl}assemblyId=${$scope.assembly.selected}&referenceName=${params[1]}&startMin=${startMin}&startMax=${startMax}&referenceBases=${params[3]}${searchType}&includeDatasetResponses=HIT`;
      } else {
        console.log('search type unselected');
      }
    } else {
      // Remnant..
      that.selectedItem = {type: 'variant'}
      that.searchText = '';
      // Advanced variable placeholders
      var start = '';
      var end = '';
      var alt = '';
      var ds = '';
      // Construct query URL from advanced search form
      // Base URL, these variables we will always use
      $scope.url = `${$scope.aggregatorUrl}assemblyId=${$scope.adv.assembly}&referenceName=${$scope.adv.chr}&referenceBases=${$scope.adv.ref}&includeDatasetResponses=${$scope.adv.resp}`;
      // Handle variables which have options
      // Handle coords
      if ($scope.adv.start) {
        console.log('1');
        var start = `&start=${$scope.adv.start.toString()}`;
      } else {
        console.log('2');
        var start = `&startMin=${$scope.adv.startMin.toString()}&startMax=${$scope.adv.startMax.toString()}`;
      }
      if ($scope.adv.end) {
        var end = `&end=${$scope.adv.end.toString()}`;
      } else if ($scope.adv.endMin && $scope.adv.endMax) {
        var end = `&endMin=${$scope.adv.endMin.toString()}&endMax=${$scope.adv.endMax.toString()}`;
      } else {
        // end will not be used
      }
      // Handle variant transformation
      if ($scope.adv.alt.length) {
        var alt = `&alternateBases=${$scope.adv.alt}`;
      } else {
        var alt = `&variantType=${$scope.adv.vt}`;
      }
      // Handle requested datasets
      if ($scope.adv.ds != 'ALL') {
        var ds = `&datasetIds=${$scope.adv.ds}`;
      }
      // Assemble URL
      $scope.url = `${$scope.url}${start}${end}${alt}${ds}`;
    }

    console.log($scope.url);

    $scope.adv = {assembly: 'GRCh38',
    chr: '1',
    start: '',
    startMin: '',
    startMax: '',
    end: '',
    endMin: '',
    endMax: '',
    ref: '',
    alt: '',
    vt: '',
    ds: 'ALL',
    resp: 'ALL'
  };


    // Prepend aggregator url with secure websocket protocol
    $scope.wsUrl = 'wss://' + $scope.url;
    var websocket = new WebSocket($scope.wsUrl);

    websocket.onopen = function(event) {
      // The connection was opened
      // console.log('websocket opened')
    }; 
    websocket.onclose = function(event) { 
      // The connection was closed
      $scope.$apply(function() {
        that.loading = false // stop spinner
      })
      // console.log('websocket closed')
    }; 
    websocket.onmessage = function(event) {
      $scope.$apply(function() {
        // New message arrived
        // console.log('websocket received data')
        that.message.push(angular.fromJson(event.data))
      });
    }; 
    websocket.onerror = function(event) { 
      // There was an error with your WebSocket
      $scope.$apply(function() {
        that.loading = false // stop spinner
      })
      // console.log('websocket errored')
    };
  }

  $scope.searchExample = function(searchtype) {
    that.toggleSearchOptions('default');  // set to basic search if user is in advanced search
    that.searchClick = false;
    if (searchtype == 'variant') {
      var variants = ['MT : 10 T > C', 'MT : 7600 G > A', 'MT : 195 TTACTAAAGT > CCACTAAAGT', 'MT : 14037 A > G',
                      '1 : 104431390 C > INS', '19 : 36585458 A > INS', '19 : 36909437 C > DUP', '1 : 2847963 G > DUP',
                      '1 : 1393861 T > CNV', '1 : 85910910 C > CNV', '1 : 218144328 A > INV']
      // Select example variant from list at random
      that.searchText = variants[Math.floor(Math.random()*variants.length)];
      document.querySelector('#autoCompleteId').focus();
    } else {
      that.searchText = 'Unknown';
    }
  }

	}]);
