services = angular.module 'services', ['ngResource']


services.factory 'Utils', [->
    findObjectById = (objects, target_id)->
        for object, index in objects
            if '' + target_id == '' + object.id
                return index
        return -1
    getObjectById: (objects, target_id)->
        index = findObjectById(objects, target_id)
        if index == -1
            return null
        return objects[index]
    deleteObjectById: (objects, target_id)->
        index = findObjectById(objects, target_id)
        if index == -1
            return false
        objects.splice index, 1
        return true
    updateObjectById: (objects, target)->
        index = findObjectById(objects, target.id)
        if index == -1
            return false
        objects[index] = target
        return true
    hasObjectById: (objects, target_id)->
        index = findObjectById(objects, target_id)
        return index != -1
]

services.factory 'Setting', ['$resource', ($resource)->
    return $resource '/api/setting', {}, {
        get: {method:'GET'},
        put: {method: 'PUT'}
    }
]


services.factory 'TVShow', ['$resource', ($resource)->
    return $resource '/api/tvshows/:tvshow_id', {tvshow_id: '@id'}, {
        query: {method:'GET', isArray:true},
        get: {method:'GET'},
        post: {method:'POST'},
        put: {method: 'PUT'},
        delete: {method: 'DELETE'}
    }
]


services.factory 'Episode', ['$resource', ($resource)->
    return $resource '/api/episodes/:episode_id/:action', {episode_id: '@id', action: '@action'}, {
        put: {method: 'PUT'}
    }
]


controllers = angular.module 'controllers', ['ngClipboard', 'toaster', 'ui.bootstrap'], ['$compileProvider', ($compileProvider)->
    $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|ed2k|magnet):/)
]


FilterCtrl = ($scope, $location, name, default_value)->
    is_array = angular.isArray default_value
    value = $location.search()[name]
    if value?
        if is_array
            value = angular.fromJson value
        $scope[name] = value
    else
        $scope[name] = default_value
    value_changed = ->
        val = $scope[name]
        if angular.isArray(val)
            val = angular.toJson val
        if val?
            search = $location.search()
            search[name] = val
            $location.search search
        else
            $location.search(name, null)
    if is_array
        $scope.$watchCollection name, value_changed
    else
        $scope.$watch name, value_changed

    names = name.split('_')
    for part, index in names
        names[index] = part.charAt(0).toUpperCase() + part.slice(1)
    $scope['set' + names.join('')] = (value)->
        if $scope[name] == value
            return
        $scope[name] = value
        $scope.reload()
FilterCtrl['$inject'] = ['$scope', '$location', 'name', 'default_value']


