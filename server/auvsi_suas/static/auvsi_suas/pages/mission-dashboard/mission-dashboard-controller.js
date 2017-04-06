/**
 * Controller for the Mission Dashboard page.
 */


/**
 * Controller for the Mission Dashboard page.
 * @param {!angular.$q} $q The promise service.
 * @param {!angular.Scope} $rootScope The root scope to listen for events.
 * @param {!angular.$routeParams} $routeParams The route parameter service.
 * @param {!angular.$interval} $interval The interval service.
 * @param {!Object} Backend The backend service.
 * @final
 * @constructor
 * @struct
 * @ngInject
 */
MissionDashboardCtrl = function($q, $rootScope, $routeParams, $interval,
                                Backend) {
    /**
     * @export {?Object} The mission data.
     */
    this.mission = null;

    /**
     * @export {?Object} The teams data.
     */
    this.teams = null;

    /**
     * @export {?Object} The obstacles data.
     */
    this.obstacles = null;

    /**
     * @private @const {?Object} The scene built by the map view, via template.
     */
    this.missionScene = null;

    /**
     * @private @const {!angular.$q} The promise service.
     */
    this.q_ = $q;

    /**
     * @private @const {!angular.$routeParams} The route params service.
     */
    this.routeParams_ = $routeParams;

    /**
     * @private @const {!Object} The backend service.
     */
    this.backend_ = Backend;

    /**
     * @private @const {!Object} Data sync every 1s.
     */
    this.updateInterval_ = $interval(
            angular.bind(this, this.update_), 1000);

    // Get the mission data.
    this.backend_.missionResource.get({id: this.routeParams_['missionId']})
        .$promise.then(angular.bind(this, this.setMission_));
};


/**
 * @return {?Object} The mission.
 * @export
 */
MissionDashboardCtrl.prototype.getMission = function() {
    return this.mission;
};


/**
 * @param {!Object} The team.
 * @return {!boolean} Whether the team is active.
 * @export
 */
MissionDashboardCtrl.prototype.isActive = function(team) {
    return !!team.telemetry &&
        new Date() - new Date(team.telemetry.timestamp) < 3000;
};


/**
 * @param {!Object} mission The mission data.
 */
MissionDashboardCtrl.prototype.setMission_ = function(mission) {
    this.mission = mission;
};


/**
 * Executes asynchronous updates for data.
 * @private
 */
MissionDashboardCtrl.prototype.update_ = function() {
    // Execute backend requests.
    var requests = [];
    requests.push(this.backend_.teamsResource.query({}).$promise
        .then(angular.bind(this, this.setTeams_)));
    requests.push(this.backend_.obstaclesResource.get({}).$promise
        .then(angular.bind(this, this.setObstacles_)));

    // Update display when requests finished.
    this.q_.all(requests).then(angular.bind(this, this.rebuildMissionScene_));
};


/**
 * Sets the teams.
 * @param {Array<Object>} teams The teams to set.
 * @private
 */
MissionDashboardCtrl.prototype.setTeams_ = function(teams) {
    this.teams = teams;
};


/**
 * Sets the obstacles.
 * @param {!Object} obstacles The obstacles to set.
 * @private
 */
MissionDashboardCtrl.prototype.setObstacles_ = function(obstacles) {
    this.obstacles = obstacles;
};


/**
 * Rebuild the mission scene using the backend data.
 * @private
 */
MissionDashboardCtrl.prototype.rebuildMissionScene_ = function() {
    if (!this.mission) {
        return;
    }

    var telemetry = [];
    if (this.teams) {
        for (var i = 0; i < this.teams.length; i++) {
            var team = this.teams[i];
            if (team.telemetry && this.isActive(team)) {
                telemetry.push(team.telemetry);
            }
        }
    }

    if (!!this.missionScene) {
        // Rebuild scene with current mission.
        this.missionScene.rebuildScene(
                this.mission, this.obstacles, telemetry);
    }
};


// Register controller with app.
angular.module('auvsiSuasApp').controller('MissionDashboardCtrl', [
    '$q',
    '$rootScope',
    '$routeParams',
    '$interval',
    'Backend',
    MissionDashboardCtrl
]);
