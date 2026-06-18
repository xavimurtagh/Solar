"""Shared, session-scoped fixtures.

The expensive objects (the spectrum integrals and the year-long pvlib
simulation) are built once for the whole suite to keep total runtime to a
couple of minutes.
"""

import pytest

from solarlab.spectrum import SpectrumIntegrals, load_am15g


@pytest.fixture(scope="session")
def spectrum():
    return load_am15g()


@pytest.fixture(scope="session")
def spec(spectrum):
    return SpectrumIntegrals(spectrum)


@pytest.fixture(scope="session")
def weather():
    from solarlab.system import reference_weather

    return reference_weather()


@pytest.fixture(scope="session")
def base_sim(weather):
    from solarlab.levers import BASE
    from solarlab.system import simulate

    data, meta = weather
    return simulate(BASE, weather=(data, meta))
