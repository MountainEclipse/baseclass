from abc import ABC, abstractmethod
import inspect
from typing import Callable, List, Any

from weakref import WeakSet
from functools import wraps


__all__ = ["TrackedInstances", "CallPostInit", "InstancingArgsTracker", "EnumDict"]


class TrackedInstances:

    def __new__(cls, *args, **kwargs):
        """
        Track all instances of this class via weak references.

        This set of instances does not include subclass instances,
        but subclasses will inherit this ability.
        """
        instance = object.__new__(cls)
        if 'instances' not in cls.__dict__.keys():
            cls.instances = WeakSet()
        cls.instances.add(instance)
        return instance

    @classmethod
    def get_instances(cls, selector: Callable) -> set:
        """
        Search through all instances using the given selector, returning a list where selector is True.

        :param selector: Callable
            A callable (lambda or other function) that accepts one argument (an instance) and returns a bool.
            Calls where selector == True will result in the corresponding instance being included in the
            return.
        """
        if 'instances' not in cls.__dict__.keys():
            raise AttributeError(f"{cls.__name__} class has no attribute 'instances'")
        val = [v for v in cls.instances if selector(v)]
        return set(val)

    @classmethod
    def inst_and_subcls_inst(cls, exclude=None) -> set:
        """
        Return a tuple of all instances of this class and its subclasses.

        :param exceptions: List<class>
            A list of subclasses (and subclasses thereof) to except from the instance query.
        """
        exclude = exclude or []
        inst = list(cls.instances)
        for subcls in [v for v in cls.__subclasses__() if v not in exclude]:
            inst += subcls.inst_and_subcls_inst(exclude=exclude)
        return set(inst)


class CallPostInit(ABC):
    
    def __init_subclass__(cls, *primeargs, **primekwargs):
        super().__init_subclass__(*primeargs, **primekwargs)
        @wraps(cls.__init__)
        def new_init(self, *args, init=cls.__init__, **kwargs):
            init(self, *args, **kwargs)
            if type(self) == cls:
                self.__post_init__(*args, **kwargs)
        cls.__init__ = new_init

    @abstractmethod
    def __post_init__(self, *args, **kwargs):
        """
        Called after all __init__ statements are complete.

        *args, **kwargs are all arguments passed at instancing.
        """


class InstancingArgsTracker(CallPostInit):
    """
    Baseclass for tracking what arguments were used to instantiate a class
    """
    _metadata: dict  # contains the class instancing args

    def __post_init__(self, *args, **kwargs):
        """
        Track all arguments used to instantiate this class.
        """
        # make all args a list (to use 'pop' function), and make return dict
        args = list(args)
        data = {}

        # iterate through all bases defined in the class's inheritance chain
        # order of iteration will be C->B->A for class D inheriting from C,
        # class C inheriting from B, and so on...
        for base in inspect.getmro(self.__class__):
            # identify parameters from the base class __init__ function def
            params = inspect.signature(base).parameters
            params_list = list(params.values())

            # build list of all positional arguments (where default value is empty)
            arg = {
                k:v for k, v in params.items()
                if v.default is inspect.Parameter.empty and
                v.kind not in [inspect.Parameter.VAR_POSITIONAL,
                               inspect.Parameter.VAR_KEYWORD]
            }
            # build list of all kw args (where default value defined)
            kw = {
                k:v.default for k, v in params.items()
                if v.default is not inspect.Parameter.empty and
                v.kind not in [inspect.Parameter.VAR_POSITIONAL,
                               inspect.Parameter.VAR_KEYWORD]
            }

            # insert default arguments into the return dict
            data.update(**kw)

            # for all positional arguments, assign passed values
            for k, v in arg.items():
                data[k] = args.pop(0) if len(args) > 0 else v.default

            # if only positional arguments passed, override default kwarg
            # value with positional argument
            for i in range(len(args)):
                idx = len(arg) + i  # parameter index to set value of
                # it's possible we have more positional arguments than parameters
                # when using positional args to pass forward to parent classes

                # don't try assignment if you encounter a *args or **kwargs 
                if params_list[idx].kind in [inspect.Parameter.VAR_POSITIONAL, 
                                             inspect.Parameter.VAR_KEYWORD]:
                    break
                data[params_list[idx].name] = args.pop(0)

            # if no additional arguments were passed to instantiate a parent
            # class with **kwargs call, we are done
            # (speeds execution by approximately 4x by eliminating depth of
            #  iteration)
            kinds = [x.kind for x in params_list]
            if (inspect.Parameter.VAR_POSITIONAL not in kinds and
                inspect.Parameter.VAR_KEYWORD not in kinds):
                    break
        
        # update return dictionary with any kwargs dict passed to the instance
        data.update(**kwargs)
        
        # clean up any 'cls', 'self', 'args', or 'kwargs' parameters, as these
        # are of no use to us
        for key in ['cls', 'self', 'args', 'kwargs']:
            data.pop(key, None)
        
        # store the result to the instance _metadata variable
        self._metadata = data

    @property
    def metadata(self):
        """Return the instantiation variables for this class"""
        return self._metadata

    @classmethod
    def get_mro_parameters(cls) -> List[inspect.Parameter]:
        """
        Return a list of parameters for the full MRO of the class.
        """
        rtn = []
        for base in inspect.getmro(cls):
            rtn += inspect.signature(base).parameters.values()
        return {v for v in rtn if v.kind not in [inspect.Parameter.VAR_POSITIONAL, 
                                                 inspect.Parameter.VAR_KEYWORD]}


class EnumDict:
    """
    The EnumDict class allows us to access enum elements using dictionary
    functions, which may be desireable in some cases.

    EnumDicts are intended to be immutable in runtime, so new or existing
    value assignments are not permitted.
    """
    @classmethod
    def keys(cls) -> set:
        return {k for k, v in cls.__dict__.items() if not any(
            [k.startswith('__'), inspect.isfunction(v), inspect.ismethod(v)])}

    @classmethod
    def values(cls) -> set:
        return {v for k, v in cls.__dict__.items() if not any(
            [k.startswith('__'), inspect.isfunction(v), inspect.ismethod(v)])}

    @classmethod
    def __setattr__(cls, key: str, value: Any):
        raise RuntimeError(f"EnumDict '{cls.__name__}'" +
                           "cannot add or change values during runtime.")
