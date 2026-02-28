"""WishlistOps package.

WishlistOps drafts Steam announcements from Git commits and prepares user-provided
images for posting. It does *not* generate images.

Keep this module lightweight: avoid importing optional / non-core modules at import
time so `import wishlistops` never fails.
"""

__version__ = "0.2.0"
__author__ = "WishlistOps Team"

from .main import WishlistOpsOrchestrator, WorkflowError

__all__ = ["WishlistOpsOrchestrator", "WorkflowError"]
