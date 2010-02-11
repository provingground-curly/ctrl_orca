import sys,os, os.path, shutil, sets, stat
import lsst.ctrl.orca as orca
import lsst.pex.policy as pol

from lsst.ctrl.orca.Directories import Directories
from lsst.pex.logging import Log

from lsst.ctrl.orca.EnvString import EnvString
from lsst.ctrl.orca.WorkflowConfigurator import WorkflowConfigurator
from lsst.ctrl.orca.SinglePipelineWorkflowLauncher import SinglePipelineWorkflowLauncher

##
#
# SinglePipelineWorkflowConfigurator 
#
class SinglePipelineWorkflowConfigurator(WorkflowConfigurator):
    def __init__(self, runid, prodPolicy, wfPolicy, logger):
        self.logger = logger
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:__init__")
        self.runid = runid
        self.prodPolicy = prodPolicy
        self.wfPolicy = wfPolicy
        self.verbosity = None

        self.nodes = None
        self.dirs = None
        self.policySet = sets.Set()

    ##
    # @brief Setup as much as possible in preparation to execute the workflow
    #            and return a WorkflowLauncher object that will launch the
    #            configured workflow.
    # @param provSetup
    # @param wfVerbosity
    #
    def configure(self, provSetup, wfVerbosity):
        self.workflowVerbosity = wfVerbosity
        self._configureDatabases(provSetup)
        return self._configureSpecialized(self.wfPolicy)
    
    def _configureSpecialized(self, wfPolicy):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:configure")
        self.shortName = wfPolicy.get("shortName")
        self.defaultDomain = wfPolicy.get("platform.deploy.defaultDomain")
        pipelinePolicies = wfPolicy.getPolicyArray("pipeline")
        for pipelinePolicy in pipelinePolicies:
            self.nodes = self.createNodeList(pipelinePolicy)
            self.createDirs(pipelinePolicy)
            self.deploySetup(pipelinePolicy)
            cmd = self.createLaunchCommand(pipelinePolicy)
        workflowLauncher = SinglePipelineWorkflowLauncher(self.logger, wfPolicy)
        return workflowLauncher

    ##
    # @brief create the command which will launch the workflow
    # @return a string containing the shell commands to execute
    #
    def createLaunchCommand(self, pipelinePolicy):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:createLaunchCommand")

        execPath = pipelinePolicy.get("definition.framework.exec")
        launchcmd = EnvString.resolve(execPath)
        filename = "stooge"

        cmd = ["ssh", self.masterNode, "cd %s; source %s; %s %s %s -L %s" % (self.dirs.get("work"), self.script, launchcmd, filename, self.runid, self.verbosity) ]
        return cmd


    ##
    # @brief creates a list of nodes from platform.deploy.nodes
    # @return the list of nodes
    #
    def createNodeList(self,  pipelinePolicy):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:createNodeList")
        node = pipelinePolicy.getArray("deploy.processesOnNode")

        nodes = map(self.expandNodeHost, node)
        # by convention, the master node is the first node in the list
        # we use this later to launch things, so strip out the info past ":", if it's there.
        self.masterNode = nodes[0]
        colon = self.masterNode.find(':')
        if colon > 1:
            self.masterNode = self.masterNode[0:colon]
        return nodes

    def getWorkflowName(self):
        return self.workflow
    
    def getNodeCount(self):
        return len(self.nodes)

    ##
    # @brief prepare the platform by creating directories and writing the node list
    #
    def prepPlatform(self):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:prepPlatform")
        self.createDirs()

    ##
    # @brief write the node list to the "work" directory
    #
    def writeNodeList(self):
        
        # write this only for debug
        nodelist = open(os.path.join(self.dirs.get("work"), "nodelist.scr"), 'w')
        for node in self.nodes:
            print >> nodelist, node
        nodelist.close()

        p = pol.Policy()
        x = 0
        for node in self.nodes:
            p.set("node%d" % x, node)
            x = x + 1
        pw = pol.PAFWriter(os.path.join(self.dirs.get("work"), "nodelist.paf"))
        pw.write(p)
        pw.close()


    ##
    # @brief 
    #
    def deploySetup(self, pipelinePolicy):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:deploySetup")

        # write the nodelist to "work"
        self.writeNodeList()

        # copy /bin/sh script responsible for environment setting

        setupPath = pipelinePolicy.get("definition.framework.environment")
        if setupPath == None:
             raise RuntimeError("couldn't find definition.framework.environment")
        self.script = EnvString.resolve(setupPath)

        if orca.envscript == None:
            print "using default setup.sh"
        else:
            self.script = orca.envscript

        shutil.copy(self.script, self.dirs.get("work"))

        # now point at the new location for the setup script
        self.script = os.path.join(self.dirs.get("work"),os.path.basename(self.script))

        #
        # TODO: Write all policy files out to the work directory, 
        #

        self.writeLaunchScript()

    ##
    # @brief write a shell script to launch a workflow
    #
    def writeLaunchScript(self):
        # write out the script we use to kick things off
        name = os.path.join(self.dirs.get("work"), "orca_launch.sh")

        # TODO: This needs to be replaced with an invocation of the Provence script, which
        # is going to be in ctrl_provenance
        #
        #user = self.provenanceDict["user"]
        #runid = self.provenanceDict["runid"]
        #dbrun = self.provenanceDict["dbrun"]
        #dbglobal = self.provenanceDict["dbglobal"]
        #repos = self.provenanceDict["repos"]
        #
        #filename = os.path.join(self.dirs.get("work"), self.configurationDict["filename"])

        #s = "ProvenanceRecorder.py --type=%s --user=%s --runid=%s --dbrun=%s --dbglobal=%s --filename=%s --repos=%s\n" % ("lsst.ctrl.orca.provenance.BasicRecorder", user, runid, dbrun, dbglobal, filename, repos)

        launcher = open(name, 'w')
        launcher.write("#!/bin/sh\n")

        launcher.write("echo $PATH >path.txt\n")
        launcher.write("eups list 2>/dev/null | grep Setup >eups-env.txt\n")
        launcher.write("workflow=`echo ${1} | sed -e 's/\..*$//'`\n")
        #launcher.write(s)
        launcher.write("#$CTRL_ORCA_DIR/bin/writeNodeList.py %s nodelist.paf\n" % self.dirs.get("work"))
        launcher.write("nohup $PEX_HARNESS_DIR/bin/launchWorkflow.py $* > ${workflow}-${2}.log 2>&1  &\n")
        launcher.close()
        # make it executable
        os.chmod(name, stat.S_IRWXU)
        return

    ##
    # @brief create the platform.dir directories
    #
    def createDirs(self, pipelinePolicy):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:createDirs")

        dirPolicy = self.wfPolicy.getPolicy("platform.dir")
        dirName = pipelinePolicy.get("shortName")
        directories = Directories(dirPolicy, dirName, self.runid)
        self.dirs = directories.getDirs()

        for name in self.dirs.names():
            if not os.path.exists(self.dirs.get(name)): os.makedirs(self.dirs.get(name))

    ##
    # @brief set up this workflow's database
    #
    def setupDatabase(self):
        self.logger.log(Log.DEBUG, "SinglePipelineWorkflowConfigurator:setupDatabase")

    ##
    # @brief perform a node host name expansion
    #
    def expandNodeHost(self, nodeentry):
        """Add a default network domain to a node list entry if necessary """

        if nodeentry.find(".") < 0:
            node = nodeentry
            colon = nodeentry.find(":")
            if colon == 0:
                raise RuntimeError("bad nodelist format: " + nodeentry)
            elif colon > 0:
                node = nodeentry[0:colon]
                if len(node) < 3:
                    #logger.log(Log.WARN, "Suspiciously short node name: " + node)
                    self.logger.log(Log.DEBUG, "Suspiciously short node name: " + node)
                self.logger.log(Log.DEBUG, "-> nodeentry  =" + nodeentry)
                self.logger.log(Log.DEBUG, "-> node  =" + node)

                if self.defaultDomain is not None:
                    node += "."+self.defaultDomain
                nodeentry = "%s:%s" % (node, nodeentry[colon+1:])
            else:
                if self.defaultDomain is not None:
                    nodeentry = "%s%s:1" % (node, self.defaultDomain)
                else:
                    nodeentry = "%s:1" % node
        return nodeentry
        
    ##
    # @brief given a policy, recursively add all child policies to a policy set
    # 
    def extractChildPolicies(self, repos, policy, workflowPolicySet):
        names = policy.fileNames()
        for name in names:
            if name.rfind('.') > 0:
                desc = name[0:name.rfind('.')]
                field = name[name.rfind('.')+1:]
                policyObjs = policy.getPolicyArray(desc)
                for policyObj in policyObjs:
                    if policyObj.getValueType(field) == pol.Policy.FILE:
                        filename = policyObj.getFile(field).getPath()
                        filename = os.path.join(repos, filename)
                        if (filename in self.policySet) == False:
                            #self.provenance.recordPolicy(filename)
                            self.policySet.add(filename)
                        if (filename in workflowPolicySet) == False:
                            workflowPolicySet.add(filename)
                        newPolicy = pol.Policy.createPolicy(filename, False)
                        self.extractChildPolicies(repos, newPolicy, workflowPolicySet)
            else:
                field = name
                if policy.getValueType(field) == pol.Policy.FILE:
                    filename = policy.getFile(field).getPath()
                    filename = policy.getFile(field).getPath()
                    filename = os.path.join(repos, filename)
                    if (filename in self.policySet) == False:
                        #self.provenance.recordPolicy(filename)
                        self.policySet.add(filename)
                    if (filename in workflowPolicySet) == False:
                        workflowPolicySet.add(filename)
                    newPolicy = pol.Policy.createPolicy(filename, False)
                    self.extractChildPolicies(repos, newPolicy, workflowPolicySet)