# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

##
#
#
#
#
# NOTE: This is here as a placeholder, and should be integrated with 
# db/Dc3aDatabaseConfigurator
#
#
#
#
# @brief
#
class DatabaseConfigurator:
    def __init__(self, runid, config, logger):
        self.runid = runid
        self.config = config
        self.logger = logger
        return

    ##
    # @brief
    #
    def setDatabase(self, provSetup):

        # setup the database - using Dc3aDatabaseConfigurator as a placeholder
        dbConfigurator = Dc3aDatabaseConfigurator(self.runid, self.config, self.logger)
        dbConfigurator.setup()

        if provSetup is not None:
            # may call provSetup.addProductionRecorder(ProvenanceRecorder)
            # may call provSetup.addWorkflowRecordCmd(string)
            return
