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
     * @export {!Object} Map from user to telemetry data.
     */
    this.telemetry = {};

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
 * Gets a list of teams which should be displayed.
 * @return {!Array} A list of teams.
 * @export
 */
MissionDashboardCtrl.prototype.getTeamsToDisplay = function() {
    // Check that data has been loaded.
    if (!this.teams || this.teams.length == 0) {
        return [];
    }

    // Get all teams which are relevant.
    teams = [];
    for (var i = 0; i < this.teams.length; i++) {
        if (this.shouldDisplayTeam_(this.teams[i])) {
            teams.push(this.teams[i]);
        }
    }
    return teams;
};


/**
 * Gets the telemetry for a team.
 * @param{!Object} team The team for which to get telemetry.
 * @return {?Object} The telemetry for the team.
 * @export
 */
MissionDashboardCtrl.prototype.getTelemetry = function(team) {
    return this.telemetry[team.id];
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
        .then(angular.bind(this, this.setTeams_))
        .then(angular.bind(this, this.updateTelemetry_)));
    requests.push(this.backend_.obstaclesResource.get({}).$promise.then(
            angular.bind(this, this.setObstacles_)));

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
 * Updates the telemetry for active teams.
 * @return {!Object} Promise for updating telemetry requests.
 * @private
 */
MissionDashboardCtrl.prototype.updateTelemetry_ = function() {
    var requests = [];
    for (var i = 0; i < this.teams.length; i++) {
        if (this.teams[i].active) {
            var query = this.backend_.telemetryResource.query({
                limit: 1,
                user: this.teams[i].id
            });
            requests.push(query.$promise.then(angular.bind(this, this.setTelemetry_)));
        }
    }
    return this.q_.all(requests);
}


/**
 * Sets the telemetry.
 * @param {!Object} telemetry The telemetry to set.
 * @private
 */
MissionDashboardCtrl.prototype.setTelemetry_ = function(telemetry) {
    for (var i = 0; i < telemetry.length; i++) {
        this.telemetry[telemetry[i].user] = telemetry[i];
    }
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
            if (team.active && this.telemetry[team.id]) {
                telemetry.push(this.telemetry[team.id]);
            }
        }
    }

    if (!!this.missionScene) {
        // Rebuild scene with current mission.
        this.missionScene.rebuildScene(
                this.mission, this.obstacles, telemetry);
    }
};


/**
 * Determines whether a team should be displayed.
 * @param {!Object} team The team to evaluate.
 * @return {!boolean} Whether team should be displayed.
 * @private
 */
MissionDashboardCtrl.prototype.shouldDisplayTeam_ = function(team) {
    return team.on_clock || team.on_timeout || team.active || team.in_air;
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
