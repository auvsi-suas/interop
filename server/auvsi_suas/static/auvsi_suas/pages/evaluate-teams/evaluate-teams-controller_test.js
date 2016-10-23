/**
 * Tests for the EvaluateTeamsCtrl controller.
 */


describe("EvaluateTeamsCtrl controller", function() {
    var httpBackend, window, evaluateTeamsCtrl;

    beforeEach(module('auvsiSuasApp'));

    beforeEach(inject(function($httpBackend, $controller, Backend) {
        httpBackend = $httpBackend;
        window = {
            expectUrl: null,
            open: function(url, target) {
                expect(url).toEqual(this.expectUrl);
            }
        };

        var teams = [
            {
                id: 1,
                on_clock: false,
                on_timeout: false,
                active: false,
                in_air: false
            }
        ];
        httpBackend.whenGET('/api/teams').respond(teams);

        evaluateTeamsCtrl = $controller('EvaluateTeamsCtrl', {
            $window: window,
            Backend: Backend
        });
    }));

    it("Should get evaluate teams", function() {
        httpBackend.flush();
        evaluateTeamsCtrl.selectedTeamId = '1';
        evaluateTeamsCtrl.selectedExtension = 'Csv';
        window.expectUrl = '/auvsi_admin/evaluate_teams.csv?team=1';
        evaluateTeamsCtrl.evaluate();
    });
});
