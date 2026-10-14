"""Desktop tests are opt-in; ordinary pytest and unittest never exercise the UI."""
import pytest


def pytest_addoption(parser):
    group = parser.getgroup('canrat-desktop')
    group.addoption('--run-desktop', action='store_true', default=False,
                    help='Run explicitly selected CanRat desktop tests')
    group.addoption('--canrat-initial', choices=('Auto', 'Existing', 'Closed'), default='Auto',
                    help='Required starting process state for the desktop run')
    group.addoption('--evidence-dir', default=None,
                    help='New report folder below raporlar/kosular for the desktop run')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-desktop'):
        return
    marker = pytest.mark.skip(reason='Masaüstü testi için açık --run-desktop gerekir.')
    for item in items:
        if item.get_closest_marker('desktop'):
            item.add_marker(marker)
