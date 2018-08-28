import pytest

import handlers


def test_handle_request():
    handlers.handle_requeset({}, None)