import micropython
micropython.alloc_emergency_exception_buf(100)

from weatherstation import WeatherStation
ws = WeatherStation()
