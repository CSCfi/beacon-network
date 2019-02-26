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
  $scope.adv = {
    assembly: 'GRCh38',
    chr: '1',
    coordBase: 0,
    start: '',
    startMin: '',
    startMax: '',
    end: '',
    endMin: '',
    endMax: '',
    ref: '',
    alt: '',
    vt: 'Unspecified',
    ds: '',
    resp: ''
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

  // Exlusive or (XOR) manager for coordinates and variant transformation
  that.manageAdvancedSearchOptions = function() {
    // If using exact start, disable startMin and startMax
    if (document.getElementById('advStart').value > 0) {
      document.getElementById('advStartMin').disabled = true;
      document.getElementById('advStartMax').disabled = true;
    } else {
      document.getElementById('advStartMin').disabled = false;
      document.getElementById('advStartMax').disabled = false;
    }
    // If using exact end, disable endMin and endMax
    if (document.getElementById('advEnd').value > 0) {
      document.getElementById('advEndMin').disabled = true;
      document.getElementById('advEndMax').disabled = true;
    } else {
      document.getElementById('advEndMin').disabled = false;
      document.getElementById('advEndMax').disabled = false;
    }
    // If using startMin or startMax, disable start
    if (document.getElementById('advStartMin').value > 0 || document.getElementById('advStartMax').value > 0) {
      document.getElementById('advStart').disabled = true;
      document.getElementById('advStart').required = false;
      document.getElementById('advStartMin').required = true;
      document.getElementById('advStartMax').required = true;
    } else {
      document.getElementById('advStart').disabled = false;
      document.getElementById('advStart').required = true;
      document.getElementById('advStartMin').required = false;
      document.getElementById('advStartMax').required = false;
    }
    // If using endMin or endMax, disable end
    if (document.getElementById('advEndMin').value > 0 || document.getElementById('advEndMax').value > 0) {
      document.getElementById('advEnd').disabled = true;
      document.getElementById('advStart').required = false;
      document.getElementById('advEndMin').required = true;
      document.getElementById('advEndMax').required = true;
    } else {
      document.getElementById('advEnd').disabled = false;
      document.getElementById('advEnd').required = false;
      document.getElementById('advEndMin').required = false;
      document.getElementById('advEndMax').required = false;
    }
    // If using altBases, disable variantType -------- WHY DOESN'T THIS WORK?
    if (document.getElementById('advAlt').value != '' && document.getElementById('advAlt').value.length > 0) {
      document.getElementById('advVt').disabled = true;
    } else {
      document.getElementById('advVt').disabled = false;
    }
    // If using variantType, disable altBases
    if ($scope.adv.vt == 'Unspecified') {
      document.getElementById('advAlt').disabled = false;
      document.getElementById('advAlt').required = true;
    } else {
      document.getElementById('advAlt').disabled = true;
      document.getElementById('advAlt').required = false;
      $scope.adv.alt = '';  // empty the altBases field if it was filled
    }
  }

  // Toggle between basic search and advanced search
  that.toggleSearchOptions = function(value){
    if (value == 'Advanced Search') {
      document.getElementById('advStart').required = true;
      document.getElementById("basicSearch").style.display = "none";
      document.getElementById("advancedSearch").style.display = "block";
      that.searchOptions = 'Basic Search';
    } else {
      document.getElementById("advancedSearch").style.display = "none";
      document.getElementById("basicSearch").style.display = "inherit";
      that.searchOptions = 'Advanced Search';
      that.searchText = '';
    }
  }

  $scope.advResetForm = function() {
    $scope.adv = {
      assembly: 'GRCh38',
      chr: '1',
      coordBase: 0,
      start: '',
      startMin: '',
      startMax: '',
      end: '',
      endMin: '',
      endMax: '',
      ref: '',
      alt: '',
      vt: 'Unspecified',
      ds: '',
      resp: ''
    };
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
      $scope.url = `${$scope.aggregatorUrl}assemblyId=${$scope.adv.assembly}&referenceName=${$scope.adv.chr}&referenceBases=${$scope.adv.ref}&includeDatasetResponses=HIT`;
      // Handle variables which have options
      // Handle coords
      // Handle coordinate base-system
      // Kind of awkward solution for now.. Advanced search is in beta anyway
      var cb = {
        s: 0,
        smi: 0,
        sma: 0,
        e: 0,
        emi: 0,
        ema: 0
      }
      if ($scope.adv.coordBase == 1) {
        if ($scope.adv.start != '' && $scope.adv.start > 0) {cb.s = $scope.adv.start - 1;}
        if ($scope.adv.startMin != '' && $scope.adv.startMin > 0) {cb.smi = $scope.adv.startMin - 1;}
        if ($scope.adv.startMax != '' && $scope.adv.startMax > 0) {cb.sma = $scope.adv.startMax - 1;}
        if ($scope.adv.end != '' && $scope.adv.end > 0) {cb.e = $scope.adv.end - 1;}
        if ($scope.adv.endMin != '' && $scope.adv.endMin > 0) {c.emi = $scope.adv.endMin - 1;}
        if ($scope.adv.endMax != '' && $scope.adv.endMax > 0) {c.ema = $scope.adv.endMax - 1;}
      } else {
        cb.s = $scope.adv.start;
        cb.smi = $scope.adv.startMin;
        cb.sma = $scope.adv.startMax;
        cb.e = $scope.adv.end;
        cb.emi = $scope.adv.endMin;
        cb.ema = $scope.adv.endMax;
      }
      // ---
      if ($scope.adv.start) {
        var start = `&start=${cb.s.toString()}`;
      } else {
        var start = `&startMin=${cb.smi.toString()}&startMax=${cb.sma.toString()}`;
      }
      if ($scope.adv.end) {
        var end = `&end=${cb.e.toString()}`;
      } else if ($scope.adv.endMin && $scope.adv.endMax) {
        var end = `&endMin=${cb.emi.toString()}&endMax=${cb.ema.toString()}`;
      } else {
        // end will not be used
      }
      // Handle variant transformation
      if ($scope.adv.alt.length) {
        var alt = `&alternateBases=${$scope.adv.alt}`;
      } else {
        var alt = `&variantType=${$scope.adv.vt}`;
      }
      // Handle requested datasets -- CAN'T HANDLE THIS RIGHT NOW..
      // if ($scope.adv.ds != 'ALL') {
      //   var ds = `&datasetIds=${$scope.adv.ds}`;
      // }
      // Assemble URL
      // $scope.url = `${$scope.url}${start}${end}${alt}${ds}`;
      $scope.url = `${$scope.url}${start}${end}${alt}`;
      // that.searchText = '';
    }

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
      var variants = ['MT : 10 T > C', 'MT : 7600 G > A', 'MT : 195 TTACTAAAGT > MNP', 'MT : 14037 A > G',
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
