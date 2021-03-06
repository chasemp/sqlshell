#!/usr/bin/python
import os
import pydoc
import MySQLdb
import cmd
import os.path as p
import sys
import tempfile
import subprocess
try:
    import readline
except ImporError:
    pass

db = MySQLdb.connect(host="localhost",
                     user="root",
                     passwd="fella",
                     db="testdb")


def runShell(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    return p.stdout.read().strip()


class Console(cmd.Cmd):

    histfile = None

    def show_history(self):
        """Print a list of commands that have been entered"""
        for i, h in enumerate(self._hist):
            print i, h

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

    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion,
           Cmd.preloop() is not a stub.
        """
        # sets up command completion
        cmd.Cmd.preloop(self)

        self._hist = []
        self._alias = {}
        #Attempt to establish aliases
        try:
            with open(self.aliasfile) as f:
                alist = f.read().strip().split('\n')
                for alias in alist:
                    key, value = alias.split('=')
                    self._alias[key.strip()] = value.strip()
        except:
            pass

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
        try:
            with open(self.histfile, 'w') as f:
                for c in set(self._hist[:100]):
                    if not c:
                        continue
                    elif c in self.exitcmds:
                        continue
                    elif c in self.histcmds:
                        continue
                    else:
                        f.write(c + '\n')
        except:
            pass

        #Clean up command completion
        cmd.Cmd.postloop(self)

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        if line:
            #self._hist += [line.strip()]
            if line not in self._hist:
                self._hist.append(line)
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
    def __init__(self, db):
        cmd.Cmd.__init__(self)
        homedir = p.expanduser('~')
        self.active = True
        self.db = db
        self.histfile = p.join(homedir, '.sqlshellhistory')
        self.aliasfile = p.join(homedir, '.sqlshellalias')
        self.prompt = ">>"
        self.intro = "sqlshell"
        self.exitcmds = ['q', 'quit', 'exit', 'e', 'end']
        self.histcmds = ['h', 'hist', 'history']
        self.redirect = ['>', '>>', 'tee']
        self.editor = os.environ.get('EDITOR', 'nano')
        self.python = os.environ.get('_', 'python')

    def do_prompt(self, line):
        """Update the interactive prompt"""
        self.prompt = line.strip()

    def die(self):
        try:
            self.db.close()
        except:
            pass
        print 'bye'
        return -1

    def default(self, line):
        #any valid exit command is handled
        if any(map(lambda c: c == line, self.exitcmds)):
            return self.die()
        #any valid history command is handled
        if any(map(lambda c: c == line, self.histcmds)):
            return self.show_history()
        print self.process(line)

    def do_less(self, line):
        output = self.process(line)
        pydoc.pager(output)

    def query(self, line):
        try:
            cur = self.db.cursor()
            cur.execute("%s" % (line,))
            return cur.fetchall()
        #yes this is heavy handed I have the idea
        #that problems with SQL parsing a command should
        #never exit here just like for standard MySQL client
        #but errors are always passed up
        except Exception, e:
            print e.__class__, ":", str(e)
            return

    def process(self, line):
        #allow use of alias commands
        aliasmatch = self._alias.get(line.split()[0], None)
        if aliasmatch:
            #$@ in bash script type behavior
            dollarall = ' '.join(line.split(' ')[1:])
            line = aliasmatch + ' ' + dollarall

        fout = False
        #determine command redirect state
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

        pipe = False
        if '|' in line:
            pipe = True
            line, shcmd = line.split('|')

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

        out = self.to_text(result)
        if pipe:
            shell = 'echo "%s" | %s' % (str(out), shcmd)
            out = runShell(shell)

        return out

    def to_text(self, param):
        txt = ''
        for i in param:
            txt += str(i)
            txt += '\n'
        return txt

    def to_file(self, outfile, content, mode):
        with open(outfile, mode) as f:
            f.write(str(content).strip())
            f.write('\n')

    def do_short(self, line):
        """"show defined aliases"""
        for k, v in self._alias.iteritems():
            print k, '-->', v

    def do_py(self, line):
        subprocess.call([self.python])

    def do_commit(self, line):
        print 'committing changes'
        self.db.commit()

    def do_edit(self, line):
        with tempfile.NamedTemporaryFile(suffix=".tmp") as tfile:
            tfile.write(line)
            tfile.flush()
            subprocess.call([self.editor, tfile.name])
            command = open(tfile.name).read().strip()
            self.process(command)

    def do_EOF(self, line):
        return True


def main():
    sqlcntrl(db).cmdloop()
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.stdout.write('\n')
        sys.exit(0)
