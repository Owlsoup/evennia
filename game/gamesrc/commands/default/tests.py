"""
This defines some test commands for use while testing the MUD.
Just remove these commands from the default state when they
are not needed anymore. 
"""

from django.db import IntegrityError
from src.comms.models import Msg
from game.gamesrc.commands.default.muxcommand import MuxCommand
from src.permissions import permissions
from src.utils import create 

# Test permissions

class CmdTest(MuxCommand):
    """
    test the command system

    Usage:
      @test <any argument or switch>

    This command will echo back all argument or switches
    given to it, showcasing the muxcommand style. 
    """

    key = "@test"
    aliases = ["@te", "@test all"]
    permissions = "cmd:Immortals Wizards"

    # the muxcommand class itself handles the display
    # so we just defer to it by not adding any function.
    pass


class CmdTestPerms(MuxCommand):
    """
    Test command - test permissions 

    Usage:
      @testperm [[lockstring] [=permstring]]

    With no arguments, runs a sequence of tests for the
    permission system using the calling player's permissions. 
    
    If <lockstring> is given, match caller's permissions
    against these locks. If also <permstring> is given,
    match this against the given locks instead.

    """
    key = "@testperm"
    permissions = "cmd:Immortals Wizards"

    def func(self, srcobj, inp):
        """
        Run tests
        """
        if srcobj.user.is_superuser:
            srcobj.msg("You are a superuser. Permission tests are pointless.")
            return 
        # create a test object
        obj = create.create_object(None, "accessed_object") # this will use default typeclass
        obj_id = obj.id 
        srcobj.msg("obj_attr: %s" % obj.attr("testattr"))

        # perms = ["has_permission", "has permission", "skey:has_permission",
        #          "has_id(%s)" % obj_id, "has_attr(testattr)",
        #          "has_attr(testattr, testattr_value)"]        
            
        # test setting permissions 
        uprofile = srcobj.user.get_profile()
        # do testing
        srcobj.msg("----------------")

        permissions.set_perm(obj, "has_permission")
        permissions.add_perm(obj, "skey:has_permission")
        srcobj.msg(" keys:[%s] locks:[%s]" % (uprofile.permissions, obj.permissions))        
        srcobj.msg("normal permtest: %s" % permissions.has_perm(uprofile, obj))
        srcobj.msg("skey permtest: %s" % permissions.has_perm(uprofile, obj, 'skey'))

        permissions.set_perm(uprofile, "has_permission")
        srcobj.msg(" keys:[%s] locks:[%s]" % (uprofile.permissions, obj.permissions))
        srcobj.msg("normal permtest: %s" % permissions.has_perm(uprofile, obj))        
        srcobj.msg("skey permtest: %s" % permissions.has_perm(uprofile, obj, 'skey'))        

        # function tests 
        permissions.set_perm(obj, "has_id(%s)" % (uprofile.id))
        srcobj.msg(" keys:[%s] locks:[%s]" % (uprofile.permissions, obj.permissions))
        srcobj.msg("functest: %s" % permissions.has_perm(uprofile, obj))

        uprofile.attr("testattr", "testattr_value")
        permissions.set_perm(obj, "has_attr(testattr, testattr_value)")
        srcobj.msg(" keys:[%s] locks:[%s]" % (uprofile.permissions, obj.permissions))
        srcobj.msg("functest: %s" % permissions.has_perm(uprofile, obj))
              
        # cleanup of test permissions
        permissions.del_perm(uprofile, "has_permission")
        srcobj.msg(" cleanup: keys:[%s] locks:[%s]" % (uprofile.permissions, obj.permissions))
        obj.delete()
        uprofile.attr("testattr", delete=True)
        

# Add/remove states 

EXAMPLE_STATE="game.gamesrc.commands.examples.example.EXAMPLESTATE"

class CmdTestState(MuxCommand):
    """
    Test command - add a state.

    Usage:
      @teststate[/switch] [<python path to state instance>]      
    Switches:
      add   - add a state 
      clear - remove all added states.
      list - view current state stack 
      reload - reload current state stack
      
    If no python path is given, an example state will be added.
    You will know it worked if you can use the commands '@testcommand'
    and 'smile'.
    """

    key = "@teststate"
    alias = "@testingstate"
    permissions = "cmd:Immortals Wizards"
    
    def func(self, source_object, inp):
        """
        inp is the dict returned from MuxCommand's parser. 
        """
        switches = inp["switches"]
        if not switches or switches[0] not in ["add", "clear", "list", "reload"]:
            string = "Usage: @teststate[/add|clear|list|reload] [<python path>]"
            source_object.msg(string)
        elif "clear" in switches:            
            source_object.statehandler.clear()
            source_object.msg("All states cleared.")
            return
        elif "list" in switches:
            string = "%s" % source_object.statehandler
            source_object.msg(string)
        elif "reload" in switches:
            source_object.statehandler.load()
            source_object.msg("States reloaded.")
        else: #add
            arg = inp["raw"]
            if not arg:
                arg = EXAMPLE_STATE
            source_object.statehandler.add(arg)
            string = "Added state '%s'." % source_object.statehandler.state.key
            source_object.msg(string)

class TestCom(MuxCommand):
    """
    Test the command system

    Usage:
      @testcom/create/list [channel]
    """
    key = "@testcom"    
    permissions = "cmd:Immortals Wizards"

    def func(self):
        "Run the test program"
        caller = self.caller
        
        if 'create' in self.switches:
            if self.args:
                chankey = self.args
                try:
                    channel = create.create_channel(chankey)
                except IntegrityError:
                    caller.msg("Channel '%s' already exists." % chankey)
                    return 
            channel.connect_to(caller)
            caller.msg("Created new channel %s" % chankey)
            msgobj = create.create_message(caller.player,
                                           "First post to new channel!")
            channel.msg(msgobj)

            return
        elif 'list' in self.switches:
            msgresults = Msg.objects.get_messages_by_sender(caller)
            string = "\n".join(["%s %s: %s" % (msg.date_sent,
                                               [str(chan.key) for chan in msg.channels.all()],
                                               msg.message)
                                for msg in msgresults])
            caller.msg(string)
            return 
        caller.msg("Usage: @testcom/create channel")