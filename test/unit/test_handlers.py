import pytest

import handlers


def test_handle_request():
    handlers.publish({}, None)