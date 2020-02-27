"""
Django settings for the interop server.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'anp#d4lgo3u6j&6dc3+8sn!t+l(6hcuspm^&3(yq10evfwbh+1'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Public IP addresses given access to Django Debug Toolbar
# Add your IP here, if not localhost.
INTERNAL_IPS = ['127.0.0.1']

# Application definition
INSTALLED_APPS = (
    'auvsi_suas',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'pipeline',
)  # yapf: disable

MIDDLEWARE_CLASSES = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'pipeline.middleware.MinifyHTMLMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'auvsi_suas.views.middleware.LoggingMiddleware',
)  # yapf: disable

ROOT_URLCONF = 'server.urls'
WSGI_APPLICATION = 'server.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases
# SECURITY WARNING: change the database superuser password!
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'auvsi_suas_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'CONN_MAX_AGE': None,
        'HOST': 'interop-db',
        'PORT': '5432',
        'TEST': {
            'NAME': 'test_auvsi_suas_db',
        },
    }
}

# Caches
# https://docs.djangoproject.com/en/1.11/topics/cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 10,
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
# https://docs.djangoproject.com/en/1.11/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'auvsi_suas/frontend'),
]

STATICFILES_STORAGE = 'pipeline.storage.PipelineStorage'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder', )

PIPELINE = {
    'STYLESHEETS': {
        'styles': {
            'source_filenames': (
                'third_party/bootstrap/bootstrap.min.css',
                'app.css',
                'components/team-status.css',
                'pages/mission-dashboard.css',
                'pages/mission-list.css',
                'pages/odlc-review.css',
                'pages/evaluate-teams.css',
            ),
            'output_filename': 'styles.css',
        },
    },
    'JAVASCRIPT': {
        'scripts': {
            'source_filenames': (
                'third_party/jquery/jquery.min.js',
                'third_party/bootstrap/bootstrap.min.js',
                'third_party/angularjs/angular.min.js',
                'third_party/angularjs/angular-resource.min.js',
                'third_party/angularjs/angular-route.min.js',
                'app.js',
                'components/navigation.js',
                'components/backend-service.js',
                'components/team-status-controller.js',
                'pages/gps-conversion-controller.js',
                'pages/mission-dashboard-controller.js',
                'pages/mission-list-controller.js',
                'pages/odlc-review-controller.js',
                'pages/evaluate-teams-controller.js',
            ),
            'output_filename': 'scripts.js',
        },
    },
} # yapf: disable

# User uploaded files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/media'

# Send images with sendfile.
SENDFILE_BACKEND = 'sendfile.backends.nginx'
SENDFILE_ROOT = MEDIA_ROOT
SENDFILE_URL = MEDIA_URL

# Login URL
LOGIN_URL = '/admin/login/?next=/'

# Migrations
MIGRATION_MODULES = {
    'auvsi_suas.models': 'auvsi_suas.models.migrations',
}  # yapf: disable

# Custom test runner.
TEST_RUNNER = 'auvsi_suas.test_runner.AuvsiSuasTestRunner'
