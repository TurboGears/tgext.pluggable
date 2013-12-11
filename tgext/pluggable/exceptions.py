try:
    from .sqla import SQLAIntegrityErrors
except ImportError:
    SQLAIntegrityErrors = tuple()

DBIntegrityErrors = SQLAIntegrityErrors