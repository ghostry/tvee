var FilterCtrl, app, controllers, services;

services = angular.module('services', ['ngResource']);

services.factory('Utils', [
  function() {
    var findObjectById;
    findObjectById = function(objects, target_id) {
      var index, object, _i, _len;
      for (index = _i = 0, _len = objects.length; _i < _len; index = ++_i) {
        object = objects[index];
        if ('' + target_id === '' + object.id) {
          return index;
        }
      }
      return -1;
    };
    return {
      getObjectById: function(objects, target_id) {
        var index;
        index = findObjectById(objects, target_id);
        if (index === -1) {
          return null;
        }
        return objects[index];
      },
      deleteObjectById: function(objects, target_id) {
        var index;
        index = findObjectById(objects, target_id);
        if (index === -1) {
          return false;
        }
        objects.splice(index, 1);
        return true;
      },
      updateObjectById: function(objects, target) {
        var index;
        index = findObjectById(objects, target.id);
        if (index === -1) {
          return false;
        }
        objects[index] = target;
        return true;
      },
      hasObjectById: function(objects, target_id) {
        var index;
        index = findObjectById(objects, target_id);
        return index !== -1;
      }
    };
  }
]);

services.factory('Setting', [
  '$resource', function($resource) {
    return $resource('/api/setting', {}, {
      get: {
        method: 'GET'
      },
      put: {
        method: 'PUT'
      }
    });
  }
]);

services.factory('TVShow', [
  '$resource', function($resource) {
    return $resource('/api/tvshows/:tvshow_id', {
      tvshow_id: '@id'
    }, {
      query: {
        method: 'GET',
        isArray: true
      },
      get: {
        method: 'GET'
      },
      post: {
        method: 'POST'
      },
      put: {
        method: 'PUT'
      },
      "delete": {
        method: 'DELETE'
      }
    });
  }
]);

services.factory('Episode', [
  '$resource', function($resource) {
    return $resource('/api/episodes/:episode_id/:action', {
      episode_id: '@id',
      action: '@action'
    }, {
      put: {
        method: 'PUT'
      }
    });
  }
]);

controllers = angular.module('controllers', ['ngClipboard', 'toaster', 'ui.bootstrap'], [
  '$compileProvider', function($compileProvider) {
    return $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|ed2k|magnet):/);
  }
]);

FilterCtrl = function($scope, $location, name, default_value) {
  var index, is_array, names, part, value, value_changed, _i, _len;
  is_array = angular.isArray(default_value);
  value = $location.search()[name];
  if (value != null) {
    if (is_array) {
      value = angular.fromJson(value);
    }
    $scope[name] = value;
  } else {
    $scope[name] = default_value;
  }
  value_changed = function() {
    var search, val;
    val = $scope[name];
    if (angular.isArray(val)) {
      val = angular.toJson(val);
    }
    if (val != null) {
      search = $location.search();
      search[name] = val;
      return $location.search(search);
    } else {
      return $location.search(name, null);
    }
  };
  if (is_array) {
    $scope.$watchCollection(name, value_changed);
  } else {
    $scope.$watch(name, value_changed);
  }
  names = name.split('_');
  for (index = _i = 0, _len = names.length; _i < _len; index = ++_i) {
    part = names[index];
    names[index] = part.charAt(0).toUpperCase() + part.slice(1);
  }
  return $scope['set' + names.join('')] = function(value) {
    if ($scope[name] === value) {
      return;
    }
    $scope[name] = value;
    return $scope.reload();
  };
};

FilterCtrl['$inject'] = ['$scope', '$location', 'name', 'default_value'];

