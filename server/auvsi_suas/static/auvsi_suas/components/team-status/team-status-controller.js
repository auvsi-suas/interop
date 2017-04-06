/**
 * @fileoverview Directive for team status view.
 */


/**
 * Directive for the team status view.
 * @final
 * @constructor
 * @struct
 * @ngInject
 */
TeamStatusCtrl = function() {
    /**
     * @export {?Object} The team object, injected by directive.
     */
    this.team;

    /**
     * @export {?boolean} Whether the team is active.
     */
    this.active;
};


/**
 * Gets the classes used to color a team's display on the dashboard.
 * @return {!string} The color classes.
 * @export
 */
TeamStatusCtrl.prototype.getTeamColorClasses = function() {
    classes = [];
    if (this.active) {
        classes.push('team-status-active');
    }
    if (this.team.in_air) {
        classes.push('team-status-in-air');
    }
    return classes.join(' ');
};


/**
 * @return {!boolean} Whether to show the team.
 * @export
 */
TeamStatusCtrl.prototype.shouldShow = function() {
    return this.active || this.team.in_air || this.team.on_clock ||
           this.team.on_timeout;
};


// Register the directive.
angular.module('auvsiSuasApp').directive('teamStatus', [
    function() {
        return {
            restrict: 'E',
            scope: {},
            bindToController: {
                team: '=',
                active: '='
            },
            controller: TeamStatusCtrl,
            controllerAs: 'teamStatusCtrl',
            templateUrl: ('/static/auvsi_suas/components/' +
                          'team-status/team-status.html'),
        };
    }
]);
