# 12/9/2023 By MountainEclipse

import unittest
from _baseclass import *


class TestTrackedInstances(unittest.TestCase):

    class Parent(TrackedInstances):
        pass

    class Child(Parent):
        pass

    class Grandchild(Child):
        pass

    def test_new(self):
        # when creating an instance of a class with tracked instances, 
        # an 'instances' variable should be created as a WeakSet, and the
        # new instance should be added.
        p1 = self.Parent()
        p2 = self.Parent()

        self.assertTrue(hasattr(self.Parent, 'instances'))
        self.assertEqual(set(self.Parent.instances), {p1, p2})

        p3 = self.Parent()
        self.assertEqual(set(self.Parent.instances), {p1, p2, p3})

    def test_get_instances(self):
        # when instances have been created, a specific instance can be retrieved
        # using the get_instance function, which selects the instance based
        # on a function that returns a bool (true for match, false otherwise)
        self.assertRaises(AttributeError, self.Parent.get_instances, 
                          selector=lambda x: x.value==10)
        
        p1 = self.Parent()
        p1.value = 10

        p2 = self.Parent()
        p2.value = 13

        # should return a set object
        self.assertIsInstance(self.Parent.get_instances(lambda x: False), set)

        # should return the p1 instance as a set
        self.assertEqual(
            self.Parent.get_instances(lambda x: x.value == p1.value),
            {p1})
        
        # should return the p2 instance as a set
        self.assertEqual(
            self.Parent.get_instances(lambda x: x.value == p2.value),
            {p2})

    def test_inst_listing(self):
        # all instances and subclass instances can be returned when needed.
        # certain subclasses can be excluded, if an iterable is passed to
        # the 'exclude' parameter
        p1 = self.Parent()
        p2 = self.Parent()
        c1 = self.Child()
        c2 = self.Child()
        gc = self.Grandchild()

        # should return all class and subclass instances
        self.assertEqual(self.Parent.inst_and_subcls_inst(), {p1, p2, c1, c2, gc})

        # should return all class and subclass instances
        self.assertEqual(self.Child.inst_and_subcls_inst(), {c1, c2, gc})

        # should return all class and subclass instances, except grandchildren
        self.assertEqual(self.Parent.inst_and_subcls_inst(exclude=[self.Grandchild]), {p1, p2, c1, c2})


class TestCallPostInit(unittest.TestCase):

    class Superclass():
        def __init__(self, value):
            self.value = value

        def __post_init__(self, value):
            self.value = value + 1

    class Subclass(Superclass, CallPostInit):
        pass

    def test_init_subclass(self):
        # when subclassing this base class, the original init function will
        # be overridden with a new one which appends a function call to
        # a function __post_init__
        
        no_post = self.Superclass(10)

        # no post-init function call should be made here
        self.assertEqual(no_post.value, 10)

        ya_post = self.Subclass(10)

        # post-init function should be called, adding 1 to the passed value
        self.assertEqual(ya_post.value, 11)