controllers.controller('TVShowListCtrl', [
  '$scope', '$injector', '$modal', 'Utils', 'TVShow', 'Episode', function($scope, $injector, $modal, Utils, TVShow, Episode) {
    $injector.invoke(FilterCtrl, this, {
      '$scope': $scope,
      'name': 'tvshow_id',
      'default_value': null
    });
    $scope.setTvshowId = function(tvshow_id) {
      $scope.tvshow_id = tvshow_id;
      $scope.current_tvshow = null;
      if (tvshow_id) {
        return TVShow.get({
          tvshow_id: $scope.tvshow_id
        }, function(tvshow) {
          return $scope.current_tvshow = tvshow;
        });
      }
    };
    $scope.loadTVShows = function() {
      return TVShow.query(function(tvshows) {
        $scope.tvshows = tvshows;
        if ($scope.tvshow_id) {
          return $scope.setTvshowId($scope.tvshow_id);
        } else if (tvshows.length > 0) {
          return $scope.setTvshowId(tvshows[0].id);
        }
      });
    };
    $scope.loadTVShows();
    $scope.refreshTVShows = function() {
      var modalInstance;
      modalInstance = $modal.open({
        templateUrl: 'static/template/confirm.html',
        controller: [
          '$scope', '$modalInstance', function($scope, $modalInstance) {
            $scope.action = '刷新剧集';
            $scope.action_class = 'btn-warning';
            $scope.tip = '确实要刷新所有剧集吗?';
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close();
            };
          }
        ]
      });
      return modalInstance.result.then(function() {
        return TVShow.put({
          id: 'refresh'
        });
      });
    };
    $scope.editSetting = function() {
      var modalInstance;
      modalInstance = $modal.open({
        templateUrl: 'static/template/setting_form.html',
        controller: [
          '$scope', '$modalInstance', 'Setting', function($scope, $modalInstance, Setting) {
            $scope.setting = Setting.get();
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close($scope.setting);
            };
          }
        ],
        size: 'lg'
      });
      return modalInstance.result.then(function(setting) {
        return setting.$put();
      });
    };
    $scope.newTVShow = function() {
      var modalInstance;
      modalInstance = $modal.open({
        templateUrl: 'static/template/tvshow_form.html',
        controller: [
          '$scope', '$modalInstance', function($scope, $modalInstance) {
            $scope.title = '增加剧集';
            $scope.tvshow = {
              chinese_only: true,
              allow_repeat: false,
              refresh_interval: 8,
              blob: 'HR-HDTV'
            };
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close($scope.tvshow);
            };
          }
        ],
        size: 'lg'
      });
      return modalInstance.result.then(function(tvshow) {
        return TVShow.post(tvshow, function(new_tvshow) {
          $scope.tvshows.push(new_tvshow);
          $scope.tvshow_id = new_tvshow.id;
          return $scope.current_tvshow = new_tvshow;
        });
      });
    };
    $scope.editTVShow = function(tvshow) {
      var modalInstance;
      modalInstance = $modal.open({
        templateUrl: 'static/template/tvshow_form.html',
        controller: [
          '$scope', '$modalInstance', function($scope, $modalInstance) {
            $scope.title = '设定剧集';
            $scope.tvshow = angular.copy(tvshow);
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close($scope.tvshow);
            };
          }
        ],
        size: 'lg'
      });
      return modalInstance.result.then(function(tvshow) {
        return tvshow.$put(function(updated_tvshow) {
          Utils.updateObjectById($scope.tvshows, updated_tvshow);
          return $scope.current_tvshow = updated_tvshow;
        });
      });
    };
    $scope.refreshTVShow = function(tvshow) {
      var modalInstance;
      if (tvshow == null) {
        tvshow = $scope.current_tvshow;
      }
      modalInstance = $modal.open({
        templateUrl: 'static/template/confirm.html',
        controller: [
          '$scope', '$modalInstance', function($scope, $modalInstance) {
            $scope.action = '刷新剧集';
            $scope.action_class = 'btn-warning';
            $scope.tip = '确实要刷新剧集 ' + tvshow.title + ' 吗?';
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close();
            };
          }
        ]
      });
      return modalInstance.result.then(function() {
        return TVShow.get({
          tvshow_id: $scope.tvshow_id
        }, function(tvshow) {
          if (tvshow.id === $scope.current_tvshow) {
            return $scope.current_tvshow = tvshow;
          }
        });
      });
    };
    $scope.controlingEpisode = function(episode, title, action_class, action) {
      var modalInstance;
      modalInstance = $modal.open({
        templateUrl: 'static/template/confirm.html',
        controller: [
          '$scope', '$modalInstance', function($scope, $modalInstance) {
            $scope.action = title + '剧集';
            $scope.action_class = action_class;
            $scope.tip = '确实要' + title + '剧集 ' + episode.title + ' 吗?';
            $scope.episode = episode;
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close($scope.episode);
            };
          }
        ]
      });
      return modalInstance.result.then(function(episode) {
        return Episode.put({
          id: episode.id,
          action: action
        }, function(updated_episode) {
          var index, _i, _len, _ref, _results;
          _ref = $scope.current_tvshow.episodes;
          _results = [];
          for (index = _i = 0, _len = _ref.length; _i < _len; index = ++_i) {
            episode = _ref[index];
            if (episode.id === updated_episode.id) {
              $scope.current_tvshow.episodes[index] = updated_episode;
              break;
            } else {
              _results.push(void 0);
            }
          }
          return _results;
        });
      });
    };
    $scope.downloadEpisode = function(episode) {
      return $scope.controlingEpisode(episode, (episode.is_downloaded ? '重新下载' : '远程下载'), (episode.is_downloaded ? 'btn-warning' : 'btn-success'), 'downloading');
    };
    $scope.pauseDownloadEpisode = function(episode) {
      return $scope.controlingEpisode(episode, '暂停远程下载', 'btn-danger', 'pause_downloading');
    };
    $scope.deleteCurrentTVShow = function(tvshow) {
      var modalInstance;
      modalInstance = $modal.open({
        templateUrl: 'static/template/confirm.html',
        controller: [
          '$scope', '$modalInstance', function($scope, $modalInstance) {
            $scope.action = '删除剧集';
            $scope.action_class = 'btn-danger';
            $scope.tip = '确实要删除剧集 ' + tvshow.title + ' 吗?';
            $scope.tvshow = tvshow;
            $scope.cancel = function() {
              return $modalInstance.dismiss('cancel');
            };
            return $scope.ok = function() {
              return $modalInstance.close($scope.tvshow);
            };
          }
        ]
      });
      return modalInstance.result.then(function(tvshow) {
        var tvshow_id;
        tvshow_id = tvshow.id;
        return tvshow.$delete(function() {
          Utils.deleteObjectById($scope.tvshows, tvshow_id);
          if ($scope.tvshows.length > 0) {
            return $scope.setTvshowId($scope.tvshows[0].id);
          } else {
            return $scope.setTvshowId(null);
          }
        });
      });
    };
    $scope.toggleEpisodeSelections = function($event) {
      var episode, _i, _len, _ref, _results;
      _ref = $scope.current_tvshow.episodes;
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        episode = _ref[_i];
        _results.push(episode.checked = $event.target.checked);
      }
      return _results;
    };
    $scope.copyEd2ks = function() {
      var episode, text, _i, _len, _ref;
      text = '';
      _ref = $scope.current_tvshow.episodes;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        episode = _ref[_i];
        if (episode.checked) {
          text += episode.ed2k + '\n';
        }
      }
      return text;
    };
    return $scope.copyMagnets = function() {
      var episode, text, _i, _len, _ref;
      text = '';
      _ref = $scope.current_tvshow.episodes;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        episode = _ref[_i];
        if (episode.checked) {
          text += episode.magnet + '\n';
        }
      }
      return text;
    };
  }
]);

app = angular.module('app', ['services', 'controllers']);
