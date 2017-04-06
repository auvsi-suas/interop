/**
 * Tests for the TeamStatusView controller.
 */

describe("TeamStatusCtrl controller", function() {
    var teamStatusCtrl, team;

    beforeEach(module('auvsiSuasApp'));

    beforeEach(inject(function($controller) {
        team = {
            id: 4,
            on_clock: false,
            on_timeout: false,
            telemetry: {
                id: 10,
                user: 4,
                timestamp: '1990-10-01T00:00:00+00:00',
                latitude: 38,
                longitude: -76,
                altitude_msl: 0,
                heading: 90
            },
            in_air: false
        };
        teamStatusCtrl = new TeamStatusCtrl();
        teamStatusCtrl.team = team;
        teamStatusCtrl.active = false;
    }));

    it("Should get the team color class", function() {
        team.in_air = false;
        expect(teamStatusCtrl.getTeamColorClasses())
            .toEqual('');

        team.in_air = true;
        expect(teamStatusCtrl.getTeamColorClasses())
            .toEqual('team-status-in-air');

        team.in_air = false;
        teamStatusCtrl.active = true;
        expect(teamStatusCtrl.getTeamColorClasses())
            .toEqual('team-status-active');

        team.in_air = true;
        expect(teamStatusCtrl.getTeamColorClasses())
            .toEqual('team-status-active team-status-in-air');
    });
});
