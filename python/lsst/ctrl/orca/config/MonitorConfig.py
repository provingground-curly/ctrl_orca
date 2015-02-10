import sys
import lsst.pex.config as pexConfig
import FakeTypeMap as fake

class MonitorConfig(pexConfig.Config):
    statusCheckInterval = pexConfig.Field("interval to wait for condor_q status checks", int, default=5)