controllers.controller('TVShowListCtrl', ['$scope', '$injector', '$modal', 'Utils', 'TVShow', 'Episode', ($scope, $injector, $modal, Utils, TVShow, Episode)->
    $injector.invoke FilterCtrl, this, 
        '$scope': $scope
        'name': 'tvshow_id'
        'default_value': null

    $scope.setTvshowId = (tvshow_id)->
        $scope.tvshow_id = tvshow_id
        $scope.current_tvshow = null
        if tvshow_id
            TVShow.get tvshow_id:$scope.tvshow_id, (tvshow)->
                $scope.current_tvshow = tvshow

    $scope.loadTVShows = ->
        TVShow.query (tvshows)->
            $scope.tvshows = tvshows
            if $scope.tvshow_id
                $scope.setTvshowId($scope.tvshow_id)
            else if tvshows.length > 0
                $scope.setTvshowId(tvshows[0].id)
    $scope.loadTVShows()

    $scope.refreshTVShows = ->
        modalInstance = $modal.open
            templateUrl: 'static/template/confirm.html'
            controller: ['$scope', '$modalInstance', ($scope, $modalInstance)->
                $scope.action = '刷新剧集'
                $scope.action_class = 'btn-warning'
                $scope.tip = '确实要刷新所有剧集吗?'
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close()
            ]
        modalInstance.result.then ()->
            TVShow.put
                id: 'refresh'


    $scope.editSetting = ()->
        modalInstance = $modal.open
            templateUrl: 'static/template/setting_form.html'
            controller: ['$scope', '$modalInstance', 'Setting', ($scope, $modalInstance, Setting)->
                $scope.setting = Setting.get()
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close $scope.setting
            ]
            size: 'lg'
        modalInstance.result.then (setting)->
            setting.$put()


    $scope.newTVShow = ()->
        modalInstance = $modal.open
            templateUrl: 'static/template/tvshow_form.html'
            controller: ['$scope', '$modalInstance', ($scope, $modalInstance)->
                $scope.title = '增加剧集'
                $scope.tvshow =
                    chinese_only: true
                    allow_repeat: false
                    refresh_interval: 8
                    blob: 'HR-HDTV'
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close $scope.tvshow
            ]
            size: 'lg'
        modalInstance.result.then (tvshow)->
            TVShow.post tvshow, (new_tvshow)->
                $scope.tvshows.push new_tvshow
                $scope.tvshow_id = new_tvshow.id
                $scope.current_tvshow = new_tvshow

    $scope.editTVShow = (tvshow)->
        modalInstance = $modal.open
            templateUrl: 'static/template/tvshow_form.html'
            controller: ['$scope', '$modalInstance', ($scope, $modalInstance)->
                $scope.title = '设定剧集'
                $scope.tvshow = angular.copy(tvshow)
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close $scope.tvshow
            ]
            size: 'lg'
        modalInstance.result.then (tvshow)->
            tvshow.$put (updated_tvshow)->
                Utils.updateObjectById $scope.tvshows, updated_tvshow
                $scope.current_tvshow = updated_tvshow

    $scope.refreshTVShow = (tvshow = $scope.current_tvshow)->
        modalInstance = $modal.open
            templateUrl: 'static/template/confirm.html'
            controller: ['$scope', '$modalInstance', ($scope, $modalInstance)->
                $scope.action = '刷新剧集'
                $scope.action_class = 'btn-warning'
                $scope.tip = '确实要刷新剧集 ' + tvshow.title + ' 吗?'
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close()
            ]
        modalInstance.result.then ()->
            TVShow.get tvshow_id:$scope.tvshow_id, (tvshow)->
                    if tvshow.id == $scope.current_tvshow
                        $scope.current_tvshow = tvshow


    $scope.controlingEpisode = (episode, title, action_class, action)->
        modalInstance = $modal.open
            templateUrl: 'static/template/confirm.html'
            controller: ['$scope', '$modalInstance', ($scope, $modalInstance)->
                $scope.action = title + '剧集'
                $scope.action_class = action_class
                $scope.tip = '确实要' + title + '剧集 ' + episode.title + ' 吗?'
                $scope.episode = episode
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close $scope.episode
            ]
        modalInstance.result.then (episode)->
            Episode.put
                id: episode.id
                action: action, (updated_episode)->
                    for episode, index in $scope.current_tvshow.episodes
                        if episode.id == updated_episode.id
                            $scope.current_tvshow.episodes[index] = updated_episode
                            break

    $scope.downloadEpisode = (episode)->
        $scope.controlingEpisode(episode, (if episode.is_downloaded then '重新下载' else '远程下载'), (if episode.is_downloaded then 'btn-warning' else 'btn-success'), 'downloading')

    $scope.pauseDownloadEpisode = (episode)->
        $scope.controlingEpisode(episode, '暂停远程下载', 'btn-danger', 'pause_downloading')

    $scope.deleteCurrentTVShow = (tvshow)->
        modalInstance = $modal.open
            templateUrl: 'static/template/confirm.html'
            controller: ['$scope', '$modalInstance', ($scope, $modalInstance)->
                $scope.action = '删除剧集'
                $scope.action_class = 'btn-danger'
                $scope.tip = '确实要删除剧集 ' + tvshow.title + ' 吗?'
                $scope.tvshow = tvshow
                $scope.cancel = ->
                    $modalInstance.dismiss 'cancel'
                $scope.ok = ->
                    $modalInstance.close $scope.tvshow
            ]
        modalInstance.result.then (tvshow)->
            tvshow_id = tvshow.id
            tvshow.$delete ->
                Utils.deleteObjectById $scope.tvshows, tvshow_id
                if $scope.tvshows.length > 0
                    $scope.setTvshowId($scope.tvshows[0].id)
                else
                    $scope.setTvshowId(null)

    $scope.toggleEpisodeSelections = ($event)->
        for episode in $scope.current_tvshow.episodes
            episode.checked = $event.target.checked

    $scope.copyEd2ks = ()->
        text = ''
        for episode in $scope.current_tvshow.episodes
            if episode.checked
                text += episode.ed2k + '\n'
        return text
    $scope.copyMagnets = ()->
        text = ''
        for episode in $scope.current_tvshow.episodes
            if episode.checked
                text += episode.magnet + '\n'
        return text
    ])


app = angular.module 'app', ['services', 'controllers']