class TestInstanceArgs(unittest.TestCase):

    class Parent(InstancingArgsTracker):
        def __init__(self, p1, p2, p3="vp3"):
            pass
    
    class Child(Parent):
        def __init__(self, c1, c2="vc2", c3="vc3", *args, **kwargs):
            super().__init__(*args, **kwargs)

    class Grandchild(Child):
        def __init__(self, gc1, gc2="vgc2", *args, **kwargs):
            super().__init__(*args, **kwargs)

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_arg_assignment_parent(self) -> None:
        test_args = {
            "p1": "argp1",
            "p2": "argp2",
            "p3": "argp3"
        }

        # test assignment using only positional arguments
        p = self.Parent(test_args['p1'], test_args['p2'], test_args['p3'])
        self.assertEqual(set(p.metadata.keys()), {'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, test_args)

        # test assignment using mix of positional and named arguments
        p = self.Parent(test_args['p1'], p2=test_args['p2'], p3=test_args['p3'])
        self.assertEqual(set(p.metadata.keys()), {'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, test_args)

        # test assignment using kwargs dict passing
        p = self.Parent(**test_args)
        self.assertEqual(set(p.metadata.keys()), {'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, test_args)

    def test_arg_assignment_child(self) -> None:
        ta = {
            "c1": "argc1",
            "c2": "argc2",
            "c3": "argc3",
            "p1": "argp1",
            "p2": "argp2",
            "p3": "argp3"
        }

        # test assignment using only positional arguments
        p = self.Child(*ta.values())
        self.assertEqual(set(p.metadata.keys()), 
                         {'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), 
                         {'argc1', 'argc2', 'argc3', 'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, ta)

        # test assignment using mix of positional and named arguments
        p = self.Child(ta['c1'], ta['c2'], c3=ta['c3'], p1=ta['p1'], p2=ta['p2'], p3=ta['p3'])
        self.assertEqual(set(p.metadata.keys()), {'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'argc1', 'argc2', 'argc3', 'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, ta)

        # test assignment using kwargs dict passing
        p = self.Child(**ta)
        self.assertEqual(set(p.metadata.keys()), {'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'argc1', 'argc2', 'argc3', 'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, ta)

    def test_arg_assignment_grandchild(self) -> None:
        ta = {
            "gc1": "arggc1",
            "gc2": "arggc2",
            "c1": "argc1",
            "c2": "argc2",
            "c3": "argc3",
            "p1": "argp1",
            "p2": "argp2",
            "p3": "argp3"
        }
        
        # test assignment using only positional arguments
        p = self.Grandchild(*ta.values())
        self.assertEqual(set(p.metadata.keys()), 
                         {'gc1', 'gc2', 'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), 
                         {'arggc1', 'arggc2', 'argc1', 'argc2', 'argc3', 'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, ta)

        # test assignment using mix of positional and named arguments
        p = self.Grandchild(ta['gc1'], ta['gc2'], ta['c1'], ta['c2'], c3=ta['c3'], p1=ta['p1'], p2=ta['p2'], p3=ta['p3'])
        self.assertEqual(set(p.metadata.keys()), {'gc1', 'gc2', 'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'arggc1', 'arggc2', 'argc1', 'argc2', 'argc3', 'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, ta)

        # test assignment using kwargs dict passing
        p = self.Grandchild(**ta)
        self.assertEqual(set(p.metadata.keys()), {'gc1', 'gc2', 'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})
        self.assertEqual(set(p.metadata.values()), {'arggc1', 'arggc2', 'argc1', 'argc2', 'argc3', 'argp1', 'argp2', 'argp3'})
        self.assertEqual(p.metadata, ta)

    def test_MRO_params(self) -> None:
        mro_params = self.Parent.get_mro_parameters()
        self.assertEqual(len(mro_params), 3)
        self.assertEqual({x.name for x in mro_params}, {'p1', 'p2', 'p3'})

        mro_params = self.Grandchild.get_mro_parameters()
        self.assertEqual(len(mro_params), 8)
        self.assertEqual({x.name for x in mro_params}, 
                         {'gc1', 'gc2', 'c1', 'c2', 'c3', 'p1', 'p2', 'p3'})


class TestEnumDict(unittest.TestCase):

    class ED(EnumDict):
        KEY1 = "value1"
        KEY2 = "value2"
        KEY3 = "value3"

    def test_access_funcs(self):
        # ensure the 'keys' function returns all keys of the enum
        self.assertEqual(self.ED.keys(), {"KEY1", "KEY2", "KEY3"})

        # ensure the 'values' function returns all values of the enum
        self.assertEqual(self.ED.values(), {"value1", "value3", "value2"})

        # attribute setting not permitted for this
        self.assertRaises(RuntimeError, self.ED.__setattr__, key="KEY4", value="value4")
    