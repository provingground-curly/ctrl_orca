import os, sys, subprocess
from lsst.pex.logging import Log
from lsst.ctrl.orca.EnvString import EnvString
from lsst.ctrl.orca.WorkflowMonitor import WorkflowMonitor
from lsst.ctrl.orca.WorkflowLauncher import WorkflowLauncher
from lsst.ctrl.orca.SinglePipelineWorkflowMonitor import SinglePipelineWorkflowMonitor

class SinglePipelineWorkflowLauncher(WorkflowLauncher):
    ##
    # @brief
    #
    def __init__(self, cmd, prodPolicy, wfPolicy, logger = None):
        logger.log(Log.DEBUG, "SinglePipelineWorkflowLauncher:__init__")
        self.logger = logger
        self.cmd = cmd
        self.wfPolicy = wfPolicy
        self.prodPolicy = prodPolicy

    ##
    # @brief perform cleanup after workflow has ended.
    #
    def cleanUp(self):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowLauncher:cleanUp")

    ##
    # @brief launch this workflow
    #
    def launch(self, statusListener):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowLauncher:launch")

        pid = os.fork()
        if not pid:
            os.execvp(self.cmd[0], self.cmd)
        os.wait()[0]

        eventBrokerHost = self.prodPolicy.get("eventBrokerHost")
        shutdownTopic = self.wfPolicy.get("shutdownTopic")

        self.workflowMonitor = SinglePipelineWorkflowMonitor(eventBrokerHost, shutdownTopic, self.logger)
        if statusListener != None:
            self.workflowMonitor.addStatusListener(statusListener)
        return self.workflowMonitor
