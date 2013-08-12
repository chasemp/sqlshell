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

db = MySQLdb.connect(host="localhost",
                     user="root",
                     passwd="fella",
                     db="testdb")


class Console(cmd.Cmd):

    histfile = None

    def do_history(self, args):
        self.do_hist(args)

    def do_hist(self, args):
        """Print a list of commands that have been entered"""
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

    #Command definitions to support Cmd object functionality
    def do_EOF(self, args):
        """Exit on system end of file character"""
        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        os.system(args)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands
                         for which help is available.

           'help <command>' or '? <command>' gives help on <command>
        """
        #The only reason to define this method is for the help text
        #in the doc string
        cmd.Cmd.do_help(self, args)

    #Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion,
           Cmd.preloop() is not a stub.
        """
        # sets up command completion
        cmd.Cmd.preloop(self)

        self._hist = []
        #Attempt to read in stored history
        try:
            with open(self.histfile) as f:
                for h in f.read().strip().split('\n'):
                    self._hist.append(h)
        except:
            pass

        #Initialize execution namespace for user
        self._locals = {}
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion,
           Cmd.postloop() is not a stub.
        """
        #Clean up command completion
        cmd.Cmd.postloop(self)
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        if line:
            self._hist += [line.strip()]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console,
           return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):
        """return new prompt on empty line"""
        pass


class sqlcntrl(Console):
    """Simple command processor example."""

    """ based on active state recipe 280500-console-built-with-cmd-object/"""
    def __init__(self, histfile):
        cmd.Cmd.__init__(self, histfile)
        self.histfile = histfile
        self.prompt = "> "
        self.intro = "sqlshell"
        self.exitcmds = ['q', 'quit', 'exit', 'e']
        self.redirect = ['>', '>>', 'tee']

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
        except Exception, e:
            print e.__class__, ":", str(e)
            return

    def default(self, line):
        if any(map(lambda c: c == line, self.exitcmds)):
            self.die()

        fout = False
        if any(map(lambda c: c in line, self.redirect)):
            fout = True

        if fout:
            echo = False
            if '>>' in line:
                mode = 'a'
                line, fout = line.split('>>')
            elif 'tee' in line:
                echo = True
                mode = 'a'
                line, fout = line.split('tee')
            else:
                mode = 'w'
                line, fout = line.split('>')

        line = line.strip()
        result = self.query(line.strip())

        #discard None type returns, etc
        if not result:
            return

        if fout:
            fout = fout.strip()
            self.to_file(fout, result, mode)
            if not echo:
                return

        for row in result:
            print row

    def to_file(self, outfile, content, mode):
        with open(outfile, mode) as f:
            f.write(str(content).strip())
            f.write('\n')

    def do_EOF(self, line):
        return True


def main():
    home = p.expanduser('~')
    history_file = p.join(home, '.sqlshellhistory')
    sqlcntrl(history_file).cmdloop()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.exit(0)
