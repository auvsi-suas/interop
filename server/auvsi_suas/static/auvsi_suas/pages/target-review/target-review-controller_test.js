/**
 * Tests for the TargetReviewCtrl controller.
 */


describe("TargetReviewCtrl controller", function() {
    var httpBackend, targets, targetReviewCtrl;

    beforeEach(module('auvsiSuasApp'));

    beforeEach(inject(function($window, $controller, $httpBackend, Backend) {
        httpBackend = $httpBackend;
        targets = [
             {id: 1, thumbnail_approved: null},
             {id: 2, thumbnail_approved: true},
             {id: 3, thumbnail_approved: false}
        ];
        httpBackend.whenGET('/api/targets/review').respond(targets);

        targetReviewCtrl = $controller('TargetReviewCtrl', {
            '$window': $window,
            'Backend': Backend,
        });
    }));

    it("Should get review targets", function() {
        httpBackend.flush();
        var recv_targets = targetReviewCtrl.getReviewTargets();
        expect(recv_targets.length).toEqual(targets.length);
        for (var i = 0; i < targets.length; i++) {
            expect(recv_targets[i].toJSON()).toEqual(targets[i]);
        }
    });

    it("Should get target button class", function() {
        targetReviewCtrl.setReviewTarget(targets[0]);
        expect(targetReviewCtrl.getTargetButtonClass(targets[0]))
                .toEqual('button disabled');
        expect(targetReviewCtrl.getTargetButtonClass(targets[1]))
                .toEqual('success button');
        expect(targetReviewCtrl.getTargetButtonClass(targets[2]))
                .toEqual('alert button');
    });

    it("Should get review target", function() {
        httpBackend.flush();
        var target = targetReviewCtrl.getReviewTargets()[0];
        targetReviewCtrl.setReviewTarget(target);
        expect(targetReviewCtrl.getReviewTarget().toJSON()).toEqual(targets[0]);
    });

    it("Should update the review", function() {
        httpBackend.flush();

        targets[0].thumbnail_approved = true;
        httpBackend.expectPUT('/api/targets/review/1', targets[0]).respond(200, targets[0]);

        var target = targetReviewCtrl.getReviewTargets()[0];
        targetReviewCtrl.setReviewTarget(target);
        target.thumbnail_approved = true;
        targetReviewCtrl.saveReview();
        httpBackend.flush();
        expect(target.thumbnail_approved).toBe(true);
    });
});
