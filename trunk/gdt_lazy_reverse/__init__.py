"""
A django app to provide the simple functionality of a deffered url reversal.

This app probably wont have much use outside of a few specific cases where a
user requires a url reversal to be performed within urls.py, specifically whilst
populating urlpatterns.  In these cases the normal django reverse function
cannot be used as it requires the populating of urlpatterns to have already been
completed.
"""
__version__ = "1.0"
