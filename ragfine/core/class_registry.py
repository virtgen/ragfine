# ragfine/core/class_registry.py
from .registry import register_step

def register_step_class(name: str | None = None):
    def deco(cls):
        step_name = name or cls.__name__
        register_step(step_name, lambda **kw: cls(**kw))
        return cls
    return deco


# USAGE:
# from ragfine.core.class_registry import register_step_class

# @register_step_class("Questor")
# class Questor:
#     def run(self, state, variant):
#         # ...
#         return state