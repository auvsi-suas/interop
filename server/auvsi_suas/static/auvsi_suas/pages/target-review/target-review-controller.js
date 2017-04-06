/**
 * Controller for the Target Review page.
 */


/**
 * Controller for the Target Review page.
 * @param {!angular.Window} $window The window service.
 * @param {!Object} Backend The backend service.
 * @final
 * @constructor
 * @struct
 * @ngInject
 */
TargetReviewCtrl = function($window, Backend) {
    /**
     * @private @const {!angular.Window} The window service.
     */
    this.window_ = $window;

    /**
     * @private{?Array<Object>} The targets for review.
     */
    this.targets_ = null;

    /**
     * @private {?Object} The target under review.
     */
    this.target_ = null;

    /**
     * @private {?Array<Object>} The target review details.
     */
    this.targetDetails_ = null;

    // Query the backend for targets to review.
    Backend.targetReviewResource.query({}).$promise.then(
            angular.bind(this, this.setTargets_));
};


/**
 * Gets the targets for review.
 * @return {?Array<Object>} The targets.
 * @export
 */
TargetReviewCtrl.prototype.getReviewTargets = function() {
    return this.targets_;
};


/**
 * @return {?Object} The target under review.
 */
TargetReviewCtrl.prototype.getReviewTarget = function() {
    return this.target_;
};


/**
 * @return {?Object} The target details.
 */
TargetReviewCtrl.prototype.getReviewTargetDetails = function() {
    return this.targetDetails_;
};


/**
 * Gets the class for the target.
 * @param {!Object} target The target.
 * @return {string} The class.
 * @export
 */
TargetReviewCtrl.prototype.getTargetButtonClass = function(target) {
    var thumbnailClass;
    if (target.thumbnail_approved == null) {
        thumbnailClass = 'button';
    } else if (target.thumbnail_approved) {
        thumbnailClass = 'success button';
    } else {
        thumbnailClass = 'alert button';
    }

    if (this.target_ && target.id == this.target_.id) {
        return thumbnailClass + ' disabled';
    } else {
        return thumbnailClass;
    }
};


/**
 * Sets the target under review.
 * @param {!Object} target The target to review.
 * @export
 */
TargetReviewCtrl.prototype.setReviewTarget = function(target) {
    this.target_ = target;

    if (this.target_ == null) {
        return;
    }

    this.targetDetails_ = [
        {'key': 'ID',
         'value': this.target_.id},
        {'key': 'Type',
         'value': this.target_.type},
    ];
    if (this.target_.type == 'standard' || this.target_.type == 'off_axis') {
        this.targetDetails_ = this.targetDetails_.concat([
            {'key': 'Alpha Color',
             'value': this.target_.alphanumeric_color},
            {'key': 'Alpha',
             'value': this.target_.alphanumeric},
            {'key': 'Shape Color',
             'value': this.target_.background_color},
            {'key': 'Shape',
             'value': this.target_.shape}
        ]);
    } else {
        this.targetDetails_ = this.targetDetails_.concat([
            {'key': 'Desc',
             'value': this.target_.description}
        ]);
    }
};


/**
 * Saves the review status for the target under review. Advances to
 * the next target for review.
 */
TargetReviewCtrl.prototype.saveReview = function() {
    this.target_.$put().then(
            angular.bind(this, this.nextTarget_));
};


/**
 * @return {string} The class info for the target image review.
 */
TargetReviewCtrl.prototype.getTargetImgStyle = function() {
    if (!!this.target_) {
        return 'background-image: url(/api/targets/' + this.target_.id +
                '/image); height: ' + this.getTargetImgHeight() + 'px;';
    } else {
        return '';
    }
};


/**
 * @return {number} The height of the target image display.
 */
TargetReviewCtrl.prototype.getTargetImgHeight = function() {
    return this.window_.innerHeight - 95;
};


/**
 * @param {Array<Object>} targets The targets to review.
 */
TargetReviewCtrl.prototype.setTargets_ = function(targets) {
    this.targets_ = targets;
    if (this.targets_.length > 0) {
        this.setReviewTarget(this.targets_[0]);
    } else {
        this.setReviewTarget(null);
    }
};


/**
 * Advances to the next target.
 */
TargetReviewCtrl.prototype.nextTarget_ = function() {
    var targets = this.getReviewTargets();

    for (var i = 0; i < targets.length-1; i++) {
        if (targets[i].id == this.target_.id) {
            this.setReviewTarget(targets[i+1]);
            return;
        }
    }

    this.setReviewTarget(targets[targets.length-1]);
};


// Register controller with app.
angular.module('auvsiSuasApp').controller('TargetReviewCtrl', [
    '$window',
    'Backend',
    TargetReviewCtrl
]);
