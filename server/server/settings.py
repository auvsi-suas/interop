"""
Django settings for the interop server.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'anp#d4lgo3u6j&6dc3+8sn!t+l(6hcuspm^&3(yq10evfwbh+1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = DEBUG

TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]

ALLOWED_HOSTS = ['*']

# Public IP addresses given access to Django Debug Toolbar
# Add your IP here, if not localhost.
INTERNAL_IPS = ['127.0.0.1']

# Path to jQuery for the Django Debug Toolbar to use.
JQUERY_URL = '/static/admin/js/jquery.js'

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'auvsi_suas',
    'auvsi_suas.views.auvsi_admin',
)  # yapf: disable

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auvsi_suas.views.middleware.LoggingMiddleware',
)  # yapf: disable

# Add a '?debug' parameter to API endpoints, which wraps them in an HTML
# response, allowing the use of Django Debug Toolbar with the endpoints.
if DEBUG:
    import debug
    INSTALLED_APPS += 'debug_toolbar',
    MIDDLEWARE_CLASSES += debug.middleware

# All of the default panels, plus the profiling panel.
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

DEBUG_TOOLBAR_CONFIG = {'PROFILER_MAX_DEPTH': 50}

ROOT_URLCONF = 'server.urls'
WSGI_APPLICATION = 'server.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'auvsi_suas_db',
        'USER': 'postgresql_user',
        'PASSWORD': 'postgresql_pass',
        'CONN_MAX_AGE': None,
        'HOST': 'localhost',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_auvsi_suas_db',
        },
    }
}

# Caches
# https://docs.djangoproject.com/en/1.6/topics/cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 30,
        'KEY_PREFIX': 'suas',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
            '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(module)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'py.warnings': {
            'handlers': ['file'],
        },
        'django': {
            'handlers': ['file'],
        },
        'django.request': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'auvsi_suas.views': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'auvsi_suas/static')

# User uploaded files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/media'

# Send with X-SENDFILE in apache
SENDFILE_BACKEND = 'sendfile.backends.xsendfile'

# Login URL
LOGIN_URL = '/admin/login/?next=/'

# Migrations
MIGRATION_MODULES = {
    'auvsi_suas.models': 'auvsi_suas.models.migrations',
}  # yapf: disable

# Custom test runner.
TEST_RUNNER = 'auvsi_suas.test_runner.AuvsiSuasTestRunner'

# Whether tests can/should generate plots (requires window access)
TEST_ENABLE_PLOTTING = False
# Whether to perform load tests (slower)
TEST_ENABLE_LOADTEST = True
# The time to execute each loadtest for
TEST_LOADTEST_TIME = 2.0
# The minimum rate of an individual interop interface
# (1.5x safety factor, 10Hz, 4 interfaces)
TEST_LOADTEST_INTEROP_MIN_RATE = 1.5 * 10.0 * 4

# The time window (in seconds) in which a plane cannot be counted as going out
# of bounds multiple times. This prevents noisy input data from recording
# significant more violations than a human observer.
OUT_OF_BOUNDS_DEBOUNCE_SEC = 10.0
# The max distance for a waypoint to be considered satisfied.
SATISFIED_WAYPOINT_DIST_MAX_FT = 100

# Ratio of object points to lose for every extra unmatched object submitted.
EXTRA_OBJECT_PENALTY_RATIO = 0.05
# The weight of classification accuracy when calculating a target match score.
CHARACTERISTICS_WEIGHT = 0.2
# The lowest allowed location accuracy (in feet)
TARGET_LOCATION_THRESHOLD = 150
# The weight of geolocation accuracy when calculating a target match score.
GEOLOCATION_WEIGHT = 0.2
# The weight of actionable intelligence when calculating a target match score.
ACTIONABLE_WEIGHT = 0.1
# The weight of autonomy when calculating a target match score.
AUTONOMY_WEIGHT = 0.2
# The weight of submission over interop when calculating a target match score.
INTEROPERABILITY_WEIGHT = 0.3

# Weight of timeline points for mission time.
MISSION_TIME_WEIGHT = 0.8
# Weight of timeline points for not taking a timeout.
TIMEOUT_WEIGHT = 0.2
# Max mission time.
MISSION_MAX_TIME_SEC = 45.0 * 60.0
# Points for flight time in mission time score.
FLIGHT_TIME_SEC_TO_POINTS = 5.0 / 60.0
# Points for post-processing time in mission time score.
PROCESS_TIME_SEC_TO_POINTS = 1.0 / 60.0
# Total points possible for mission time.
MISSION_TIME_TOTAL_POINTS = MISSION_MAX_TIME_SEC * max(
    FLIGHT_TIME_SEC_TO_POINTS, PROCESS_TIME_SEC_TO_POINTS)
# Mission time points lost due for every second over time.
MISSION_TIME_PENALTY_FROM_SEC = MISSION_TIME_WEIGHT * 0.01

# Total mission time 
# Weight for 
# Max weighted time.
