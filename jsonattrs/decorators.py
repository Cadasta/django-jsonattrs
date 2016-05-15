def fix_model_for_attributes(cls):
    def wrapped_init(self, *args, **kwargs):
        super(cls, self).__init__(*args, **kwargs)
        self.attrs._instance = self

    cls.__init__ = wrapped_init
    return cls
