#!/usr/bin/python
import MySQLdb
import cmd
import os.path as p
import sys

db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                      passwd="fella", # your password
                      db="testdb") # name of the data base


class sqlcntrl(cmd.Cmd):
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


        for row in result:
            print row

    def do_shelp(self, yo):
        print yo
        print self.query('help')
        print self.query('\n')
        print self.query('?')

    def do_EOF(self, line):
        return True

def main():
    home = p.expanduser('~')
    print p.join(home, '.sqlshellhistory')
    sqlcntrl().cmdloop()



if __name__ == '__main__':
    main()
