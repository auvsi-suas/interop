// Karma configuration
// Generated on Wed Jul 29 2015 07:57:21 GMT-0400 (EDT)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine'],


    // list of files / patterns to load in the browser
    files: [
      // Base files.
      '../angularjs/angular.js',
      '../angularjs/angular-mocks.js',
      '../angularjs/angular-animate.js',
      '../angularjs/angular-cookies.js',
      '../angularjs/angular-resource.js',
      '../angularjs/angular-route.js',
      '../angularjs/angular-sanitize.js',
      '../angularjs/angular-touch.js',
      // Source files.
      'app.js',
      'components/settings/settings-service.js',
      'components/navigation/navigation.js',
      'components/backend/backend-service.js',
      'components/units/units-service.js',
      'components/distance/distance-service.js',
      'components/mission-scene/mission-scene.js',
      'components/mission-map/mission-map-controller.js',
      'components/team-status/team-status-controller.js',
      'pages/mission-dashboard/mission-dashboard-controller.js',
      'pages/mission-list/mission-list-controller.js',
      'pages/target-review/target-review-controller.js',
      'pages/evaluate-teams/evaluate-teams-controller.js',
      // Test files.
      'components/settings/settings-service_test.js',
      'components/navigation/navigation_test.js',
      'components/units/units-service_test.js',
      'components/distance/distance-service_test.js',
      'components/team-status/team-status-controller_test.js',
      'pages/mission-dashboard/mission-dashboard-controller_test.js',
      'pages/mission-list/mission-list-controller_test.js',
      'pages/target-review/target-review-controller_test.js',
      'pages/evaluate-teams/evaluate-teams-controller_test.js',
    ],


    // list of files to exclude
    exclude: [
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Chrome', 'PhantomJS'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false
  })
}
