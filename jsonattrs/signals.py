def attribute_model_pre_save(sender, **kwargs):
    kwargs['instance']._attr_field._pre_save_selector_check()
