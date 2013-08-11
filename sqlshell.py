#!/usr/bin/python
import os
import MySQLdb
import cmd
import os.path as p
import sys
try:
    import readline
except ImporError:
    pass

db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                      passwd="fella", # your password
                      db="testdb") # name of the data base

class Console(cmd.Cmd):
    """ based on active state recipe 280500-console-built-with-cmd-object/"""
    def __init__(self):
        cmd.Cmd.__init__(self)
        self.prompt = "> "
        self.intro  = "sqlshell"

    def do_history(self, args):
        self.do_hist(args)        

    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        if args:
           print type(args)
           print 'args!'
        for h in self._hist:
            if args:
                for oldcmd in self._hist:
                    if oldcmd in h:
                        print h
            else:
                print h

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        self._hist    = []      ## No history yet
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

    def default(self, line):       
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e


class sqlcntrl(Console):
    """Simple command processor example."""

    exitcmds = ['q', 'quit', 'exit', 'e']
    redirects = ['>', '>>']

    def die(self):
        print 'exiting!'
        sys.exit(0)

    def query(self, line):
        try:
            cur = db.cursor() 
            cur.execute("%s" % (line,))
            return cur.fetchall()
        #yes this is heavy handed I have the idea
        #that problems with SQL parsing a command should
        #never exit here just like for standard MySQL client
        #but errors are always passed up
        except Exception as e:
             print 'ERROR:', str(e)

    def default(self, line):
        fout = None
	
        if any(map(lambda c: c == line, self.exitcmds)):
            self.die()

        if any(map(lambda c: c in line, self.redirects)):
            print 'redirect!'

        if '>' in line:
            line, fout = line.split('>')

        result = self.query(line.strip())
        print type(result)
        if fout:
            with open(fout.strip(), 'w') as f:
                f.write(str(result))
                f.write('\n')

        for row in result:
            print row

    def do_EOF(self, line):
        return True

def main():
    home = p.expanduser('~')
    print p.join(home, '.sqlshellhistory')
    sqlcntrl().cmdloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.exit(0)
