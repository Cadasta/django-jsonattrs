def pytest_configure():
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': 'jsonattrs_test',
                'USER': 'jsonattrs',
                'PASSWORD': 'jsonattrs',
                'HOST': 'localhost',
            }
        },
        # JSONATTRS_SCHEMA_SELECTORS=(
        #     'project.organization.name', 'project.name'
        # ),
        JSONATTRS_SCHEMA_SELECTORS={
            'tests.organization': (),
            'tests.project': ('organization.pk',),
            'tests.party': ('project.organization.pk', 'project.pk'),
            'tests.parcel': ('project.organization.pk', 'project.pk', 'type'),
            'tests.labelled': ('label',)
        },
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        TEMPLATE_LOADERS=(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ),
        MIDDLEWARE_CLASSES=(
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.messages',
            'django.contrib.staticfiles',

            'jsonattrs',
            'tests',
        ),
        CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'default'
            },
            'jsonattrs:schema': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'jsonattrs:schema'
            }
        },
        # LOGGING={
        #     'version': 1,
        #     'disable_existing_loggers': False,
        #     'handlers': {
        #         'console': {
        #             'class': 'logging.StreamHandler'
        #         },
        #     },
        #     'loggers': {
        #         'django.db.backends': {
        #             'handlers': ['console'],
        #             'level': 'DEBUG'
        #         }
        #     }
        # }
    )

    try:
        import django
        django.setup()
    except AttributeError:
        pass
