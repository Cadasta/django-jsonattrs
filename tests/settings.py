DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'jsonattrs_test',
        'USER': 'jsonattrs',
        'PASSWORD': 'jsonattrs',
        'HOST': 'localhost',
    }
}

JSONATTRS_SCHEMA_SELECTORS = (('organization', 'project__organization'),
                              'project')
