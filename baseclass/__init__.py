"""
baseclass == Baseclass Library

@author: MountainEclipse
@date: 18 February 2024
"""

# Inform users of any missing hard dependencies
hard_dependencies = ['typing']
missing_dependencies = []  # dependency strings

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append(f'{dependency}: {e}')

if missing_dependencies:
    raise ImportError(
        'Unable to import required dependencies:\n' + '\n'.join(missing_dependencies))

# Delete now-unnecessary variables
del hard_dependencies, dependency, missing_dependencies

# library version
__version__ = (0, 0, 1)

# All members that can be imported
__all__ = ["TrackedInstances", "CallPostInit", "InstancingArgsTracker", "EnumDict"]

from ._baseclass import TrackedInstances, CallPostInit, InstancingArgsTracker, EnumDict